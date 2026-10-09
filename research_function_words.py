#!/usr/bin/env python3
"""Conservative completed screening of purely grammatical surface forms.

Only one-to-one QAC-aligned forms whose *every* occurrence has exclusively
closed-class grammatical POS tags are eligible. Mixed lexical uses stay pending.
"""
from collections import Counter, defaultdict
import json

from qac_morphology import SOURCE_SHA256, align, stems
from quran_words import WORDS, STATUS_PENDING, atomic_json, identity, now, read_words

TAGS = {
    'P': 'предлог', 'CONJ': 'союз', 'NEG': 'отрицательная частица',
    'ACC': 'грамматическая частица', 'SUB': 'подчинительная частица',
    'COND': 'условная частица/местоимение', 'REL': 'относительное местоимение',
    'DEM': 'указательное местоимение', 'PRON': 'личное/притяжательное местоимение',
    'INTG': 'вопросительная частица/местоимение', 'CERT': 'утвердительная частица',
    'EMPH': 'усилительная частица', 'PREV': 'ограничительная частица',
    'PRO': 'запретительная частица', 'RET': 'ответная частица',
    'RES': 'исключительная частица', 'ANS': 'частица ответа',
    'AMD': 'частица противопоставления', 'SUP': 'дополнительная частица',
    'COM': 'сопутствующая частица', 'EXH': 'побудительная частица',
    'RSLT': 'частица следствия',
}

manifest, word_records = read_words()
words, mapping = align()
by_form = defaultdict(list)
for loc, group in mapping.items():
    if len(group) != 1:
        continue
    stem_tags = {seg['tag'] for seg in stems(words[loc])}
    by_form[group[0]['word']].append((loc, stem_tags))

eligible = 0
changed = 0
for record in word_records:
    word = record['word']
    observed = by_form[word]
    # Ensure no occurrence of the form was hidden inside a QAC multiword token.
    if len(observed) != record['frequency']:
        continue
    tags = set().union(*(tags for _, tags in observed)) if observed else set()
    if not tags or not tags <= TAGS.keys():
        continue
    eligible += 1
    if record['research_status'] != STATUS_PENDING:
        continue
    tag_counts = Counter(tag for _, found in observed for tag in found)
    positions = [':'.join(map(str, loc)) for loc, _ in observed]
    roles = ', '.join(TAGS[tag] for tag in sorted(tags))
    record['meanings'] = [TAGS[tag] for tag in sorted(tags)]
    record['meaning_source'] = 'Quranic Arabic Corpus v0.4, aligned by verse and position'
    record['ambiguity'] = ('Возможны разные грамматические функции; все учтённые функции являются служебными.'
                           if len(tags) > 1 else None)
    record['research_status'] = 'Проверяемое соответствие не найдено'
    record['hypotheses'].append({
        'id': 'closed_class_external_quantity_screen',
        'question': 'Есть ли независимая измеримая внешняя величина, непосредственно определяемая этой грамматической функцией?',
        'result': 'Функции слова не задают фиксированного внешнего числа; числовой кандидат не сформулирован.',
        'scope': 'Все вхождения этой словоформы в основном профиле.',
    })
    record['sources'].append({
        'url': 'https://corpus.quran.com/download/',
        'publisher': 'Quranic Arabic Corpus, Kais Dukes', 'version': '0.4',
        'source_sha256': SOURCE_SHA256,
        'pos_counts': dict(sorted(tag_counts.items())),
        'sample_locations': positions[:5],
        'local_alignment': 'data/qac_alignment.csv',
    })
    record['third_column'] = (
        f'Проверяемое соответствие не найдено. Все {record["frequency"]} вхождений — '
        f'служебные формы или местоимения по QAC v0.4 ({roles}; '
        'https://corpus.quran.com/download/). Их грамматическая функция не задаёт '
        'независимой измеримой величины для сравнения с частотой.'
    )
    record['completed_steps'].append('Все вхождения сверены по POS QAC v0.4; проверена применимость внешнего количественного сравнения.')
    record['next_action'] = None
    record['record_version'] += 1
    record['updated_at'] = now()
    atomic_json(WORDS / f'{record["word_id"]}.json', record)
    changed += 1

print(f'Eligible closed-class forms: {eligible}; newly completed: {changed}')
