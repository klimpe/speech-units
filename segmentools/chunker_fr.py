# -*- coding: utf-8 -*-
# Name:    chunker v2.2
# Author:  Klim Peshkov
# Date:    26.09.2014
# Modifications:
#   26 sept 2014: lexical filter for
#   25 july 2014: add disfluency detection

import copy
import logging
import re
import pickle
import groupsegm
import annotationdata.aio as aio
from annotationdata.transcription import Transcription
from annotationdata.tier import Tier
from annotationdata.annotation import Annotation
from annotationdata.ptime.interval import TimeInterval
from annotationdata.label.label import Label
import tierutil


class Chunker:

    def __init__(self, token_tier, synt_tier):
        '''
        In:
          token_tier (annotationdata.tier.Tier)
          synt_tier (annotationdata.tier.Tier)
        Errors:
          TypeError
        '''
        logging.basicConfig(level=logging.DEBUG)
        if not (isinstance(token_tier, Tier) and isinstance(synt_tier, Tier)):
            raise TypeError('Expecting two Tiers')
        rsegm = groupsegm.GroupSegm([token_tier, synt_tier], 0)
        self.token_tier = copy.deepcopy(rsegm.reference)
        self.raw_synt_tier = copy.deepcopy(rsegm.data[1])
        self.synt_tier = None
        self.simple_synt_tier = None # simplified version of self.synt_tier
        self.chunk_tier = None
        self.synt_cat_tier = None # Categories: ex. VC, NC, PC
        self.disf_cat_tier = None # Categories: ex. hyper, atro, BC
        self.disf_bool_tier = None # Categories: 0 and 1 (disfluent or not)

        # PAUSE_THRESHOLD: pauses which last longer than this threshold
        # will be concidered as true silences,
        # while shorter pause intervals will be glued to adjacent intervals
        self.PAUSE_THRESHOLD = 0.2 # seconds
        self._prepare_token_tier()
        self._prepare_synt_tier() # creates self.synt_tier
                                  # by modifying original POS tier
        self._create_simple_synt_tier() #creates self.simple_synt_tier

        # initialize dictionnary for chunking rules statistics
        self.skeys = [
            'Cc .','Cs .', 'D .', 'I .','Pp .', 'Pr .', 'Px .',
            'Rpd .', 'Rpn .', 'S .', 'Va .', 'Ve .',
            'A N', 'Nc Np', 'Nk Nc', 'Np Np', 'Pd Cs', 'Pd P[^t]',
            'Pd Pr', 'Pd Rpn', 'Pd V', 'V Rgd', 'V Rgn', 'V V',
            'Rgc P', 'Rgp A', 'Rgp Rgp', 'Rgp Vmps', 'Rgn A', 'empty string',
            'ouais non', 'donc', 'cut FP', 'glue final I', 'Rgp2I']
        # 'V Pd',
        self.stats = dict()
        for x in self.skeys:
            self.stats[x] = 0

        # initialize dictionnary for statistics on categories
        self.skeys_category = ['DisfError', 'PC', 'NC', 'VC',
                               'PVC', 'AC', 'RC', 'IC']
        self.stats_category = dict()
        for x in self.skeys_category:
            self.stats_category[x] = 0


    def launch_chunking(self):
        '''
        Obtain segmentation into chunks

        Out: annotationdata.tier.Tier, creates self.chunk_tier
        '''
        chunk_tier = Tier('Chunk-spattern')
        # List of morphosynt. intervals which consitute the chunk.
        # form: [(tag, i)], where 'i' is index in synt_tier
        chunk = [(self.synt_tier[0], 0)]
        i = 0
        while i < len(self.synt_tier)-1:
            cur_tag = self.synt_tier[i]
            next_tag = self.synt_tier[i+1]
            together = self._belong_together(cur_tag.GetLabel().GetValue(),
                                             next_tag.GetLabel().GetValue())
            #print cur_tag.GetLabel().GetValue(), next_tag.GetLabel().GetValue(), together
            if together:
                chunk.append((next_tag, i+1))
            else:
                if len(chunk) == 1 and chunk[0][0].GetLabel().GetValue() == '#':
                    chunk_tier.Add(chunk[0][0])
                elif chunk:
                    # Add chunk
                    self._add_chunk(chunk, chunk_tier)
                chunk = [(next_tag, i+1)]
            i += 1

        chunk_tier = self._glue_through_nonsynt(chunk_tier) # 2nd pass

        self.chunk_tier = chunk_tier
        self._apply_postchunking_rules()
        self._create_synt_category_tier()
        self._create_disf_tiers()
        return chunk_tier


    def _add_chunk(self, chunk, chunk_tier):
        '''
        Add chunk to chunk_tier

        In:
          chunk (list) - list of annotations, representing POS intervals
              which consitute the chunk,
          chunk_tier (Tier) - the chunk will be added here

        Out:
          Tier - modified chunk_tier
        '''
        if len(chunk)>0:
            text = ' '.join([self.simple_synt_tier[x[1]].GetLabel().GetValue()
                             for x in chunk])
            text = text.replace('<LI>', '')
            text = text.replace('<FP>', 'I')
            text = text.replace('  ',' ')
            chunk_annot = tierutil.create_annotation(
                chunk[0][0].GetLocation().GetBegin(),
                end=chunk[-1][0].GetLocation().GetEnd(),
                label=text)
            chunk_tier.Add(chunk_annot)
            #print 'Chunk added:', chunk_annot
        return chunk_tier


    def _glue_through_nonsynt(self, chunk_tier):
        '''
        In the situation, when the last tag of one chunk
        can be glued with the first non-special tag of the next
        a non-syntactic tag can form a single chunk, the
        three intervals are merged into one
        '''
        new_chunk_tier = Tier(chunk_tier.GetName())
        glued_annot = None
        i = 0
        while i < len(chunk_tier)-1:
            cur_tags = chunk_tier[i].GetLabel().GetValue().split()
            next_tags = chunk_tier[i+1].GetLabel().GetValue().split()
            if len(next_tags) == 0:
                next_tags.append('')
            if self._is_special(next_tags[0]):
                first_synt = self._first_synt_index(next_tags)
                if first_synt is not None:
                    if self._belong_together_pos(cur_tags[-1],
                                                 next_tags[first_synt]):
                        text = chunk_tier[i].GetLabel().GetValue() + ' ' + chunk_tier[i+1].GetLabel().GetValue()
                        glued_annot = tierutil.create_annotation(chunk_tier[i].GetLocation().GetBegin(),
                                                                 end=chunk_tier[i+1].GetLocation().GetEnd(),
                                                                 label=text)
                        new_chunk_tier.Add(glued_annot)
                        print 'Glued:', glued_annot
                        glued_annot = None
                        i += 2
            if glued_annot is None:
                new_chunk_tier.Add(chunk_tier[i])
                i += 1
        return new_chunk_tier


    def _first_synt_index(self, tags):
        '''
        In: tags (list) list of strings
        Out: (int or None) index of the first normal pos-tag
        '''
        for index, element in enumerate(tags):
            if element not in ['<FP>','<WF>','<LI>','#','+', '']:
                return index
        return None


    def _prepare_token_tier(self):
        for token in self.token_tier:
            label = token.GetLabel()
            dur = token.GetLocation().GetDuration()
            if label.GetValue().strip() == '':
                if dur < self.PAUSE_THRESHOLD:
                    label.SetValue('+')
                else:
                    label.SetValue('#')


    def _prepare_synt_tier(self):
        '''
        Creates a modified copy of the syntactic tier:
        1. All empty intervals in the original syntactic tier are
           replaced by the tags for silent pauses, filled pauses,
           word fragments and silent pauses, using information
           from self.token_tier.
        (Obsolete, but was used for disfluency detection:
          2. Tag 'Rgp' is replaced by 'I')
         '''
        synt_tier = Tier('Chunk-Synt')
        for pos in self.raw_synt_tier:
            pos_label = pos.GetLabel()
            pos_loc = pos.GetLocation()
            # Empty interval of the syntactic tier
            if pos_label.GetValue().strip() == '':
                tokens = self.token_tier.Find(pos_loc.GetBegin(),
                                              pos_loc.GetEnd())
                for token in tokens:
                    token = copy.deepcopy(token)
                    tok_label = token.GetLabel().GetValue()
                    tag = self._special_token_to_tag(tok_label)
                    pos_label.SetValue(tag)
                    synt_tier.Add(pos)
            else:
                # Rgp -> I
                # pos = self._apply_Rgp2I_rule(pos)

                synt_tier.Add(pos)
        synt_tier = self._remove_FP_from_I(synt_tier)
        synt_tier = self._merge_pauses(synt_tier)
        self._relabel_pauses(synt_tier)
        self._apply_prechunking_rules()
        self.synt_tier = synt_tier


    def _apply_Rgp2I_rule(self, pos):
        '''
        In: pos (Annotation)
        '''
        # lex = ['ouais', 'alors', 'voilà', 'en fait',
        #        'donc', 'ok', 'okey', 'o.k.']

        # if pos.GetLabel().GetValue() == 'Rgp':
        #     pos.GetLabel().GetValue() = 'I'

        label = pos.GetLabel()
        start = pos.GetLocation().GetBegin()
        if label.GetValue().lower()=='Rgp':
            if self.token_tier.Lindex(start)!=-1:
                self.stats['Rgp2I']+=1
                label.SetValue('I')
        return pos


    def _remove_FP_from_I(self, synt_tier):
        '''
        Lexical rule:
        In self.synt_tier, remove filled pauses marked with I
        '''
        new_synt_tier = Tier()
        for tag in synt_tier:
            taglab = tag.GetLabel()
            tagloc = tag.GetLocation()
            if taglab.GetValue().strip() == 'I':
                for token in self.token_tier:
                    tokloc = token.GetLocation()
                    toklab = token.GetLabel()
                    # tokens, included in tag
                    if (tokloc.GetBegin() >= tagloc.GetBegin() and
                        tokloc.GetEnd() <= tagloc.GetEnd()):
                        if re.match('(hm|euh|heu|mhhm|hum|mhm|pff)\b',
                                    toklab.GetValue()):
                            logging.info('skipping', tag, token)
                        else:
                            new_synt_tier.Add(tag)
            else:
                new_synt_tier.Add(tag)
        return new_synt_tier


    def _apply_prechunking_rules(self):
        '''
        Apply lexical rules to synt_tier
        '''
        # In 'ouais non' non -> I
        i = 0
        token_tier = self.token_tier
        while i < len(token_tier)-1:
            if token_tier[i]=='ouais' and token_tier[i+1]=='non':
                synt_annot = self.synt_tier.Find(token_tier[i+1].GetLocation().GetBegin(),
                                                 token_tier[i+1].GetLocation().GetEnd())[0]
                synt_annot.GetLabel().SetValue('I')
                self.stats['ouais non'] += 1
            i += 1



    def _apply_postchunking_rules(self):
        '''
        Apply lexical rules to chunk_tier
        '''
        self._apply_donc_rule()
        self._apply_cut_FP_rule()
        self._apply_glue_final_I()


    def _apply_donc_rule(self):
        '''
        In chunk_tier: '^donc' followed by I+ -> I
        '''
        donc_list = [x for x in self.token_tier if x.GetLabel().GetValue() == 'donc']
        for donc in donc_list:
            chunk_index = self.chunk_tier.Lindex(donc.GetLocation().GetBegin())
            if chunk_index != -1:
                chunk = self.chunk_tier[chunk_index]
                pattern = chunk.GetLabel().GetValue().split()
                if len(pattern) > 1:
                    if pattern[1] == 'I':
                        new_pattern = ' '.join(['I']+pattern)
                        self.stats['donc'] += 1


    def _apply_cut_FP_rule(self):
        '''
        Cut before filled pauses marked as I

        Apply rule: ^[IC]+ euh
        couper apres I, avant euh
        '''
        chunk_tier = self.chunk_tier
        token_tier = self.token_tier
        filled_pauses = ['hm','euh','heu','mhhm','hum','mhm','pff']
        for chunk in chunk_tier:
            tags = chunk.GetLabel().GetValue().split()
            if '<FP>' in tags and list(set(tags)) == ['I', 'C', '<FP>']:
                chunk_start = chunk.GetLocation().GetBegin().GetValue()
                chunk_end = chunk.GetLocation().GetEnd().GetValue()
                tokens = tierutil.units_of_interval(token_tier,
                                                   chunk_start,
                                                   chunk_end)
                t = 0
                while tokens[t].GetLabel().GetValue() not in filled_pauses:
                    t += 1
                new_boundary = tokens[t].EndValue
                left_text = ' '.join(tags[t+1:])
                right_text = ' '.join(tags[:t+1])
                tierutil.boundary_add(chunk_tier, new_boundary,
                                      left_text, right_text)
                self.stats['cut FP'] += 1


    def _apply_glue_final_I(self):
        '''
        [X]  [I+]  [#] -> [X I+] [#]
        '''
        chunk_tier = self.chunk_tier
        i = 1
        while i < len(chunk_tier)-1:
            if set(chunk_tier[i].GetLabel().GetValue().split()) == {'I'}:
                if chunk_tier[i+1].GetLabel().GetValue()=='#':
                    if self._first_synt_index(chunk_tier[i-1].GetLabel().GetValue().split()):
                        glued_interval = TimeInterval(chunk_tier[i-1].GetLocation().GetBegin(),
                                                      chunk_tier[i].GetLocation().GetEnd())
                        text = ' '.join([chunk_tier[i-1].GetLabel().GetValue(),
                                         chunk_tier[i].GetLabel().GetValue()])
                        glued_annot = Annotation(glued_interval, Label(text))
                        self.stats['glue final I'] += 1
            i += 1


    def _belong_together(self, cur_tag, next_tag):
        '''
        Says whether current tag must be in the same
        chunk as the previous.

        In: cur_tag (str)
            next_tag (str)

        - Long pause
        - POS (full morphosynt tags)
        - Special tags (<FP>, <WF>, <LI>, +)
        '''
        # special + special
        if self._is_special(cur_tag) and self._is_special(next_tag):
            return True
        # special + POS
        if (self._is_special(cur_tag)
              and not self._is_special(next_tag)
              and not next_tag == '#'):
            return True
        # POS + POS
        if not (self._is_special(cur_tag)
                or self._is_special(next_tag)
                or cur_tag == '#' or next_tag == '#'):
            together = self._belong_together_pos(cur_tag, next_tag)
            return together
        return False



        # if not self._is_synt(next_tag): # next is spe
        #     if self._is_synt(cur_tag):
        #         # case 1 : synt + non-synt => cut
        #         return True
        #     else:
        #         # case 2 : non-synt + non-synt
        #         return False

        # else: # next is synt
        #     if not self._is_synt(cur_tag):
        #         # case 3' non-synt + synt(long pause)
        #         if next_tag.GetLabel().GetValue() == '#':
        #             return True
        #         # case 3 : non-synt - synt
        #         return False
        #     else:
        #         # case 4 : synt - synt
        #         return not self._belong_together(cur_tag.GetLabel().GetValue(),
        #                                          next_tag.GetLabel().GetValue())


    def _is_special(self, tag):
        '''
        True if short pause, word fragment, filled pause or liason.

        In: (str)
        Out: (bool)

        '''
        if tag in ('<FP>', '<WF>', '<LI>', '+', ''):
            return True
        return False



    def _belong_together_pos(self, cur, nxt):
        '''
        Do two (unsimplified) tags belong to the same chunk?

        In:
        cur - str, morphosyntactic tag
        nxt - str, morphosyntactic tag

        Out: bool
        '''
        # if cur == '':
        #     self.stats['empty string'] += 1
        #     return True

        # (A) TAG .
