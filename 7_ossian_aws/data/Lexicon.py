#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

# from naive.naive_util import *
# from VoiceElements import ConfiguredComponent

import os
import sys
import re
import regex
import unicodedata
import shutil
import glob
import fileinput
import subprocess
import codecs

import default.const as c

from processors.NodeEnricher import NodeEnricher
from processors.UtteranceProcessor import SUtteranceProcessor

from UtteranceProcessor import Element

from util.LookupTable import LookupTable
from util.ipa2sampa import ipa2sampa

from naive.naive_util import readlist, writelist, safetext

import util.NodeProcessors as NodeProcessors


class Lexicon(SUtteranceProcessor):

    def __init__(self, processor_name='lexicon', target_nodes="//token", \
                target_attribute='text', part_of_speech_attribute='pos', child_node_type='segment', output_attribute='pronunciation', \
                class_attribute='token_class', word_classes=['word'], probable_pause_classes=['punctuation', c.TERMINAL], \
                possible_pause_classes=['space'], \
                dictionary='some_dictionary_name', backoff_pronunciation='axr',lts_variants=1,\
                lts_ntrain=0, lts_gram_length=3, max_graphone_letters=2, max_graphone_phones=2):

        self.processor_name = processor_name
        self.target_nodes = target_nodes
        self.target_attribute = target_attribute
        self.part_of_speech_attribute = part_of_speech_attribute
        self.child_node_type = child_node_type
        self.output_attribute = output_attribute
        self.class_attribute = class_attribute
        self.word_classes = word_classes
        self.probable_pause_classes = probable_pause_classes
        self.possible_pause_classes = possible_pause_classes

        # Lexicon
        self.dictionary = dictionary  # used for training
        self.backoff_pronunciation = backoff_pronunciation # use this if lookup and LTS fail for whatever reason...
        self.lts_variants = lts_variants
        #
        ## Settings for LTS training:
        self.lts_ntrain = lts_ntrain ## train on n words -- 0 means all.
        self.lts_gram_length = lts_gram_length # 1: context independent graphones
        self.max_graphone_letters = max_graphone_letters
        self.max_graphone_phones = max_graphone_phones


        super(Lexicon, self).__init__()

        self.parallelisable = False ## poor parallelisation due to sequitur (## see: http://stackoverflow.com/questions/20727375/multiprocessing-pool-slower-than-just-using-ordinary-functions)

    def verify(self, voice_resources):
        self.voice_resources = voice_resources

        # self.target_nodes = self.config.get('target_nodes', "//token[@token_class='word']")
        # self.input_attribute = self.config.get('input_attribute', 'norm_text')
        # self.output_attribute = self.config.get('output_attribute', 'pronunciation')

        ## --- find and check required binaries ---
        self.lts_tool = os.path.join(self.voice_resources.path[c.BIN], 'g2p.py')
        tool_executable = os.access(self.lts_tool, os.X_OK)
        if not tool_executable:
            sys.exit('LTS tool %s doesn\'t exist or not executable'%(self.lts_tool ))

        ## If this component has been trained for a previous model and stored globally, this is
        ## where it will be:--
        lex_config_name = 'lexicon-%s_sequitur_LTS_ntrain%s_gramlen%s_phon%s_lett%s'%(self.dictionary, \
                    self.lts_ntrain, self.lts_gram_length, self.max_graphone_phones, self.max_graphone_letters)
        self.component_path = self.voice_resources.get_dirname(lex_config_name, c.COMPONENT, create=False)

        ## Try loading model:  # similar to acoustic model code--refactor and put this in UtteranceProcessor?
                               # Specific stuff would be the names of component of trained model.
        self.trained = True
        self.model_dir = os.path.join(self.get_location())  ## TODO = self.get_location() ?

        if not os.path.isdir(self.model_dir):
            self.trained = False

        ## verify all the parts needed are present: if the model files exists, count it as trained:
        self.lexicon_fname = os.path.join(self.model_dir, 'lexicon.txt')
        self.lts_fname = os.path.join(self.model_dir, 'lts.model')
        self.phoneset_fname = os.path.join(self.model_dir, 'phones.table')
        self.onsets_fname = os.path.join(self.model_dir, 'onsets.txt')
        self.letter_fname = os.path.join(self.model_dir, 'letter.names')

        complete = True
        for component in [self.lexicon_fname, self.lts_fname, self.phoneset_fname, \
                                                    self.onsets_fname, self.letter_fname]:
            if not os.path.isfile(component):
                complete = False
                self.trained = False

        if self.trained:
            self.load_lexicon() # populate self.entries
            self.load_onsets()  # populate self.onsets
            self.phoneset = LookupTable(self.phoneset_fname, is_phoneset=True)
            self.load_letternames()  # populate self.letternames

