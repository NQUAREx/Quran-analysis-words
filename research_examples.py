"""Idempotently persist three manually checked research examples."""
import json
from quran_words import WORDS, atomic_json, identity, now, CORPUS, digest, STATUS_PENDING

corpus_sha = digest(CORPUS.read_bytes())
updates = {
    'يوم': {
        'meanings': ['день', 'День суда и иные контекстные употребления'],
        'ambiguity': 'Форма включает обычный день и эсхатологические контексты (например, 1:4); не все вхождения обозначают земные сутки.',
        'research_status': 'Соответствие не воспроизведено',
        'hypotheses': [{'claim': 'Частота формы يوم равна числу суток в земном году.', 'observed_frequency': 217, 'external_value': 365.25, 'result': 'не совпало', 'caveat': 'Внешнее число относится к продолжительности земного года в сутках, а корпусная частота — к одной словоформе; другие формы не добавляются.'}],
        'external_facts': [{'fact': 'Продолжительность земного года', 'value': 365.25, 'unit': 'суток', 'source_url': 'https://science.nasa.gov/earth/facts/'}],
        'sources': [{'url': 'https://science.nasa.gov/earth/facts/', 'publisher': 'NASA Science', 'section': 'Quick Facts', 'accessed': '2026-10-09', 'excerpt': 'Length of Year 365.25 days', 'page_sha256': '4b13f71ac69ad67c2d63b08c6a212074f4d05472e9fa2fb20b55ff1e29055343'}],
        'third_column': 'Соответствие не воспроизведено. 217 употреблений формы يوم не равны 365,25 суткам земного года (NASA: https://science.nasa.gov/earth/facts/). Среди контекстов есть День суда (1:4); частота одной формы не равна числу календарных дней.',
        'completed_steps': ['Просмотрены контексты формы в индексе, включая 1:4 и 2:254.', 'Проверен внешний показатель NASA и точное число.'],
        'next_action': None,
    },
    'شهر': {
        'meanings': ['месяц как календарная или временная единица'],
        'ambiguity': 'Форма встречается в выражении شهر رمضان (2:185), как мера времени (34:12) и в ألف شهر (97:3).',
        'research_status': 'Соответствие не воспроизведено',
        'hypotheses': [{'claim': 'Частота формы شهر равна числу месяцев в исламском году.', 'observed_frequency': 4, 'external_value': 12, 'result': 'не совпало', 'caveat': 'Другие словоформы месяца не прибавляются к этому ключу.'}],
        'external_facts': [{'fact': 'Число месяцев в исламском календаре', 'value': 12, 'unit': 'месяцев', 'source_url': 'https://www.timeanddate.com/calendar/islamic-calendar.html'}],
        'sources': [{'url': 'https://www.timeanddate.com/calendar/islamic-calendar.html', 'publisher': 'timeanddate.com', 'section': 'Calendar Structure', 'accessed': '2026-10-09', 'excerpt': 'The Islamic calendar has 12 months with 29 or 30 days.', 'page_sha256': '649467e36fee7818e49bb0b2a86ebfdec06813b2c8dc73d7d9a18c5b22b079c9'}],
        'third_column': 'Соответствие не воспроизведено. Форма شهر встречается 4 раза, а исламский календарь содержит 12 месяцев (https://www.timeanddate.com/calendar/islamic-calendar.html, раздел Calendar Structure). Это календарное соглашение; другие формы не включены.',
        'completed_steps': ['Проверены все 4 вхождения: 2:185, два в 34:12 и 97:3.', 'Проверена структура исламского календаря во внешнем источнике.'],
        'next_action': None,
    },
    'البر': {
        'meanings': ['добродетель', 'суша'],
        'ambiguity': 'После удаления огласовок الْبِرَّ (2:177) и الْبَرِّ (5:96) объединяются в один ключ.',
        'research_status': 'Недостаточно данных',
        'hypotheses': [{'claim': 'Все употребления البر обозначают сушу и могут сравниваться с долей суши.', 'observed_frequency': 19, 'result': 'отклонено из-за разных значений', 'caveat': 'Для сравнения нужна разметка значения каждого вхождения; 19 не является числом упоминаний суши.'}],
        'external_facts': [], 'sources': [{'url': 'Quran_text.txt#2:177', 'publisher': 'предоставленный корпус', 'section': '2:177', 'accessed': '2026-10-09', 'excerpt': 'لَّيْسَ الْبِرَّ'}, {'url': 'Quran_text.txt#5:96', 'publisher': 'предоставленный корпус', 'section': '5:96', 'accessed': '2026-10-09', 'excerpt': 'صَيْدُ الْبَرِّ'}],
        'third_column': 'Недостаточно данных. 19 вхождений объединяют «добродетель» (2:177, الْبِرَّ) и «сушу» (5:96, الْبَرِّ). Сопоставление всех 19 с площадью суши некорректно без разметки значений каждого вхождения.',
        'completed_steps': ['Проверены противоположные значения в контекстах 2:177 и 5:96.', 'Отклонена интерпретация всей частоты как числа упоминаний суши.'],
        'open_questions': ['Разметить все вхождения по значениям в отдельном семантическом профиле.'],
        'next_action': 'Семантически разметить 19 вхождений и отдельно проверить внешнюю гипотезу.',
    },
}

for word, fields in updates.items():
    path = WORDS / (identity(corpus_sha, word) + '.json')
    item = json.loads(path.read_text())
    if item['research_status'] != STATUS_PENDING:
        continue
    item.update(fields)
    item['record_version'] += 1
    item['updated_at'] = now()
    atomic_json(path, item)
    print(word, item['frequency'], item['research_status'])
