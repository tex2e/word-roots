#!/usr/bin/env python3

import re
import sys
import csv
import argparse
import itertools
import pandas as pd
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument('word')
output_options = parser.add_mutually_exclusive_group()
output_options.add_argument('--dat',  action='store_true')
output_options.add_argument('--tree', action='store_true')
args = parser.parse_args()

def assign_root_word_regex(pandas_frame_roots):
    root_word_regexes = []
    for root_word in pandas_frame_roots['Root word']:
        root_pattern = []
        for root in re.split(r',\s+', root_word):
            if re.search('/', root):
                base, *others = re.split('/', root)
                if len(others) == 1 and len(others[0]) == 1:
                    root_pattern.append("{}{}?".format(base, others[0]))
                elif all(len(x) == 1 for x in others):
                    root_pattern.append("{}[{}]?".format(base, ''.join(others)))
                else:
                    root_pattern.append("{}(?:{})?".format(base, '|'.join(others)))
            else:
                root_pattern.append(root)

        root_word_regex = '|'.join(root_pattern)
        root_word_regexes.append(root_word_regex)

    pandas_frame_roots['Root word regex'] = \
        pd.Series(root_word_regexes, index=pandas_frame_roots.index)
    return pandas_frame_roots

def assign_suffix_word_regex(pandas_frame_suffixes):
    suffixes_word_regexes = []
    for suffix_word in pandas_frame_suffixes['Suffix']:
        suffix_pattern = []
        for suffix in re.split(r',\s+', suffix_word):
            suffix_pattern.append(re.sub(r'^-', '', suffix))

        if len(suffix_pattern) == 1:
            suffixes_word_regexes.append("{}$".format(suffix_pattern[0]))
        else:
            suffixes_word_regexes.append("(?:{})$".format('|'.join(suffix_pattern)))

    pandas_frame_suffixes['Suffix regex'] = \
        pd.Series(suffixes_word_regexes, index=pandas_frame_suffixes.index)
    return pandas_frame_suffixes

def find_roots(word, root_regexes):
    """
    Find roots from given word.
    Returns array of tuple, and each tuple contains (start, end, regex_i)
    where regex_i represents index, so 0 <= regex_i < len(root_regexes)
    """
    result = []
    i = 0
    while i < len(word):
        tmp_word = word[i:]
        matched_regexes = []
        for regex_i, root_regex in enumerate(root_regexes):
            m = re.match(root_regex, tmp_word)
            if m:
                matched_regexes.append( (i + m.start(), i + m.end(), regex_i) )

        if len(matched_regexes) == 0:
            i += 1
        else:
            matched_regexes.sort()
            longest_match = matched_regexes[-1]
            start = longest_match[0]
            end   = longest_match[1]
            diff  = abs(end - start)
            # (root word has 2 chars at least) or (at beginning of the given word)
            if diff >= 2 or i == 0:
                result.extend(
                    list(itertools.takewhile(
                        lambda x: x[1] == longest_match[1],
                        reversed(matched_regexes))))
            i += diff

    # print(result)
    return result

def find_suffix(word, suffix_regexes):
    matched_regexes = []
    for regex_i, suffix_regex in enumerate(suffix_regexes):
        m = re.search(suffix_regex, word)
        if m:
            matched_regexes.append( (m.start(), m.end(), regex_i) )

    if len(matched_regexes) >= 1:
        matched_regexes.sort()
        longest_match = matched_regexes[-1]
        return list(itertools.takewhile(
            lambda x: x[0] == longest_match[0],
            reversed(matched_regexes)))
    else:
        return []