#         self.extra_lex_entries = self.config.get('extra_lex_entries', '')
#
        extra_lex = os.path.join(self.model_dir, 'extra_lex.txt')
        if os.path.isfile(extra_lex):
            print '    extra exists --> loading it!'
            self.load_extra_lexicon(extra_lex)

        ## Add locations for sequitur g2p to pythonpath:
        tooldir = os.path.join(self.voice_resources.path[c.BIN], '..')
        sitepackages_dir = glob.glob(tooldir + '/lib*/python*/site-packages')  ## lib vs lib64?
        assert len(sitepackages_dir) > 0
        sitepackages_dir = sitepackages_dir[0]

        ## Prepend this to relevant system calls -- using sequitur via python
        ## would obviously be a lot neater.
        self.g2p_path = 'export PYTHONPATH=%s:%s ; '%(sitepackages_dir, os.path.join(tooldir, 'g2p'))



    def load_letternames(self):
        data = readlist(self.letter_fname)
        self.letternames = {}
        for line in data:
            line = line.strip(' \n')
            letter, pron = re.split('\s+', line, maxsplit=1)
            self.letternames[letter] = pron


    def convert_lexicon(self, files, format='festival'):

        print '     convert lexicon...'
        entries = {}
        seen_tags = {}  ## for reporting
        if format=='festival':
            for line in fileinput.input(files, openhook=fileinput.hook_encoded("utf8")):
                line = line.strip(' \n')
                if line.startswith(';') or line == '' or line == 'MNCL':
                    continue ## ignore Scheme comment line and empty lines

                (headword, tags, pronun) = self.read_festival_lexentry(line)

                if headword not in entries:
                    entries[headword] = []
                entries[headword].append([tags, pronun])
                seen_tags[tags] = ''
        else:
            sys.exit('Unknown lexicon format: %s'%(format))

        print 'Tags in lexicon: '
        print seen_tags.keys()

        f = codecs.open(self.lexicon_fname, 'w', encoding='utf8')
        for head_word in sorted(entries.keys()):
            for (tag, pron) in entries[head_word]:
                f.write('%s\t%s\t%s\n'%(head_word, tag, pron))
        f.close()

        self.entries = entries



    def load_lexicon(self):

        assert os.path.isfile(self.lexicon_fname)
        items = readlist(self.lexicon_fname)
        self.entries = {}
        for item in items:
            (head,tag,pron) = item.split('\t')
            tag = tag.split(',')
            if head not in self.entries:
                self.entries[head] = []
            self.entries[head].append((tag, pron))


    def load_extra_lexicon(self, extra_lex):

        assert os.path.isfile(extra_lex), 'not file: ' + extra_lex
        items = readlist(extra_lex)
        for item in items:
            if item.startswith('#') or re.match('\A\s*\Z', item):
                continue
            (head,tag,pron) = item.split('\t')
            tag = tag.split(',')
            if '|' not in pron:
                pron = self.syllabify(pron)
            if head not in self.entries:
                self.entries[head] = []
            self.entries[head].append((tag, pron))

    def load_onsets(self):
        onsets = readlist(self.onsets_fname)
        onsets = [tuple(line.split(' ')) for line in onsets]
        self.onsets = dict(zip(onsets, onsets))

    def process_utterance(self, utt):
        for node in utt.xpath(self.target_nodes):
            assert node.has_attribute(self.class_attribute)
            assert node.has_attribute(self.target_attribute)

            current_class = node.attrib[self.class_attribute]

            if current_class in self.word_classes:
                word = node.attrib[self.target_attribute]
                pos = node.attrib.get(self.part_of_speech_attribute, None) # default to None
                (pronunciation, method) = self.get_phonetic_segments(word, part_of_speech=pos)
                node.set('phones_from', method)
                NodeProcessors.add_syllable_structure(node, pronunciation, syllable_delimiter='|', syllable_tag='syllable', \
                                phone_tag='segment', pronunciation_attribute='pronunciation', stress_attribute='stress')
            elif current_class in self.probable_pause_classes:
                pronunciation = c.PROB_PAUSE # [c.PROB_PAUSE]
                child = Element('segment')
                child.set('pronunciation', pronunciation)
                node.add_child(child)
            elif current_class in self.possible_pause_classes:
                pronunciation = c.POSS_PAUSE # [c.POSS_PAUSE]
                child = Element('segment')
                child.set('pronunciation', pronunciation)
                node.add_child(child)
            else:
                sys.exit('Class "%s" not in any of word_classes, probable_pause_classes, possible_pause_classes')


    def get_phonetic_segments(self, word, part_of_speech=None):

        word = word.lower()
        word = word.strip("'\" ;,")

        initialism_patt = '\A([a-z]\.)+\Z'
        if re.match(initialism_patt, word):
            pronunciation = self.get_initialism(word)
            method = 'letter_prons'
        elif word in self.entries:
            method = 'lex'
            if len(self.entries[word]) == 1:  ## unique, no disambig necessary
                tag, pronunciation = self.entries[word][0]  ## for now take first
            else:
                ## filter ambiguous pronunciations by first part of tag (POS):
                ## if there *is* no POS, take first in list:
                if not part_of_speech:
                    print 'WARNING: no pos tag to disambiguate pronunciation of "%s" -- take first entry in lexicon'%(word)
                    tag, pronunciation = self.entries[word][0] #take first
                else:
                    wordpos = part_of_speech.lower() # node.attrib['pos']
                    filtered = [(tag, pron) for (tag,pron) in self.entries[word] \
                                                                 if tag[0] == wordpos]
                    if len(filtered) == 0:
                        tag, pronunciation = self.entries[word][0] #if no POS matches, take first anyway
                    else:
                        tag, pronunciation = filtered[0] ## take first matching filtered dictionary entry

        else:
            if self.lts_variants == 1:
                pronunciation = self.get_oov_pronunciation(word)
            else:
                pronunciation = self.get_nbest_oov_pronunciations(word, self.lts_variants)
            if pronunciation != None:
                pronunciation = self.syllabify(pronunciation)
                method = 'lts'
            else:
                pronunciation = self.backoff_pronunciation
                method = 'default'

        return (pronunciation, method)

    def count_onsets_and_codas(self):
        print '     count onsets and codas...'
        onsets = {}
        codas = {}
        for (entry, prons) in self.entries.items():

            for (tag, pron) in prons:

                pron = re.sub('\d','',pron) ## remove stress marks so we can look up vowels
                sylls = pron.split(' | ')
                for syll in sylls:
                    phones = syll.split(' ')
                    vowel_index = [i for (i,phone) in enumerate(phones) \
                            if self.phoneset.lookup(phone, field='vowel_cons')=='vowel']
                    if len(vowel_index) > 1:
                        print 'Multiple vowels found in syll %s in an entry for %s'%(syll, entry)
                        continue
                    if len(vowel_index) < 1:
                        print 'No vowels found in syll %s in an entry for %s'%(syll, entry)
                        continue
                    i = vowel_index[0]
                    onset = tuple(phones[:i])
                    coda = tuple(phones[i+1:])
                    if onset not in onsets:
                        onsets[onset] = 0
                    onsets[onset] += 1
                    if coda not in codas:
                        codas[coda] = 0
                    codas[coda] += 1
        self.onsets = onsets
        self.codas = codas


    def get_initialism(self, form):
        letters = form.lower().strip(' .').split('.')
        pronunciation = []
        for letter in letters:
            pronunciation.append(self.letternames[letter] )
        pronunciation = ' | '.join(pronunciation)
        return pronunciation

    def syllabify(self, phonestring):
        '''
        Syllabify with maximum legal (=observed) onset.
        Take "e g z a1 m"
        return "e g | z a1 m"
        '''
        assert '|' not in phonestring
        plain = re.sub('\d','',phonestring) ## remove stress marks so we can look up vowels
        plainphones = plain.split(' ')
        phones = phonestring.split(' ')
        vowel_indexes = [i for (i,phone) in enumerate(plainphones) \
                            if self.phoneset.lookup(phone, field='vowel_cons')=='vowel']

        if len(vowel_indexes) > 0:  ## else add nothing to phones and return that.

            start = vowel_indexes[0]+1

            for end in vowel_indexes[1:]:

                if start == end:  ## juncture between 2 vowels as in 'buyer'
                    best_split = start
                else:
                    split_scores = []
                    for split in range(start, end):
                        first_part = tuple(plainphones[start:split])
                        second_part = tuple(plainphones[split:end])

                        ## Take maximum legal onset:
                        if second_part in self.onsets:
                            score = len(second_part)
                        else:
                            score = -1

                        ## Older version: score is sum of onset and coda freqs:
                        # score = self.codas.get(first_part, 0) + self.onsets.get(second_part, 0)

                        split_scores.append((score, split))
                    split_scores.sort()

                    best_split = split_scores[-1][1]
                phones[best_split] = '| ' + phones[best_split]

                start = end + 1

        return ' '.join(phones)


    def do_training(self, corpus, text_corpus):

        dict_location = os.path.join(self.voice_resources.path[c.LANG], 'labelled_corpora', self.dictionary)

        ## phoneset
        phonetable_files = glob.glob(os.path.join(dict_location, '*.table'))
        if phonetable_files == []:
            sys.exit('Cannot find any phone table files at %s'%(os.path.join(dict_location, '*.table')))
        phonetable_file = phonetable_files[0] ## take first
        shutil.copy(phonetable_file, self.phoneset_fname)
        ## load phoneset now for converting lexicon:
        self.phoneset = LookupTable(self.phoneset_fname, is_phoneset=True)

        ## letter pronunciations
        letter_file = os.path.join(dict_location, 'letter.names')
        assert os.path.isfile(letter_file)
        shutil.copy(letter_file, self.letter_fname)
        self.load_letternames()  # populate self.letternames

        ## lexicon
        dict_files = [f for f in glob.glob(os.path.join(dict_location, '*')) \
                    if f.endswith('.out')]

                    ## exclude cmudict extensions:  ## or f.endswith('.scm') ]
                    ## glob doesn't support {} for .{out,scm}

        assert dict_files != [],'No lexicon files found at %s'%(dict_location)
        self.convert_lexicon(dict_files)

        ## onsets
        self.count_onsets_and_codas()
        onset_strings = [' '.join(onset) for onset in self.onsets.keys()]
        writelist(onset_strings, self.onsets_fname)

        ## G2P
        train_file = os.path.join(self.get_training_dir(), 'train_data.txt')
        self.make_sequitur_train_data(train_file)
        self.train_sequitur_g2p(train_file)

        ## save it also globally for posterity:-
        if os.path.isdir(self.component_path):
            shutil.rmtree(self.component_path)
        shutil.copytree(self.model_dir, self.component_path)


    def make_sequitur_train_data(self, train_file):
        '''Write entries to file for training g2p, append stress to vowel symbols'''
        lines = []
        for (head, entry) in self.entries.items():
            for (tags, pronun) in entry:
                train_phones = pronun.replace(' | ', ' ').split(' ') ## list of phones w/o syllab
                line = ' '.join([head] + train_phones) + '\n'
                lines.append(line)

        if self.lts_ntrain > 0:
            lines = lines[:self.lts_ntrain]

        f = codecs.open(train_file, 'w', encoding='utf8')
        for line in lines:
            f.write(line)
        f.close()
        print 'Wrote %s'%(train_file)

    def train_sequitur_g2p(self, train_file):
        '''Currently use system call -- TODO: keep this all in python?'''

        lts_model = self.lts_fname
        print 'Training LTS with sequitur...'
        ## train unigram model:
        n = 1
        comm = '%s %s --train %s -s 1,%s,1,%s --devel 5%% --encoding utf8 --write-model %s_%s > %s.log'%(self.g2p_path, \
                            self.lts_tool, train_file, self.max_graphone_letters, \
                            self.max_graphone_phones, lts_model, n, lts_model)
        print comm
        os.system(comm)
        n += 1
        while n <= self.lts_gram_length:
            comm = '%s %s --model %s_%s --ramp-up --train %s --devel 5%% --encoding utf8 --write-model %s_%s >> %s.log'%(
                          self.g2p_path, self.lts_tool, lts_model, n-1, train_file, lts_model, n, lts_model)
            print comm
            os.system(comm)
            n += 1
        shutil.copy('%s_%s'%(lts_model, self.lts_gram_length), lts_model)
        self.lts_model = lts_model


    def get_nbest_oov_pronunciations(self, word, nbest):
        '''return n best, sep by sil'''

        word = word.lower()
        word = self.strip_space_and_punc(word)   ## strip apostrophe and also other punc that gets into KY's words (Poirot'',)
        #escaped_word = "'" + word.replace("'", "'\\''") + "'" ## escape ' for shell command
        #escaped_word = "'" + word.replace("'", "") + "'"  ## strip apostrophe
        escaped_word = "'" + word + "'"


        comm = '%s echo %s | %s  --model %s  --variants-number %s --encoding utf8 --apply -'%(self.g2p_path,  \
                                                    escaped_word, self.lts_tool, self.lts_fname, nbest)

        pronun = subprocess.check_output(comm, shell=True, stderr=subprocess.STDOUT)
        if 'failed to convert' in pronun:
            print comm
            print 'WARNING: couldnt run LTS for %s'%(word)


        ## remove the 'stack usage' output line -- its position varies:
        pronun = unicodedata.normalize('NFKD', pronun.decode('utf-8'))
                            ## ^----- 2015-11-4: moved this line back from c.440

        pronun = pronun.strip(' \n').split('\n')
        print pronun

        ## deal with this, but TODO: work out long-term solution --
        assert len(pronun) >= 2,str(pronun)     ## ==   -->   >=     to handle extra warnings
        if type(word) == str:
            word = word.decode('utf-8')
        normalised_word = unicodedata.normalize('NFKD', word)
        real_pronuns = []
        for line in pronun:
            if 'stack usage' not in line and normalised_word in line:   ## word in line   added to reject warnings
                real_pronuns.append(line)

        word = unicodedata.normalize('NFKD', word)
        clean_pronuns = []
        for line in  real_pronuns:
            (outword, number, score, pronun) = re.split('\s+', line, maxsplit=3)
            outword = unicodedata.normalize('NFKD', outword.decode('utf-8'))
            if type(word) == str:
                word = word.decode('utf-8')
            assert outword == word,'don\'t match: %s and %s'%(outword, word)
                        ## sequitur seems to return decomposed forms


            clean_pronuns.append(pronun)
        clean_pronuns = ' sil '.join(clean_pronuns)
        return clean_pronuns



    def get_oov_pronunciation(self, word):
        '''Currently use system call -- TODO: keep this all in python?'''

        word = word.lower()

        word = self.strip_space_and_punc(word)   ## strip apostrophe and also other punc that gets into KY's words (Poirot'',)
        #escaped_word = "'" + word.replace("'", "'\\''") + "'" ## escape ' for shell command
        #escaped_word = "'" + word.replace("'", "") + "'"  ## strip apostrophe
        escaped_word = "'" + word + "'"

        comm = '%s echo %s | %s  --model %s --encoding utf8 --apply -'%(self.g2p_path,  \
                                                    escaped_word, self.lts_tool, self.lts_fname)

        pronun = subprocess.check_output(comm.encode('utf8'), shell=True, stderr=subprocess.STDOUT)
        if 'failed to convert' in pronun:
            print comm
            print 'WARNING: couldnt run LTS for %s'%(word)
            return None

        ## remove the 'stack usage' output line -- its position varies:
        pronun = unicodedata.normalize('NFKD', pronun.decode('utf-8'))
                            ## ^----- 2015-11-4: moved this line back from c.440

        pronun = pronun.strip(' \n').split('\n')

        ## form of returned pronuncations is different when warnings are given:

        ## ]'stack usage:  415', 'androcles\ta1 n d r @0 k @0 lw z'] ... becomes:

        ## ['/afs/inf.ed.ac.uk/group/cstr/projects/blizzard_entries/blizzard2015/tool/Ossian//tools/bin/g2p.py:37: DeprecationWarning: the sets module is deprecated', '  import math, sets, sys', 'stack usage:  415', 'androcles\ta1 n d r @0 k @0 lw z']

        ## deal with this, but TODO: work out long-term solution --
        assert len(pronun) >= 2,str(pronun)     ## ==   -->   >=     to handle extra warnings
        if type(word) == str:
            word = word.decode('utf-8')
        normalised_word = unicodedata.normalize('NFKD', word)
        for line in pronun:
            if 'stack usage' not in line and normalised_word in line:   ## word in line   added to reject warnings
                pronun = line

        (outword, pronun) = re.split('\s+', pronun, maxsplit=1)
        outword = unicodedata.normalize('NFKD', outword)
