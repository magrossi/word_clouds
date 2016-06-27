import os
import sys
import argparse
import json
import re
import codecs
from csv_classes import *
from sortedcontainers import SortedList, SortedListWithKey
from collections import Counter
from nltk.corpus import stopwords

# from stemming.porter2 import stem # Todo in future versions
# stem("factionally")
# faction

cachedStopWords = stopwords.words("english")

# Especially created for SortedListWithKey to overcome the search by key only
# I don't know why but the original code disregards the key for returning the value
def binarySearch(lst, key, keyFun):
    lo = 0
    hi = len(lst) - 1
    # Continually narrow search until just one element remains
    while (lo < hi):
        mid = (hi + lo)//2
        if keyFun(lst[mid]) < key:
            lo = mid + 1
        else:
            hi = mid
    # Deferred test for equality
    if len(lst) > 0 and hi == lo and keyFun(lst[lo]) == key:
        return lo
    else:
        raise ValueError

def countWords(words):
    # return [{ word : count }]
    cnt = Counter()
    for word in words:
        cnt[word] += 1
    return cnt

def getWords(text):
    wordList = re.sub("[^\w]", " ", text.lower()).split()
    return [word for word in wordList if word not in cachedStopWords and len(word) > 1 and not word.isdigit()]

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory')
    args = parser.parse_args()
    print args
    if args.directory:
        print "Starting directory in: " + args.directory
    else:
        print "Invalid usage. Must provide -d <starting directory>."
        quit()

    # Counter
    totalTermTF = 0

    # List of objects
    categories = SortedListWithKey(key=lambda c: c.cat_name) # of Category() class
    terms = SortedListWithKey(key=lambda t: t.term) # of Term() class

    # Output CSV files
    terCSV = codecs.open(os.path.normpath("c:/data/csv_data/terms.csv"), 'w', 'utf-8')
    catCSV = codecs.open(os.path.normpath("c:/data/csv_data/categories.csv"), 'w', 'utf-8')
    docCSV = codecs.open(os.path.normpath("c:/data/csv_data/documents.csv"), 'w', 'utf-8')
    tfCSV = codecs.open(os.path.normpath("c:/data/csv_data/termdoc_tf.csv"), 'w', 'utf-8')

    # Ids
    maxDocId = 0
    maxCatId = 0
    maxTermId = 0

    # Temp objects
    cat = None
    doc = None
    term = None
    term_tf = None

    # Processing
    for root, dirs, files in os.walk(args.directory):
        print 'Walking directory {0}'.format(root)
        for file in files:
            if file.endswith(".json"):
                fname = os.path.join(root, file)
                with open(fname, 'rb') as json_file:
                    try:
                        # Load article in JSON format
                        json_data = json.load(json_file)
                        # Get/Add Cat()
                        catKey = json_data['category'].lower()
                        if not cat or cat.cat_name != catKey:
                            # Try to find category in list
                            try:
                                cat_idx = binarySearch(categories, catKey, keyFun=lambda c: c.cat_name)
                                cat = categories[cat_idx]
                            except ValueError:
                                # If not found create and add to list
                                maxCatId += 1
                                cat = Cat()
                                cat.cat_name = catKey
                                cat.cat_id = maxCatId
                                categories.add(cat)
                                catCSV.write(cat.ToCSV())
                        # Add Doc()
                        doc = Doc()
                        doc.cat_id = cat.cat_id
                        doc.doc_date = json_data['date']
                        doc.url = json_data['url']
                        maxDocId += 1
                        doc.doc_id = maxDocId
                        docCSV.write(doc.ToCSV())
                        # Add Term() and TermTF()
                        count = countWords(getWords(json_data['text']))
                        count_len = len(count)
                        for word in count:
                            # Get/Add Term()
                            try:
                                term_idx = binarySearch(terms, word, keyFun=lambda t: t.term)
                                term = terms[term_idx]
                            except ValueError:
                                maxTermId += 1
                                term = Term()
                                term.term = word
                                term.term_id = maxTermId
                                terms.add(term)
                                terCSV.write(term.ToCSV())
                            # Add TF and TF_NORM to TermTF
                            term_tf = TermTF()
                            term_tf.term_id = term.term_id
                            term_tf.doc_id = doc.doc_id
                            term_tf.tf = count[word]
                            term_tf.tf_norm = count[word]/float(count_len)
                            tfCSV.write(term_tf.ToCSV())
                            totalTermTF += 1
                    except Exception, e:
                        print 'Error in article '.format(fname)
                        print str(e)
    print 'Added a total of {0} categories, {1} documents, {2} terms and {3} term tfs to CSV files.'.format(maxCatId, maxDocId, maxTermId, totalTermTF)

    terCSV.close()
    catCSV.close()
    docCSV.close()
    tfCSV.close()


if __name__ == "__main__":
   main(sys.argv[1:])
