#!/usr/bin/env python3

import re
import argparse
import pandas as pd
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument('word')
args = parser.parse_args()

def main(args):
    print(args.word)

    roots = pd.read_csv('roots.csv')

    root_word_regexes = []
    for root_word in roots['Root word']:
        root_pattern = []
        for root in re.split(r',\s+', root_word):
            if re.search('/', root):
                base, *others = re.split('/', root)
                if all(len(x) == 1 for x in others):
                    root_pattern.append("{}[{}]?".format(base, ''.join(others)))
                else:
                    root_pattern.append("{}(?:{})?".format(base, '|'.join(others)))
            else:
                root_pattern.append(root)

        root_word_regex = '|'.join(root_pattern)
        root_word_regexes.append(root_word_regex)

    roots['Root word regex'] = pd.Series(root_word_regexes, index=roots.index)

    print(roots.loc[:, ['Root word', 'Root word regex']])

if __name__ == '__main__':
    main(args)