#        word = unicodedata.normalize('NFKD', word.decode('utf-8'))
        if type(word) == str:
            word = word.decode('utf-8')
        word = unicodedata.normalize('NFKD', word)


        assert outword == word,'don\'t match: %s and %s'%(outword, word)
                    ## sequitur seems to return decomposed forms
        return pronun






    def strip_space_and_punc(self, token):
        '''Use regex to match unicode properties to strip punctuation and space.'''
        space_or_punc = '[\p{Z}||\p{C}||\p{P}||\p{S}]'
        return regex.sub(space_or_punc, '', token)


    def read_festival_lexentry(self, string):

        ## TODO: handle simple pronunciations better

        string = re.sub('(\A\s*\(\s*|\s*\)\s*\Z)', '', string) ## strip outer brackets

        entry = re.split('(\A"[^"]+\")', string) ## brackets to return chunks as well as splits

        entry = [chunk for chunk in entry if chunk != ''] ## filter intial ''
        assert len(entry) == 2,entry
        word, pronun = entry

        word = word.strip('"')
        pronun = pronun.strip(' ')
        ## tag might be a string or bracketed sequence:

        if pronun[0] == '(':
            pronun = re.split('\)\s*\(', pronun,maxsplit=1) # re.split('(\([^)]+\))',pronun)
        else:
            pronun = re.split('\s+',pronun,maxsplit=1)
        pronun = [chunk for chunk in pronun if chunk != '']

        assert len(pronun) == 2,pronun
        tag, all_syllables = pronun

        tag = tag.strip('() ')

        pronun = []

        ## is it a simple pronunciation (later addition, no syll and stress appended to vowel)? -- :
        if all_syllables.count(')') == 1 and all_syllables.count('(') == 1:
            phones = all_syllables.strip('()')
            stress = '1' ## dummy
            pronun.append(phones)

        else:

            syllables = re.split('\)\s*\(', all_syllables)
            syllables = [syll.strip(' ()') for syll in syllables]

            for syll in syllables:
                phones, stress = re.split('\)\s*', syll)
                phones = phones.split(' ')
                stressed_phones = []
                for phone in phones:
                    if self.phoneset.lookup(phone, field='vowel_cons') == 'vowel':
                        phone = phone + stress
                    stressed_phones.append(phone)
                pronun.append(' '.join(stressed_phones))
        pronun = ' | '.join(pronun)

        ## parse tag into either [POS] or [POS, disambig] or [POS, disambig, variant_tag]
        if ' ' in tag:
            tag = tag.split(' ')
            assert len(tag) == 2 # in [2,3]
        else:
            tag = [tag]
        tag = ','.join(tag)  ## tuple(tag)

        return (word, tag, pronun)


