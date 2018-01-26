#!/usr/bin/env python3

import re
import sys
import csv
import argparse
import pandas as pd
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument('word')
output_options = parser.add_subparsers(dest='output')
output_options.add_parser('--dat')
output_options.add_parser('--tree')
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

    pandas_frame_roots['Root word regex'] = pd.Series(root_word_regexes, index=pandas_frame_roots.index)
    return pandas_frame_roots

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
        for regex_i, root_with_regex in enumerate(root_regexes):
            m = re.match(root_with_regex, tmp_word)
            if m:
                matched_regexes.append( (i + m.start(), i + m.end(), regex_i) )

        if len(matched_regexes) == 0:
            i += 1
        else:
            longest_match = sorted(matched_regexes)[-1]
            start = longest_match[0]
            end   = longest_match[1]
            diff  = abs(end - start)
            if diff >= 2: # root word has 2 chars at least
                result.append(longest_match)
            elif i == 0: # at beginning of the given word
                result.append(longest_match)
            i += diff

    return result

def get_word_structure(word, roots_data_frame):
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
        diff = abs(prev_end - start)
        if diff > 0:
            word_end = prev_end + diff
            word_fragments.append( ('none', word[prev_end:word_end], '', prev_end, word_end) )
        word_fragments.append( ('styled', word[start:end], meaning, start, end) )
        prev_end = end

    if prev_end < len(word):
        word_end = len(word)
        word_fragments.append( ('none', word[prev_end:word_end], '', prev_end, word_end) )

    return word_fragments

def show_tree(word_fragments):
    word_len = word_fragments[-1][-1] # last word's end pos is word length
    tree_down_and_right = "┌"
    tree_verticle = "│"
    tree_horizontal = "─"
    tree_prefix = ""
    prev_start = 0
    for i, (style, root_word, meaning, start, end) in enumerate(word_fragments):
        if style == 'none':
            tree_prefix += " "
            continue
        tree_prefix += " " * (start - prev_start)
        tree_branch = tree_horizontal * (word_len + len(word_fragments) - len(tree_prefix))
        print("{}{}{} {}".format(tree_prefix, tree_down_and_right, tree_branch, meaning))
        tree_prefix += tree_verticle
        prev_start = start

    style_bold      = "\033[1m"
    style_underline = "\033[4m"
    style_clear     = "\033[0m"
    word_display    = ""
    for style, root_word, meaning, start, end in word_fragments:
        if style == 'styled':
            word_display += style_bold + root_word + style_clear + " "
        else:
            word_display += root_word + " "
    print(word_display)

def show_dat(word_fragments):
    writer = csv.writer(sys.stdout, delimiter="\t")
    writer.writerows([ ["{}..{}".format(x[3], x[4]), x[1], x[2]] for x in word_fragments if not x[0] == 'none'])

def main(args):
    word = args.word
    roots = pd.read_csv('roots.csv')
    roots = assign_root_word_regex(roots)
    word_fragments = get_word_structure(word, roots)

    print()
    if args.output == 'dat':
        show_dat(word_fragments)
    elif args.output == 'tree':
        show_tree(word_fragments)
    else:
        show_tree(word_fragments)
    print()

if __name__ == '__main__':
    main(args)
