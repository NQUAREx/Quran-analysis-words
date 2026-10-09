#!/usr/bin/env python3
"""Persist checked morphology-profile claims without changing surface frequencies."""
import json

from quran_words import DATA, WORDS, atomic_json, identity, now, read_words

manifest, _ = read_words()
audit = json.loads((DATA / 'morphology_audit.json').read_text())
evidence = json.loads((DATA.parent / 'sources/evidence.json').read_text())
facts = {f['id']: f for f in evidence['facts']}

findings = {
    'profile': 'Quranic Arabic Corpus v0.4, positional alignment to corpus SHA-256 ' + manifest['corpus_sha256'],
    'source_sha256': audit['qac_source_sha256'],
    'updated_at': now(),
    'candidates': [
        {
            'id': 'qac_singular_months_12',
            'lemma_buckwalter': '$ahor', 'lemma_arabic': 'شهر',
            'count_definition': 'QAC lemma, masculine singular forms, including attached prefixes',
            'count': 12, 'all_numbers_count': 21,
            'external_fact': '12 months in the Islamic calendar',
            'external_fact_id': 'islamic_calendar_months',
            'status': 'Условное/культурное соответствие',
            'third_column_ru': 'Условное/культурное соответствие. 12 форм единственного числа леммы شهر по QAC совпадают с 12 месяцами исламского календаря. Источник: https://www.timeanddate.com/calendar/islamic-calendar.html. Все числа леммы вместе дают 21; правило календаря условно, а 9:36 прямо называет 12 месяцев.',
            'limitations': ['Это отдельный лемматизированный профиль, а не частота формы شهر в основной таблице.', 'Сопоставление общеизвестно; новизна не заявляется.'],
            'qac_locations': audit['profiles']['$ahor']['qac_locations'],
        },
        {
            'id': 'qac_moon_27_sidereal_days',
            'lemma_buckwalter': 'qamar', 'lemma_arabic': 'قمر',
            'count_definition': 'All QAC lemma occurrences, including attached prefixes',
            'count': 27,
            'external_fact': 'Sidereal lunar orbital period 27.321661 Earth days',
            'external_fact_ids': ['moon_orbit_nasa_rounded', 'sidereal_month_britannica'],
            'prior_publication_id': 'moon_27_prior_art',
            'absolute_difference_days': 0.321661,
            'relative_difference_percent': round(100 * 0.321661 / 27.321661, 3),
            'status': 'Приблизительное совпадение',
            'third_column_ru': 'Приблизительное совпадение. Лемма قمر встречается 27 раз; сидерический оборот Луны длится 27,321661 суток (https://www.britannica.com/science/sidereal-month), NASA округляет до 27 суток (https://science.nasa.gov/moon/facts/). Отклонение 1,18 %. Сопоставление опубликовано ранее (https://www.quranmiracles.com/2011/03/the-moon/, 2011); необычность не установлена.',
            'limitations': ['Отличается от синодического месяца.', 'Источник NASA округляет физическое значение.', 'Кандидат обнаружен после просмотра частоты; множество проверок не ограничено.', 'Это соответствие публиковалось 22 марта 2011 года.'],
            'qac_locations': audit['profiles']['qamar']['qac_locations'],
        },
    ],
    'rejected_or_unresolved': [
        {
            'id': 'day_356', 'lemma_buckwalter': 'yawom', 'claimed_count': 356,
            'status': 'Не воспроизведено без правила включения',
            'observed_profiles': {'surface_form_yawm': 217, 'qac_lemma_all_numbers': 405,
                                  'qac_lemma_singular': 375, 'qac_day_then': 70,
                                  'qac_lemma_all_plus_day_then': 475},
            'next_action': 'Получить список 356 вхождений или точное правило включения и сравнить по позициям.',
        },
        {
            'id': 'day_365', 'lemma_buckwalter': 'yawom', 'claimed_count': 365,
            'status': 'Получается только при специальном исключении',
            'calculation': '375 QAC singular day forms - 10 possessive suffix forms (يومكم, يومهم) = 365',
            'limitation': 'Притяжательный суффикс не меняет грамматическое число, поэтому это исключение не является единым правилом подсчёта единственного числа.',
        },
    ],
}
atomic_json(DATA / 'lemma_findings.json', findings)

for word, hypothesis_id, note, description in [
    ('يوم', 'qac_day_recount', 'Соответствие не воспроизведено. Частота самой формы يوم — 217. По отдельному профилю QAC лемма يوم даёт 405 вхождений, из них 375 форм единственного числа; 365 получается исключением 10 форм يومكم и يومهم. Число 356 пока не воспроизведено; методика: RECOUNT.md. Длина земного года около 365,25 суток (https://science.nasa.gov/earth/facts/).', 'Повторный подсчёт по QAC: 405 все числа, 375 единственное, 70 отдельная лемма يومئذ.'),
    ('شهر', 'qac_month_recount', 'Соответствие не воспроизведено для этой словоформы: شهر — 4. В отдельном профиле QAC лемма شهر имеет 12 форм единственного числа; это условное совпадение с 12 месяцами исламского календаря (https://www.timeanddate.com/calendar/islamic-calendar.html). Все числа леммы вместе дают 21; см. RECOUNT.md.', 'Повторный подсчёт по QAC: 21 все числа, 12 единственное, 7 множественное, 2 двойственное.'),
]:
    wid = identity(manifest['corpus_sha256'], word)
    path = WORDS / f'{wid}.json'
    item = json.loads(path.read_text())
    if any(h.get('id') == hypothesis_id for h in item['hypotheses']):
        continue
    item['hypotheses'].append({'id': hypothesis_id, 'result': description, 'profile': 'QAC v0.4', 'evidence_file': 'data/morphology_audit.json'})
    item['third_column'] = note
    item['completed_steps'].append(description)
    item['record_version'] += 1
    item['updated_at'] = now()
    atomic_json(path, item)
    print(word, item['research_status'], item['frequency'])