#        left_empty_a = ['Cc','Cs', 'I', '<FP>']
        if cur == 'Cs':
            self.stats['Cs .'] += 1
            return True
        if cur == 'Cc':
            self.stats['Cc .'] += 1
            return True
        if cur == 'I':
            self.stats['I .'] += 1
            return True

        # (B) TAG . [^CI]
        if nxt != 'C' and nxt != 'I':
            if cur[0] == 'D':
                self.stats['D .'] += 1
                return True
            if cur[0] == 'S':
                self.stats['S .'] += 1
                return True
            if cur[:2] == 'Pp':
                self.stats['Pp .'] += 1
                return True
            if cur[:2] == 'Pr':
                self.stats['Pr .'] += 1
                return True
            if cur[:2] == 'Px':
                self.stats['Px .'] += 1
                return True
            if cur[:2] == 'Va':
                self.stats['Va .'] += 1
                return True
            if cur[:2] == 'Ve':
                self.stats['Ve .'] += 1
                return True
            if cur == 'Rpd':
                self.stats['Rpd .'] += 1
                return True
            if cur == 'Rpn':
                self.stats['Rpn .'] += 1
                return True

        # (C) TAG TAG
        # adjective + noun
        if cur[0]=='A' and nxt[0]=='N':
            self.stats['A N'] += 1
            return True
        # common noun + proper noun
        if cur[:2]=='Nc' and nxt[:2]=='Np':
            self.stats['Nc Np'] += 1
            return True
        # proper noun + proper noun
        if cur[:2]=='Np' and nxt[:2]=='Np':
            self.stats['Np Np'] += 1
            return True
        # cardinal noun + common noun
        if cur[:2]=='Nk' and nxt[:2]=='Nc':
            self.stats['Nk Nc'] += 1
            return True
        # demonstrative pronoun + verb
        if cur[:2]=='Pd' and nxt[0]=='V':
            self.stats['Pd V'] += 1
            return True
        # demonstrative pronoun + particle n'
        if cur[:2]=='Pd' and nxt[:3]=='Rpn':
            self.stats['Pd Rpn'] += 1
            return True
        # demonstr. pronoun + subord. conjunct.
        # turned off 27 mar 2013
        if cur[:2]=='Pd' and nxt=='Cs':
            self.stats['Pd Cs'] += 1
            return True
        # demonstr. pronoun + relative pronoun
        if cur[:2]=='Pd' and nxt[:2]=='Pr':
            self.stats['Pd Pr'] += 1
            return True
        # comparative adverb(? + pronoun
        if cur=='Rgc' and nxt[0]=='P':
            self.stats['Rgc P'] += 1
            return True
        # adverb + adjective
        if cur=='Rgp' and nxt[0]=='A':
            self.stats['Rgp A'] += 1
            return True
        # adverb + adverb
        if cur=='Rgp' and nxt=='Rgp':
            self.stats['Rgp Rgp'] += 1
            return True
        # adverb + participe passe
        if cur=='Rgp' and nxt[:4]=='Vmps':
            self.stats['Rgp Vmps'] += 1
            return True
        # verb + verb
        if cur[0]=='V' and nxt[0]=='V':
            self.stats['V V'] += 1
            return True
        # ex. v + pas
        if cur[0]== 'V' and nxt=='Rgd':
            self.stats['V Rgd'] += 1
            return True
        # ex. V + plus
        if cur[0]== 'V' and nxt=='Rgn':
            self.stats['V Rgn'] += 1
            return True
        # ??
        #if cur[0]=='V' and nxt[:2]=='Pd':
        #    self.stats['V Pd'] += 1
        #    return True
        # demonstrative pronoun + any but interrogative pronoun
        if cur[:2]=='Pd' and re.match('P[^t]', nxt):
            self.stats['Pd P[^t]'] += 1
            return True
        # ne + Adjectif
        if cur=='Rgn' and nxt[0]=='A':
            self.stats['Rgn A'] += 1
            return True
        return False


    def _merge_pauses(self, tier):
        '''
        Group sequences of pauses into a single pause
        (Treatment of data weirdness.)
        '''
        PAUSE_LABEL = ['#','+']
        new_tier = Tier(tier.GetName())
        pauses = []
        for t in tier:
            label = t.GetLabel()
            loc = t.GetLocation()
            if label.GetValue().strip() in PAUSE_LABEL:
                pauses.append(t)
            else:
                if pauses:
                    pauseannot = tierutil.create_annotation(
                        pauses[0].GetLocation().GetBegin(),
                        pauses[-1].GetLocation().GetEnd(),
                        '#')
                    new_tier.Add(pauseannot)
                    pauses = []
                new_tier.Add(t)
        return new_tier


    def _relabel_pauses(self, tier):
        '''
        Long pauses are marked with '#',
        short pauses --- with '+'.
        '''
        for annot in tier:
            label = annot.GetLabel()
            loc = annot.GetLocation()
            if label.GetValue().strip() in ['#', '+']:
                if loc.GetDuration() >= self.PAUSE_THRESHOLD:
                    label.SetValue('#')
                else:
                    label.SetValue('+')



    def _special_token_to_tag(self, token):
        '''
        Convert token to a tag if it corresponds
        to a filled pause, word fragment or liason,
        '<FP>', '<WF>' or '<LI>' respectively.
        Otherwise, leave the token unchanged.

        In: (str)
        Out: (str)
        '''
        # Label word fragments as <WF>.
        if re.match(r"([^'^ ])+\- |([^'^ ])+\-$", token):
            return '<WF>'
        # Label filled pauses as <FP>.
        elif re.match(r"(hm|euh|heu|mhhm|hum|mhm|pff)\b", token):
            return '<FP>'
        # Label liasons as <LI>.
        elif re.match("=[a-z]+=$", token):
            return '<LI>'
        # Return any other token unchanged.
        return token






    # def get_tags_grouped_by_chunk(self):
    #     '''
    #     Out: syntactic tags grouped into chunks (as 2d list)
    #     '''
    #     if self.chunk_tier == None:
    #         print 'Generating chunks..'
    #         self.generate_chunk_tier()
    #     tags_by_chunk = []
    #     for chunk in self.chunk_tier:
    #         tags = self._tags(chunk, 'simple')
    #         tags = [x.GetLabel().GetValue() for x in tags]
    #         tags_by_chunk.append(tags)
    #     return tags_by_chunk


    # def get_tokens_grouped_by_chunk(self):
    #     '''
    #     Out: 2d list, token intervals grouped into chunks
    #     '''
    #     if self.chunk_tier == None:
    #         print 'Generating chunks..'
    #         self.generate_chunk_tier()
    #     tags_by_chunk = []
    #     for chunk in self.chunk_tier:
    #         tokens = self._tokens(chunk)
    #         tags_by_chunk.append(tokens)
    #     return tags_by_chunk


    def _tags_of_interval(self, chunk, tags_type):
        '''
        In: chunk - annotationdata.annotation.Annotation object
            type_of_tags - string, accepted values: 'full', 'simple'
        Out: list of tag intervals contained in the chunk
        '''
        if tags_type == 'full':
            synt_tier = self.synt_tier
        elif tags_type == 'simple':
            if not self.simple_synt_tier:
                self.simplify_synt_tier()
            synt_tier = self.simple_synt_tier
        else:
            raise ValueError
        return [x for x in synt_tier
                if x.minTime >= chunk.minTime and x.maxTime <= chunk.maxTime]


    def _tokens_of_interval(self, interval):
        '''
        In: interval - textgrid.Interval
        Out: list of tokens belonging to the interval
        '''
        tokens = [x for x in self.token_tier
                  if x.minTime >= interval.minTime
                  and x.maxTime <= interval.maxTime]
        return tokens


    def _create_simple_synt_tier(self):
        '''
        Creates self.simple_synt_tier, a copy of self.synt_tier
        with simplified tags
        '''
        simple_tier = tierutil.create_tier(name='Chunk-simple-synt')
        for tag in self.synt_tier:
            simple_tag = self.simplify_tag(tag.GetLabel().GetValue())
            tagloc = tag.GetLocation()
            annot = tierutil.create_annotation(tagloc.GetBegin(),
                                               end=tagloc.GetEnd(),
                                               label=simple_tag)
            simple_tier.Add(annot)
        self.simple_synt_tier = simple_tier


    def simplify_tag(self, tag):
        '''
        Return simplified version of a given morpho-syntactic tag.

        Int: str
        Out: str
        '''
        if tag.startswith('A'):
            new_label = 'A'
        elif tag.startswith('C'):
            new_label = 'C'
        elif tag.startswith('D'):
            new_label = 'D'
        elif tag.startswith('I'):
            new_label = 'I'
        elif tag.startswith('Nc') or tag.startswith('Nk'):
            new_label = 'N'
        elif tag.startswith('Nd') or tag.startswith('Np'):
            new_label = 'Np'
        # "pronoun-object"
        elif re.match('Pp.+(j-|d-)$', tag):
            new_label = 'Po'
        # personal pronoun tonique form
        elif re.match('Pp.+o-$', tag):
            new_label = 'Pt'
        # personal pronoun - subject
        elif tag.startswith('Pp'):
            new_label = 'Pp'
        elif tag.startswith('Pd'):
            new_label = 'Pd'
        elif re.match('Pi|Pk|Pp|Ps', tag):
            new_label = 'P'
        # relative pronoun
        elif tag.startswith('Pr'):
            new_label = 'Pr'
        # pronoun - question word
        elif tag.startswith('Pt'):
            new_label = 'Pq'
        # pronom reflechi
        elif tag.startswith('Px'):
            new_label = 'Px'
        # negation: ne, pas, plus, non...
        elif re.match('Rpn|Rgn|Rgd', tag):
            new_label = 'Rn'
        elif tag.startswith('R'):
            new_label = 'R'
        elif tag.startswith('Spd+D'):
            new_label = 'S D'
        elif tag.startswith('S'):
            new_label = 'S'
        elif tag.startswith('Va') or tag.startswith('Ve'):
            new_label = 'Va'
        # infinitive
        elif tag.startswith('Vmn---'):
            new_label = 'Vi'
        elif tag.startswith('V'):
            new_label = 'V'
        elif tag.strip() == '':
            new_label = ''
        elif tag == '+':
            new_label = ''
        else:
            if tag not in ['<FP>', '<LI>', '<WF>', '#']:
                logging.warning('Unknown tag: '+tag)
            new_label = tag
        return new_label


    def _create_synt_category_tier(self):
        cat_tier = copy.deepcopy(self.chunk_tier)
        cat_tier.SetName('Chunk-s-category')
        for interval in cat_tier:
            label = interval.GetLabel()
            if label.GetValue() != '#':
                syntcat = self._which_synt_category(label.GetValue())
                interval.GetLabel().SetValue(syntcat)
        self.synt_cat_tier = cat_tier


    def _which_synt_category(self, pattern):
        '''
        In: (string) chunk's morphosyntactic pattern
        Out: (string) syntactic category
        '''
        tags = pattern.split()
        try:
            tags.remove('<FP>')
        except ValueError:
            pass
        try:
            tags.remove('<WF>')
        except ValueError:
            pass
        if len(tags) == 0:
            self.stats_category['DisfError'] += 1
            return 'DisfError'
        # PC -- prepositional -- ends with N, with preposition
        if tags[-1] in ['N', 'Np'] and 'S' in tags:
            self.stats_category['PC'] += 1
            return 'PC'
        # NC -- ends with N, without preposition
        if tags[-1] in ['N', 'Np'] and 'S' not in tags:
            self.stats_category['NC'] += 1
            return 'NC'
        # VC -- contains V or Va, without prepositions
        if ('V' in tags or 'Va' in tags
                or 'Vi' in tags) and 'S' not in tags:
            self.stats_category['VC'] += 1
            return 'VC'
        # PVC -- ends with verb with prep
        if tags[-1] in ['V', 'Vi'] and 'S' in tags:
            self.stats_category['PVC'] += 1
            return 'PVC'
        # AC -- adjecive chunk, ends with adjective
        if tags[-1] == 'A':
            self.stats_category['AC'] += 1
            return 'AC'
        # RC -- adverbial chunk, ends with adverb
        if tags[-1] == 'R':
            self.stats_category['RC'] += 1
            return 'RC'
        # IC -- only I or C
        if list(set(tags)) in [['I'], ['C'], ['I', 'C']]:
            self.stats_category['IC'] += 1
            return 'IC'
        # Disfluencies or Tagging errors
        self.stats_category['DisfError'] += 1
        return 'DisfError'


    def _create_disf_tiers(self):
        '''
        Creates two tiers:
          self.disf_cat_tier - projection of pattern calssification
            aimed at identification of disfluency
          self.disf_bool_cat_tier - indicates presence/absence of disfluency

        Reads regexes and spokenhood classes
        from chunker_fr_resources.pickle
        '''
        # Create disf_cat_tier
        cat_tier = copy.deepcopy(self.chunk_tier)
        cat_tier.SetName('Chunk-disf-category')
        resources = pickle.load(open('/Users/klimpeshkov/work/chunkers/chunker_fr_resources.pickle'))
        i = 0
        while i < len(cat_tier):
            patterns = self._triwindow(cat_tier, i)
            label = cat_tier[i].GetLabel()
            if label.GetValue() != '#':
                disfcat = self._which_disf_category(patterns, resources)
                label.SetValue(disfcat)
            i += 1
        self.disf_cat_tier = cat_tier

        # Create disf_bool_tier
        disfluent_categories = ['atro', 'hyper', 'FPWF']
        nondisfluent_categories = ['backchannel', 'hesitation', 'canonical',
                                   'spoken_canonical', 'd_marker', 'rare']
        bool_tier = copy.deepcopy(cat_tier)
        bool_tier.SetName('Chunk-disf-boolean')
        for annot in bool_tier:
            label = annot.GetLabel()
            if label.GetValue() == '#':
                pass
            if label.GetValue() in disfluent_categories:
                label.SetValue('1')
            elif label.GetValue() in nondisfluent_categories:
                label.SetValue('0')
        self.disf_bool_tier = bool_tier


    def _triwindow(self, list_, i):
        '''
        In:
          list_ (list)
          i - range (0,)
        '''
        if i < 0:
            raise ValueError('negative i')
        cur = list_[i].GetLabel().GetValue()
        if i == 0:
            prev = None
        else:
            prev = list_[i-1].GetLabel().GetValue()
        if i == len(list_) - 1:
            next_ = None
        else:
            next_ = list_[i+1].GetLabel().GetValue()
        return prev, cur, next_


    def _which_disf_category(self, patterns, resources):
        pre, cur, nex = patterns
        # 'Backchannels' sequence of 'I's, surrounded by pauses
        bc = re.compile(r'^[I]( I)*$')
        # 'Discourse markers' sequence of 'C's and 'I's
        dm = re.compile(r'^[CI]( [CI])*$')
        if cur.strip() == '': # empty pattern
            return ''
        elif re.search(r'<FP>|<WF>', cur):
            return 'FPWF'
        elif (re.match(bc, cur) and
              pre in ['#', None] and
              nex in ['#', None]):
            return 'backchannel'
        elif re.match(dm, cur):
            return 'd_marker'
        elif self._is_atro(cur, resources['atroph']):
            return 'atro'
        elif self._is_hyper(cur, resources['hypertroph']):
            return 'hyper'
        elif self._is_hesitation(cur, resources['canonical']): #sequence of C/I + canon ("Hesitation")
            return 'hesitation'
        elif cur in resources['canonical']:
            return 'canonical'
        elif cur in resources['spoken_canonical']:
            return 'spoken_canonical'
        else:
            return 'rare'


    def _is_hesitation(self, pattern, canonical_list):
        for c in canonical_list:
            if re.match('([CI] )+' + c, pattern):
                return True
        return False


    def _is_atro(self, pattern, atro_list):
        '''
        In:
          pattern (str)
          atro_list (list) - regexes for atrophs
        Out: (bool) True
               - if the pattern matches one of regexes from the list
               - if the pattern contains no head
        '''
        for a in atro_list:
            if re.match(a, pattern):
                return True
        # Pattern is atro if doesn't contain any head
        heads = set(['A', 'N', 'Np', 'P', 'Pd', 'Pq', 'Pt', 'R',
                     'Rn', 'Va','V', 'Vi'])
        tags = set(pattern.split())
        if not tags.intersection(heads):
            return True
        return False


    def _is_hyper(self, pattern, hyper_list):
        '''
        In:
          pattern (str)
          hyper_list (list) - regexes for hypertrophs
        Out: (bool) True if equals or contains one of the hyper
        '''
        for hyper in hyper_list:
            if re.search(hyper, pattern):
                return True
        return False


    ###################################################### I/O #########

    def write_textgrid(self, filename, token_tier=False, synt_tier=False,
                       simple_synt_tier=False):
        '''Save chunks tier in a textgrid'''
        if self.chunk_tier is None:
            self.launch_chunking()
        grid = Transcription()
        if token_tier:
            grid.Append(self.token_tier)
        if synt_tier:
            grid.Append(self.synt_tier)
        if simple_synt_tier:
            grid.Append(self.simple_synt_tier)
        grid.Append(self.chunk_tier)
        grid.Append(self.synt_cat_tier)
        grid.Append(self.disf_cat_tier)
        grid.Append(self.disf_bool_tier)
        aio.write(filename, grid)
        print 'TextGrid with {} intervals written to {}'.format(
            len(self.chunk_tier), filename)


    def write_stats(self, path):
        '''
        Write rule application counts to a comma-separated file.

        In:
        path (str) path and file name
        '''
        stats_file = open(path, 'w')
        for key in self.skeys:
            stats_file.write(key+','+str(self.stats[key])+'\n')
        stats_file.close()


    # doesn't work
    # def save_chunks_as_xls(self, filename):
    #     '''Write chunks' constituents into an Excel spreadsheet'''
    #     import xlwt
    #     if self.chunk_tier == None:
    #         print 'Generating chunks..'
    #         self.generate_chunk_tier()
    #     print 'Converting to Excel..'
    #     wb = xlwt.Workbook()
    #     ws = wb.add_sheet('Chunks-pattern')
    #     ws.write(0, 0, 'chunk start')
    #     ws.write(0, 1, 'chunk end')
    #     ws.write(0, 2, 'length (stokens)')
    #     ws.write(0, 3, 'length (tokens)')
    #     ws.write(0, 4, 'tokens')
    #     ws.write(0, 5, 'morph - simple')
    #     ws.write(0, 6, 'morph - full')
    #     row = 1
    #     #chunk_tier = [x for x in chunk_tier if x.mark != '#']
    #     for chunk in self.chunk_tier:
    #         simple_tags = chunk.GetLabel().GetValue()
    #         full_tags = self._tags(chunk, 'full')
    #         tokens = self._tokens(chunk)
    #         #convert utf8 to ascii
    #         tokens = [x.GetLabel().GetValue() for x in tokens]
    #         #tokens_u = [unicode(x.mark, 'utf8') for x in tokens]
    #         #tokens_ascii = [x.encode('ascii','xmlcharrefreplace') for x in tokens_u]
    #         ws.write(row, 0, str(chunk.BeginValue))
    #         ws.write(row, 1, str(chunk.EndValue))
    #         ws.write(row, 2, str(len(simple_tags)))
    #         ws.write(row, 3, str(len(tokens)))
    #          #print ' '.join(tokens_ascii)
    #         ws.write(row, 4, ' '.join(tokens))#_ascii))
    #         ws.write(row, 5, simple_tags)
    #         ws.write(row, 6, ' '.join([x.GetLabel().GetValue() for x in full_tags]))
    #         row += 1
    #     ws.write(0, 7, 'total:')
    #     ws.write(0, 8, str(row))
    #     wb.save(filename)
    #     print filename, 'written'
