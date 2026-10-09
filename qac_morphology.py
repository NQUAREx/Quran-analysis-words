#!/usr/bin/env python3
"""Positionally align QAC v0.4 segments with the supplied text; keep profiles distinct.

The copied QAC source is verbatim and retains its copyright notices and license.
QAC calls some surface-separated words one word; those joins are enumerated below.
"""
import csv
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from quran_words import ROOT, DATA, atomic_json, digest, read_words

SOURCE = ROOT / 'sources/quranic-corpus-morphology-0.4.txt'
SOURCE_SHA256 = 'a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46'
ROW_RE = re.compile(r'^\((\d+):(\d+):(\d+):(\d+)\)\t([^\t]+)\t([^\t]+)\t(.+)$')
# Words represented as a QAC prefix to the following surface token.
BEFORE = {'يا', 'ويا', 'ها'}
# Source-specific joins. Values are our 1-based surface positions; the joined
# token belongs to the preceding QAC word. These six verses are checked by hand.
AFTER = {(2, 181): {4}, (8, 6): {5}, (13, 37): {9},
         (20, 94): {4}, (37, 130): {4}, (72, 16): {2}}


def qac_words():
    if digest(SOURCE.read_bytes()) != SOURCE_SHA256:
        raise ValueError('QAC source hash changed')
    words = defaultdict(list)
    for line in SOURCE.read_text(encoding='utf-8').splitlines():
        match = ROW_RE.fullmatch(line)
        if match:
            s, a, w, segment = map(int, match.group(1, 2, 3, 4))
            words[(s, a, w)].append({'segment': segment, 'form': match[5],
                                      'tag': match[6], 'features': match[7]})
    if len(words) != 77429 or sum(map(len, words.values())) != 128011:
        raise ValueError('Unexpected QAC word/segment coverage')
    return words


def surface_rows():
    verses = defaultdict(list)
    with (DATA / 'occurrences.csv').open(encoding='utf-8', newline='') as handle:
        for row in csv.DictReader(handle):
            verse = (int(row['sura']), int(row['ayah']))
            verses[verse].append(row)
    return verses


def group_surface(rows, verse):
    groups, pending = [], []
    for row in rows:
        pos, word = int(row['position']), row['word']
        if word in BEFORE:
            pending.append(row)
        elif pos in AFTER.get(verse, set()):
            if pending or not groups:
                raise ValueError(f'Unexpected backward join {verse}:{pos}')
            groups[-1].append(row)
        else:
            groups.append(pending + [row])
            pending = []
    if pending:
        raise ValueError(f'Dangling prefix {verse}')
    return groups


def align():
    words = qac_words()
    surface = surface_rows()
    qac_per_verse = Counter((s, a) for s, a, _ in words)
    mapping = {}
    for verse, rows in surface.items():
        groups = group_surface(rows, verse)
        if len(groups) != qac_per_verse[verse]:
            raise ValueError(f'Alignment mismatch at {verse}: {len(groups)} != {qac_per_verse[verse]}')
        for qac_pos, group in enumerate(groups, 1):
            loc = (*verse, qac_pos)
            if loc not in words:
                raise ValueError(f'Absent QAC location {loc}')
            mapping[loc] = group
    if len(mapping) != len(words) or sum(map(len, mapping.values())) != 77800:
        raise ValueError('Incomplete alignment')
    return words, mapping


def stems(segments):
    return [s for s in segments if s['features'].startswith('STEM|')]


def feature(segments, name):
    values = []
    for s in segments:
        for part in s['features'].split('|'):
            if part.startswith(name + ':'):
                values.append(part[len(name) + 1:])
    return values


