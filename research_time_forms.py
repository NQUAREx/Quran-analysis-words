"""Check every surface form mapped to QAC day/month lemmas against calendar facts."""
import json

from quran_words import DATA, WORDS, STATUS_PENDING, atomic_json, identity, now, read_words

manifest, _ = read_words()
audit = json.loads((DATA / 'morphology_audit.json').read_text())
profiles = audit['profiles']
day_forms = profiles['yawom']['surface_forms']
day_then_forms = profiles['yawoma}i*']['surface_forms']
month_forms = profiles['$ahor']['surface_forms']
assert not (set(day_forms) & set(day_then_forms) or set(day_forms) & set(month_forms))
changes = 0
for name, counts, lemma, mode in [
    ('день', day_forms, 'yawom', 'day'),
    ('в тот день', day_then_forms, 'yawoma}i*', 'day_then'),
    ('месяц', month_forms, '$ahor', 'month'),
]:
    for form, counted in counts.items():
        path = WORDS / (identity(manifest['corpus_sha256'], form) + '.json')
        item = json.loads(path.read_text())
        assert item['frequency'] == counted
        if item['research_status'] != STATUS_PENDING:
            continue
        item['meanings'] = [name]
        item['meaning_source'] = 'Quranic Arabic Corpus v0.4, positional alignment'
        item['ambiguity'] = None
        if mode == 'day_then':
            status = 'Проверяемое соответствие не найдено'
            explanation = (f'Проверяемое соответствие не найдено. Все {counted} вхождений {form} '
                           'выражают «в тот день» по отдельной лемме QAC; указательный '
                           'эсхатологический или повествовательный контекст не определяет '
                           'независимого количества суток в реальном мире. '
                           'Разметка: https://corpus.quran.com/download/.')
            hypothesis = {'id': 'deictic_day_external_value', 'result': 'Независимая внешняя количественная величина для данного указательного выражения не определена.'}
            sources = [{'url': 'https://corpus.quran.com/download/', 'publisher': 'Quranic Arabic Corpus', 'version': '0.4', 'qac_lemma': lemma}]
        else:
            status = 'Соответствие не воспроизведено'
            if mode == 'day':
                hypothesis = {'id': 'days_per_earth_year', 'observed_frequency': counted,
                              'external_value': 365.25, 'unit': 'суток', 'result': 'не совпало'}
                explanation = (f'Соответствие не воспроизведено. {counted} вхождений формы {form} '
                               'не равны 365,25 суткам земного года (NASA: '
                               'https://science.nasa.gov/earth/facts/). Форма относится к лемме '
                               'يوم по QAC; объединять её с другими формами можно только в '
                               'отдельном профиле (RECOUNT.md).')
                sources = [{'url': 'https://science.nasa.gov/earth/facts/', 'publisher': 'NASA Science', 'section': 'Quick Facts', 'excerpt': 'Length of Year 365.25 days'},
                           {'url': 'https://corpus.quran.com/download/', 'publisher': 'Quranic Arabic Corpus', 'version': '0.4', 'qac_lemma': lemma}]
            else:
                hypothesis = {'id': 'months_per_islamic_year', 'observed_frequency': counted,
                              'external_value': 12, 'unit': 'месяцев', 'result': 'не совпало'}
                explanation = (f'Соответствие не воспроизведено для формы {form}: {counted} '
                               'вхождений против 12 месяцев исламского календаря '
                               '(https://www.timeanddate.com/calendar/islamic-calendar.html). '
                               'В отдельном профиле QAC 12 имеет вся лемма شهر в единственном '
                               'числе; см. RECOUNT.md.')
                sources = [{'url': 'https://www.timeanddate.com/calendar/islamic-calendar.html',
                            'publisher': 'timeanddate.com', 'section': 'Calendar Structure',
                            'excerpt': 'The Islamic calendar has 12 months with 29 or 30 days.'},
                           {'url': 'https://corpus.quran.com/download/', 'publisher': 'Quranic Arabic Corpus', 'version': '0.4', 'qac_lemma': lemma}]
        item['research_status'] = status
        item['hypotheses'].append(hypothesis)
        item['sources'].extend(sources)
        item['third_column'] = explanation
        item['completed_steps'].append('Все вхождения формы сопоставлены с временной леммой QAC и проверена применимость календарного сравнения.')
        item['next_action'] = None
        item['record_version'] += 1
        item['updated_at'] = now()
        atomic_json(path, item)
        changes += 1
print('Newly completed time forms:', changes)
