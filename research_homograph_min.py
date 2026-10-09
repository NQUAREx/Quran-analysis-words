"""Document the high-frequency homograph من with all QAC grammatical uses."""
import json
from collections import Counter

from qac_morphology import SOURCE_SHA256, align, stems
from quran_words import WORDS, STATUS_PENDING, atomic_json, identity, now, read_words

manifest, _ = read_words()
path = WORDS / (identity(manifest['corpus_sha256'], 'من') + '.json')
item = json.loads(path.read_text())
if item['research_status'] == STATUS_PENDING:
    words, mapping = align()
    tags = Counter()
    verb_locations = []
    for loc, group in mapping.items():
        if len(group) == 1 and group[0]['word'] == 'من':
            found = [s['tag'] for s in stems(words[loc])]
            tags.update(found)
            if 'V' in found:
                verb_locations.append(':'.join(map(str, loc)))
    expected = {'P': 2366, 'REL': 343, 'COND': 37, 'INTG': 13, 'V': 4}
    assert dict(tags) == expected and sum(tags.values()) == item['frequency'] == 2763
    assert verb_locations == ['3:164:2', '6:53:7', '12:90:11', '28:82:18']
    item['meanings'] = ['предлог «из/от»', 'относительное «кто»', 'условное «кто бы»',
                        'вопросительное «кто?»', 'глагол «оказал милость»']
    item['meaning_source'] = 'Quranic Arabic Corpus v0.4; сверено с контекстами Quran_text.txt'
    item['ambiguity'] = 'Написание без огласовок объединяет служебные формы и глагол مَنَّ.'
    item['research_status'] = 'Проверяемое соответствие не найдено'
    item['hypotheses'].append({'id': 'single_referent_min',
                                'question': 'Можно ли сопоставить все 2763 употребления с одной внешней величиной?',
                                'result': 'Нет единого референта: пять грамматических функций, включая четыре глагола.',
                                'qac_pos_counts': expected})
    item['sources'].append({'url': 'https://corpus.quran.com/download/',
                            'publisher': 'Quranic Arabic Corpus, Kais Dukes', 'version': '0.4',
                            'source_sha256': SOURCE_SHA256, 'verb_locations': verb_locations})
    item['third_column'] = (
        'Проверяемое соответствие не найдено. 2763 вхождения من объединяют предлог (2366), '
        'относительное местоимение (343), условное (37), вопросительное (13) и глагол مَنَّ '
        '(4; например, 3:164). Для этих разных значений единая внешняя количественная '
        'характеристика не определена. Разметка: https://corpus.quran.com/download/.'
    )
    item['completed_steps'].append('Все 2763 вхождения распределены по POS QAC; четыре глагольных случая сверены с арабским текстом.')
    item['next_action'] = None
    item['record_version'] += 1
    item['updated_at'] = now()
    atomic_json(path, item)
    print('من', item['research_status'])
