#!/usr/bin/env python3

import os
import re
import csv
import shutil
import urllib.request
from pprint import pprint
from bs4 import BeautifulSoup

def create_backup_file(filename):
    if os.path.isfile(filename):
        dest_filename = filename + '.orig'
        shutil.copyfile(filename, dest_filename)
        print("Create backup file: {}".format(dest_filename))

def url2html(url):
    req = urllib.request.Request(url, headers={'User-Agent': "Browser"})
    with urllib.request.urlopen(req) as f:
        html = f.read()
    return html

def html2table(html, selector, head_selector="tr th"):
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one(selector)

    # thead
    header = [th.text for th in table.select(head_selector)] # tr th
    # print(header)
    body = [[td.text.strip() for td in row.find_all("td")] for row in table.select("tr + tr")]
    body.insert(0, header)
    return body

def save_as_csv(table, filename):
    with open(filename, "w") as f:
        wr = csv.writer(f, dialect='unix')
        wr.writerows(table)

def fetch_word_roots(filename="roots.csv"):
    url = 'https://www.learnthat.org/pages/view/roots.html'
    html = url2html(url)
    table = html2table(html, selector="table.root_meanings", head_selector="thead tr td")
    subtable = []
    for i, row in enumerate(table):
        trimmed_row = row[1:]
        trimmed_row = list(map(lambda x: re.sub(r'\s+', ' ', x), trimmed_row))
        if i == 0:
            subtable.append(trimmed_row)
            continue
        # trimmed_row[0] = re.sub(r'\s+', ' ', trimmed_row[0])
        trimmed_row[0] = trimmed_row[0].lower() \
            .replace('ann/enn', 'ann, enn') \
            .replace('chrom/o chromat/o', 'chrom/o, chromat/o') \
            .replace('e-', 'e') \
            .replace('esth/aesth', 'esth, aesth') \
            .replace('gen/o/e/ genesis', 'gen/o/e, genesis') \
            .replace('kine/t /mat', 'kine/t, mat') \
            .replace('magn/a/i', 'magn/i') \
            .replace('oxi/oxy', 'oxi, oxy') \
            .replace('rrh/ea /oea/ag', 'rrh/ea/oea/ag') \
            .replace('sy/m /n/l/s', 'sy/m/n/l/s') \
            .replace('phon/o /e/y', 'phon/o/e/y') \
            .replace('viv/i vit', 'viv/i, vit')
        subtable.append(trimmed_row)

    save_as_csv(subtable, filename)

def fetch_word_suffixes(filename="suffixes.csv"):
    url = 'https://www.learnthat.org/pages/view/suffix.html'
    html = url2html(url)
    table = html2table(html, selector="table", head_selector="thead tr td")
    subtable = []
    for i, row in enumerate(table):
        trimmed_row = list(filter(None, row))
        trimmed_row = list(map(lambda x: re.sub(r'\s+', ' ', x), trimmed_row))
        if i == 0:
            subtable.append(trimmed_row)
            continue
        if not trimmed_row[0].startswith('-') and i >= 1:
            trimmed_row.insert(0, subtable[-1][0])
        trimmed_row[0] = trimmed_row[0].lower() \
            .replace('/', ', -') # -gam/gamy => -gam, -gamy
        trimmed_row[0] = re.sub(r' \(-?([a-z]+)\)$', r', -\1', trimmed_row[0])
        # -acity (-ocity) => -acity, -ocity
        subtable.append(trimmed_row)

    save_as_csv(subtable, filename)

def main():
    create_backup_file("roots.csv")
    fetch_word_roots("roots.csv")

    create_backup_file("suffixes.csv")
    fetch_word_suffixes("suffixes.csv")


if __name__ == '__main__':
    main()