def build():
    manifest, surface_words = read_words()
    words, mapping = align()
    lemma_counts = Counter()
    lemma_examples = {}
    segment_counts = Counter()
    surface_analysis = defaultdict(lambda: {'pos': Counter(), 'lemmas': Counter(), 'aligned': 0, 'joined': 0})
    rows = []
    for loc in sorted(words):
        segments, group = words[loc], mapping[loc]
        lemmas = feature(stems(segments), 'LEM')
        roots = feature(stems(segments), 'ROOT')
        for lemma in set(lemmas):
            lemma_counts[lemma] += 1
            lemma_examples.setdefault(lemma, group[0]['word'])
        if len(group) == 1:
            current = surface_analysis[group[0]['word']]
            current['aligned'] += 1
            current['pos'].update(s['tag'] for s in stems(segments))
            current['lemmas'].update(set(lemmas))
        else:
            for surface in group:
                surface_analysis[surface['word']]['joined'] += 1
        for segment in segments:
            if segment['features'].startswith('PREFIX|') or segment['features'].startswith('SUFFIX|'):
                segment_counts[(segment['tag'], segment['form'], segment['features'].split('|', 1)[0])] += 1
        rows.append((*loc, ';'.join(r['position'] for r in group),
                     ' '.join(r['word'] for r in group), ';'.join(lemmas),
                     ';'.join(roots), ';'.join(s['tag'] for s in stems(segments))))
    with (DATA / 'qac_alignment.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['sura', 'ayah', 'qac_word_position', 'surface_positions',
                         'surface_words', 'qac_lemmas_buckwalter', 'qac_roots_buckwalter', 'qac_stem_tags'])
        writer.writerows(rows)
    with (DATA / 'qac_lemmas.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['QAC лемма (Buckwalter)', 'Количество слов QAC', 'Пример формы в корпусе'])
        writer.writerows((lemma, n, lemma_examples[lemma]) for lemma, n in sorted(lemma_counts.items(), key=lambda x: (-x[1], x[0])))
    with (DATA / 'qac_affixes.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['QAC POS', 'Форма (Buckwalter)', 'Тип сегмента', 'Количество сегментов'])
        writer.writerows((*key, n) for key, n in sorted(segment_counts.items(), key=lambda x: (-x[1], x[0])))
    with (DATA / 'word_morphology_summary.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['word_id', 'Слово', 'Частота основного профиля',
                         'Однозначно выровнено с QAC', 'В слитых словах QAC',
                         'POS QAC: число сегментов', 'Леммы QAC: число слов'])
        for item in sorted(surface_words, key=lambda x: (-x['frequency'], x['word'])):
            info = surface_analysis[item['word']]
            if info['aligned'] + info['joined'] != item['frequency']:
                raise ValueError(f'Surface morphology coverage mismatch: {item["word"]}')
            writer.writerow([item['word_id'], item['word'], item['frequency'],
                             info['aligned'], info['joined'],
                             json.dumps(dict(sorted(info['pos'].items())), ensure_ascii=False),
                             json.dumps(dict(sorted(info['lemmas'].items())), ensure_ascii=False)])
    profiles = {}
    for lemma in ['yawom', 'yawoma}i*', '$ahor', 'qamar', '$amos']:
        matches = []
        for loc, segments in words.items():
            target = [segment for segment in stems(segments)
                      if f'LEM:{lemma}' in segment['features'].split('|')]
            if target:
                matches.append((loc, segments, target, mapping[loc]))
        forms = Counter(' '.join(r['word'] for r in group) for _, _, _, group in matches)
        numbers = Counter(next((value for value in segment['features'].split('|')
                                if value in {'M', 'F', 'MS', 'FS', 'MP', 'FP', 'MD', 'FD'}), '?')
                          for _, _, target, _ in matches for segment in target)
        profiles[lemma] = {'total': len(matches), 'grammatical_number_tags': dict(numbers),
                           'surface_forms': dict(sorted(forms.items())),
                           'qac_locations': [':'.join(map(str, loc)) for loc, _, _, _ in sorted(matches)]}
    day = profiles['yawom']
    day['singular_masculine_with_possessive_suffix'] = sum(
        1 for _, segments, target, _ in (
            (loc, segments, [s for s in stems(segments) if 'LEM:yawom' in s['features'].split('|')], mapping[loc])
            for loc, segments in words.items())
        if target and any('M' in s['features'].split('|') for s in target)
        and any(s['features'].startswith('SUFFIX|PRON') for s in segments))
    assert day['total'] == 405 and day['grammatical_number_tags']['M'] == 375
    assert day['singular_masculine_with_possessive_suffix'] == 10
    assert profiles['yawoma}i*']['total'] == 70
    assert profiles['$ahor']['total'] == 21 and profiles['$ahor']['grammatical_number_tags']['M'] == 12
    assert profiles['qamar']['total'] == 27
    atomic_json(DATA / 'morphology_audit.json', {
        'qac_source_sha256': SOURCE_SHA256,
        'qac_source_url': 'https://corpus.quran.com/download/',
        'qac_version': '0.4',
        'surface_profile_id': manifest['profile_id'],
        'surface_corpus_sha256': manifest['corpus_sha256'],
        'qac_word_locations': len(words),
        'surface_tokens': sum(map(len, mapping.values())),
        'surface_to_qac_join_difference': sum(map(len, mapping.values())) - len(words),
        'profiles': profiles,
    })
    print(f'QAC words: {len(words)}; surface tokens: {sum(map(len, mapping.values()))}; lemmas: {len(lemma_counts)}')
    for lemma in ['yawom', 'yawoma}i*', '$ahor', 'qamar', '$amos']:
        print(f'{lemma}: {lemma_counts[lemma]}')
    return words, mapping


if __name__ == '__main__':
    build()
