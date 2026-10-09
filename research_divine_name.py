"""Screen QAC's proper-name lemma of God for external numerical referents."""
import json
from collections import Counter, defaultdict

from qac_morphology import SOURCE_SHA256, align, stems
from quran_words import WORDS, STATUS_PENDING, atomic_json, identity, now, read_words

manifest, records = read_words()
words, mapping = align()
by_form = defaultdict(list)
for loc, group in mapping.items():
    lemma = [s for s in stems(words[loc]) if 'LEM:{ll~ah' in s['features'].split('|')]
    if lemma and len(group) == 1:
        by_form[group[0]['word']].append(loc)

assert sum(map(len, by_form.values())) == 2699 and len(by_form) == 11
changed = 0
for record in records:
    word = record['word']
    if word not in by_form:
        continue
    assert len(by_form[word]) == record['frequency']
    if record['research_status'] != STATUS_PENDING:
        continue
    record['meanings'] = ['имя Бога в кораническом тексте; приставки остаются частью словоформы']
    record['meaning_source'] = 'Quranic Arabic Corpus v0.4; собственное имя (PN), лемма {ll~ah'
    record['ambiguity'] = None
    record['research_status'] = 'Проверяемое соответствие не найдено'
    record['hypotheses'].append({
        'id': 'divine_name_empirical_number',
        'question': 'Существует ли независимо измеряемое число, заданное самим референтом имени?',
        'result': 'У религиозного собственного имени нет установленной эмпирической числовой величины для сравнения с частотой написания. Символические системы требуют отдельного явного определения.',
    })
    record['sources'].append({'url': 'https://corpus.quran.com/download/',
                              'publisher': 'Quranic Arabic Corpus, Kais Dukes',
                              'version': '0.4', 'source_sha256': SOURCE_SHA256,
                              'qac_lemma': '{ll~ah',
                              'sample_locations': [':'.join(map(str, x)) for x in by_form[word][:5]]})
    record['third_column'] = (
        f'Проверяемое соответствие не найдено. Все {record["frequency"]} вхождений формы '
        f'{word} относятся к имени Бога по QAC v0.4 '
        '(https://corpus.quran.com/download/). Для религиозного имени нет независимо '
        'измеряемой физической величины, которую определяет эта частота; символическую '
        'интерпретацию нужно задавать отдельно.'
    )
    record['completed_steps'].append('Все вхождения формы сопоставлены с леммой собственного имени QAC; проверена применимость независимого количественного сравнения.')
    record['next_action'] = None
    record['record_version'] += 1
    record['updated_at'] = now()
    atomic_json(WORDS / f'{record["word_id"]}.json', record)
    changed += 1
print(f'Divine-name forms: {len(by_form)}; newly completed: {changed}')