def get_word_structure(word, roots_data_frame, suffixes_data_frame):
    """
    Create word structure for display.
    Returns array of tuple, and each tuple contains (style, root_word, meaning, start, end)
    """

    result = find_roots(word, roots_data_frame['Root word regex'])

    root_starts   = [x[0] for x in result]
    root_ends     = [x[1] for x in result]
    root_indices  = [x[2] for x in result]
    root_words    = roots_data_frame.iloc[root_indices, 0].as_matrix()
    root_meanings = roots_data_frame.iloc[root_indices, 1].as_matrix()

    word_fragments = []
    prev_end = 0
    for start, end, meaning in zip(root_starts, root_ends, root_meanings):
        diff = start - prev_end
        if diff > 0:
            word_end = prev_end + diff
            word_fragments.append( ('none', word[prev_end:word_end], '', prev_end, word_end) )
        word_fragments.append( ('styled', word[start:end], meaning, start, end) )
        prev_end = end

    word_end = len(word)
    if prev_end < word_end:
        # Find suffix
        result = find_suffix(word[prev_end:word_end], suffixes_data_frame['Suffix regex'])
        word_fragments_suffix = []
        if len(result) > 0:
            suffix_start, suffix_end, suffix_regex_i = result[0]
            suffix_starts   = [x[0] for x in result]
            suffix_ends     = [x[1] for x in result]
            suffix_indices  = [x[2] for x in result]
            suffix_words    = suffixes_data_frame.iloc[suffix_indices, 0].as_matrix()
            suffix_meanings = suffixes_data_frame.iloc[suffix_indices, 1].as_matrix()
            for start, end, meaning in zip(suffix_starts, suffix_ends, suffix_meanings):
                start += prev_end
                end   += prev_end
                word_fragments_suffix.append(
                    ('styled', word[start:end], meaning, start, end) )
            word_end = start # Move word end boundary to suffix start

        if prev_end < word_end:
            word_fragments.append( ('none', word[prev_end:word_end], '', prev_end, word_end) )

        word_fragments.extend(word_fragments_suffix)

    # pprint(word_fragments)
    return word_fragments

def show_tree(word_fragments):
    word_len = word_fragments[-1][-1] # Last word's end pos is word length
    tree_down_and_right = "┌"
    tree_verticle = "│"
    tree_verticle_and_right = "├"
    tree_horizontal = "─"
    tree_prefix = ""
    prev_start = 0
    # pprint(word_fragments)
    for i, (style, root_word, meaning, start, end) in enumerate(word_fragments):
        if style == 'none':
            tree_prefix += " "
            continue
        if prev_start == start and i != 0:
            tree_prefix = tree_prefix[:-1]
            joint = tree_verticle_and_right
        else:
            joint = tree_down_and_right
        tree_prefix += " " * (start - prev_start)
        tree_branch = tree_horizontal * (word_len + len(word_fragments) - len(tree_prefix))
        print("{}{}{} {}".format(tree_prefix, joint, tree_branch, meaning))
        tree_prefix += tree_verticle
        prev_start = start

    style_bold      = "\033[1m"
    style_underline = "\033[4m"
    style_clear     = "\033[0m"
    word_display    = ""
    prev_start = 0
    for i, (style, root_word, meaning, start, end) in enumerate(word_fragments):
        if prev_start == start and i != 0:
            continue
        if style == 'styled':
            word_display += style_bold + root_word + style_clear + " "
        else:
            word_display += root_word + " "
        prev_start = start
    print(word_display)

def show_dat(word_fragments):
    writer = csv.writer(sys.stdout, delimiter="\t")
    writer.writerows([ ["{}..{}".format(x[3], x[4]), x[1], x[2]] for x in word_fragments if not x[0] == 'none'])

def main(args):
    word = args.word
    roots = pd.read_csv('roots.csv')
    roots = assign_root_word_regex(roots)
    suffixes = pd.read_csv('suffixes.csv')
    suffixes = assign_suffix_word_regex(suffixes)
    word_fragments = get_word_structure(word, roots, suffixes)

    print()
    if args.dat:
        show_dat(word_fragments)
    elif args.tree:
        show_tree(word_fragments)
    else:
        show_tree(word_fragments)
    print()

if __name__ == '__main__':
    main(args)
