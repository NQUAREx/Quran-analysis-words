# Quran-analysis-words

Полная таблица словоформ Корана для корпуса `Quran_text.txt`: [CSV](data/quran_word_counts.csv) и [XLSX](data/quran_word_counts.xlsx). Третий столбец различает завершённое исследование и ещё не проверенные строки. Огласованные формы: [CSV](data/vocalized_forms.csv). Индекс каждого вхождения: [CSV](data/occurrences.csv). Отдельный индекс вступительных басмал: [CSV](data/unnumbered_initial_basmalas.csv).

Сначала прочитайте [методику](METHODOLOGY.md), [текущее состояние](PROJECT_STATE.md) и [порядок возобновления](RESUME.md). Для проверки: `python quran_words.py verify` (Python 3 и `openpyxl` для пересборки XLSX). Для идемпотентного пересчёта: `python quran_words.py build`; для пересборки экспортов из записей: `python quran_words.py export`.