class NaiveIcelandicG2P(Lexicon):

    '''
    rough sketch of processor for Blizzard 2015 schwa-deletion dicts,
    they and LTS are already trained.

    Replaced parts with much simpler stuff.
    Use something like Lexicon's get_oov_pronunciation but handle P2P
    lexicon rather than G2P.

    Omit actual lexicon part as the lexicon is created with G2P anyway.
    '''

    def __init__(self, processor_name='lexicon', target_nodes="//token", \
                target_attribute='text', part_of_speech_attribute='pos', \
                child_node_type='segment', output_attribute='pronunciation', \
                class_attribute='token_class', word_classes=['word'],
                probable_pause_classes=['punctuation', c.TERMINAL], \
                possible_pause_classes=['space'], dictionary='ice_g2p', \
                backoff_pronunciation='a'):

        super(NaiveIcelandicG2P, self).__init__()

        self.processor_name = processor_name
        self.target_nodes = target_nodes
        self.target_attribute = target_attribute
        self.output_attribute = output_attribute
        self.dictionary=dictionary
        self.backoff_pronunciation = backoff_pronunciation

    def verify(self, voice_resources):
        self.voice_resources = voice_resources
        self.phone_delimiter = ' '
        self.lts_tool = os.path.join(self.voice_resources.path[c.BIN], 'g2p.py')

        tool_executable = os.access(self.lts_tool, os.X_OK)
        if not tool_executable:
            sys.exit('LTS tool %s doesn\'t exist or not executable'%(self.lts_tool ))

        # Marked as trained if Sequitur model exists
        self.model_dir = os.path.join(self.get_location())
        self.trained = True
        if not os.path.isdir(self.model_dir):
            self.trained = False

        self.lexicon_fname = os.path.join(self.model_dir, 'lexicon.txt')
        self.lts_fname = os.path.join(self.model_dir, 'lts.model')

        complete = True
        for component in [self.lts_fname]:
            if not os.path.isfile(component):
                complete = False
                self.trained = False

        if not self.trained:
            self.do_training(None, None)

        # populate self
        self.load_lexicon()

        ## Add locations for sequitur G2P to pythonpath:
        tooldir = os.path.join(self.voice_resources.path[c.BIN], '..')
        sitepackages_dir = glob.glob('/usr/local/lib/python2.7/site-packages')  ## lib vs lib64?
        assert len(sitepackages_dir) > 0
        sitepackages_dir = sitepackages_dir[0]

        # Prepend this to relevant system calls,
        # using sequitur via python would obviously be a lot neater.
        self.g2p_path = 'export PYTHONPATH=%s:%s ; '%(sitepackages_dir, os.path.join(tooldir, 'g2p'))

    def load_lexicon(self):
        ## assume one entry per head word -- take first if multiple
        assert os.path.isfile(self.lexicon_fname)
        items = readlist(self.lexicon_fname)
        self.entries = {}
        self.phone_inventory = []
        for item in items:
            (head,pron) = item.split('\t')
            if head not in self.entries:
                self.entries[head] = pron
                phones = pron.split(' ')
                for phone in phones:
                    if phone not in self.phone_inventory:
                        self.phone_inventory.append(phone)

    def convert_lexicon(self, files):
        entries = {}
        seen_tags = {}  ## for reporting
        for line in fileinput.input(files, openhook=fileinput.hook_encoded("utf8")):
            line = line.strip(' \n')
            (headword, pronun) = line.split('\t')
            phones = [ipa2sampa[x.encode('utf8')] if x.encode('utf8') in ipa2sampa.keys() else x for x in pronun.split(' ')]
            entries[headword] = ' '.join(phones)

        if "#0" not in entries.keys():
            # Add silence phone if not already present
            entries["#0"] = "sil"
        f = codecs.open(self.lexicon_fname, 'w', encoding='utf8')
        for head_word, pron in sorted(entries.items(), key=lambda x: x[0]):
            f.write('%s\t%s\n'%(head_word, pron))
        f.close()
        self.entries = entries

    def process_utterance(self, utt):
        for node in utt.xpath(self.target_nodes):
            assert node.has_attribute(self.target_attribute)
            word = node.get(self.target_attribute)
            word = [safetext(lett.lower()) for lett in word]
            current_class = node.attrib[self.class_attribute]
            phones_from = None
            if current_class in self.word_classes:
                word = node.attrib[self.target_attribute]
                if word.lower() in self.entries:
                    phones_from = 'lex'
                    pronunciation = self.entries[word.lower()]
                else:
                    pronunciation = self.get_oov_pronunciation(word)
                    phones_from = 'lts'
                    if pronunciation == None:
                        pronunciation = self.backoff_pronunciation
                        phones_from = 'default'
            elif current_class in self.probable_pause_classes:
                pronunciation = c.PROB_PAUSE # [c.PROB_PAUSE]
                child = Element('segment')
                child.set('pronunciation', pronunciation)
                node.add_child(child)
                continue
            elif current_class in self.possible_pause_classes:
                pronunciation = c.POSS_PAUSE # [c.POSS_PAUSE]
                child = Element('segment')
                child.set('pronunciation', pronunciation)
                node.add_child(child)
                continue
            if phones_from == 'lts':
                phones = [ipa2sampa[x.encode('utf8')] if x.encode('utf8') in ipa2sampa.keys() else x for x in pronunciation.split(' ')]
            else:
                phones = [x for x in pronunciation.split(' ')]
            for phone in phones:
                child = Element('segment')
                child.set('pronunciation', phone)
                if phones_from:
                    child.set('phones_from', phones_from)
                node.add_child(child)

    def do_training(self, corpus, text_corpus):
        dict_location = os.path.join(self.voice_resources.path[c.LANG], 'labelled_corpora', self.dictionary)
        print dict_location
        assert os.path.isfile(os.path.join(dict_location, "lexicon.txt"))
        self.convert_lexicon(os.path.join(dict_location, "lexicon.txt"))
        assert os.path.isfile(os.path.join(dict_location, "lts.model"))
        shutil.copy(os.path.join(dict_location, "lts.model"), self.lts_fname)

    def get_oov_pronunciation(self, word):

        ##input to P2P apply is word + pron:
        word = word.lower() #+ ' ' + ' '.join(letters)
        escaped_input = "'" + word + "'"
        comm = '%s echo %s | %s  --model %s --encoding utf8 --apply -'%(self.g2p_path,  \
                                                    escaped_input, self.lts_tool, self.lts_fname)
        try:
            pronun = subprocess.check_output(comm, shell=True, stderr=subprocess.STDOUT)
            if 'failed to convert' in pronun:
                print comm
                print 'WARNING: couldnt run LTS for %s'%(word)
                return None
        except Exception as e:
            print(e)
            print("Exception!!")
            return None

        ## remove the 'stack usage' output line -- its position varies:
        pronun = pronun.strip(' \n').split('\n')
        assert len(pronun) >= 2,str(pronun)
        for line in pronun:
            line = line.decode('utf8')
            if 'stack usage' not in line and word in line:
                pronun = line
        (outword, pronun) = re.split('\s+', pronun, maxsplit=1)
        outword = unicodedata.normalize('NFKD', outword)
        if type(word) == str:
            word = word.decode('utf-8')
        word = unicodedata.normalize('NFKD', word)

        assert outword == word,'don\'t match: %s and %s'%(outword, word)
        return pronun

if __name__=="__main__":
    print get_spans_on_one_level('("checkpoints" nil (((ch eh k) 1) ((p oy n t s) 1)))')
