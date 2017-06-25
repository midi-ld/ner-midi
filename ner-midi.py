#!/usr/bin/env python

import sys
import os
import pprint
import operator
import copy
import requests
import time
import Levenshtein
import hashlib

class NERMidi(object):
    def __init__(self, __path):
        self.path = __path
        self.records = []
        self.sep = [' ', '.', '_', '-']

    def process(self):
        for root, dirs, files in os.walk(path):
            for f in files:
                if '.mid' in f:
                    md5_id = hashlib.md5(open(os.path.join(root, f), 'rb').read()).hexdigest()

                    record = {}
                    record['id'] = md5_id
                    # Full path of the MIDI file
                    record['midi_path'] = os.path.join(root, f)
                    # MIDI file name
                    record['midi_filename'] = f
                    # Without the extension
                    record['midi_name'] = f[:f.rfind('.')]

                    record['separators'] = {}
                    for s in self.sep:
                        record['separators'][s] = record['midi_name'].count(s)

                    # Use the max of the previous count as tokenizer
                    record['sep_max'] = max(record['separators'].iteritems(), key=operator.itemgetter(1))[0]
                    temp = copy.copy(record['separators'])
                    # We'll also store the 2nd max
                    del temp[record['sep_max']]
                    record['sep_2nd_max'] = max(temp.iteritems(), key=operator.itemgetter(1))[0]
                    del temp

                    # A draw between '-' and '_' should put priority in the latter
                    if record['sep_max'] == '-' and record['sep_2nd_max'] == '_' and  record['separators'][record['sep_max']] == record['separators'][record['sep_2nd_max']]:
                        record['sep_max'] = '_'
                        record['sep_2nd_max'] = '-'

                    record['tokens'] = [token.strip() for token in record['midi_name'].split(record['sep_max'])]
                    record['normal_blanks'] = ' '.join(record['tokens'])

                    # Use the 2nd_max to separate entities
                    # The latter is only useful if it's > 0
                    record['entities'] = [entity.strip() for entity in record['normal_blanks'].split(record['sep_2nd_max'])] if record['separators'][record['sep_2nd_max']] > 0 else [record['normal_blanks']]

                    self.records.append(record)

        return None

    def dbpedia_link(self):
    	dbp_lookup_uri = "http://lookup.dbpedia.org/api/search/PrefixSearch?QueryClass=&MaxHits=5"
    	params = { 'MaxHits' : 5}
    	headers = { 'Accept' : 'application/json' }
    	for r in self.records:
    	    r['entities_dbp'] = {}
    	    for e in r['entities']:
    		params['QueryString'] = e
    		resp = requests.get(dbp_lookup_uri, headers=headers, params=params).json()
    		if e not in r['entities_dbp']:
    		    r['entities_dbp'] = { e: resp }
    		else:
    		    r['entities_dbp'][e] = resp
    	    time.sleep(1)

    def dbpedia_str_sim_uri_link(self):
        with open('dbp.txt', 'r') as dbp:
            dbp_uris = dbp.readlines()

        for r in self.records:
            mld_str = " ".join(r['entities'])
            hs = 0
            match = None
            for s in dbp_uris:
                dbp_str = s.split('/')[-1].split('>')[0].replace('_', ' ')
                ratio = Levenshtein.ratio(mld_str, dbp_str)
                if ratio > hs:
                    hs = ratio
                    match = dbp_str
            # print "Best match for " + mld_str + " is " + match + " with ratio " + str(hs)
            print "<http://purl.org/midi-ld/pattern/" + r['id'] + "> <http://www.w3.org/2002/07/owl#sameAs> <http://dbpedia.org/resource/" + match.replace(' ', '_') + "> ."


    def print_records(self):
        pp = pprint.PrettyPrinter(indent=4)
        for r in self.records:
            pp.pprint(r)
            print

        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: ner-midi.py PATH-TO-MIDIS"
        exit(1)

    path = sys.argv[1]
    ner_midi = NERMidi(path)
    ner_midi.process()
    ner_midi.dbpedia_str_sim_uri_link()
    # ner_midi.dbpedia_link()
    # ner_midi.print_records()

    exit(0)
