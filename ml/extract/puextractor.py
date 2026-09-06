# encoding: utf-8
from __future__ import division
import math
# import numpy as np
import copy as cp
from annotationdata.ptime.interval import TimeInterval
import data_access as da
import groupsegm as gs
from extractor import Extractor


class PUExtractor(Extractor):
    '''
    Class for extracting features to detect prosodic units.
    Uses information from two TextGrid tiers:
    syllables and prosodic units (PU).

    Iterates through syllables (excluding pauses).
    '''
    def __init__(self, speaker, data=None, copy=False):
        '''
        In:
          speaker (str) Used as prefix to name intermediate files.
          data (list) If a piece of data is missing, use None.
            Expected Tiers in GroupSegm:
              0 tokens (Tier)
              1 syllables (Tier)
              2 ip: intermediate prosodic units (Tier)
              3 ap: intermediate prosodic units (Tier)
              4 raw pitch (PitchTier)
              5 stylized pitch (PitchTier)
              6 nuclei
              7 chunks - POS tags
              8 chunks - disfluency categories
              9 chunks - disfluency boolean
          pause_labels (tuple) Labels for silent pauses
        '''
        # Initialize parent
        super(PUExtractor, self).__init__()

        self._pitch_styl = None # 2d list, raw pitch grouped by syllables
        self._pitch_raw = None  # 2d list, raw pitch grouped by syllables
        self.avg_pause_dur = None
        self.pitch_range = None

        # Available feature subsets in order
        self._subset_order = ['TIME', 'SPEAKER',
                              'PD', 'PP', 'PS',
                              'SB', 'SC', 'SD',
                              'DU', 'AP', 'IP']
        # Lengths of feature subsets
        self._subset_len = {'PD':8, 'PP':10, 'PS':3,
                            'SB':1, 'SC':8, 'SD':4,
                            'DU':1, 'IP':1, 'AP':1}
        if copy:
            self.data = cp.copy(data)
        else:
            self.data = data  # tokens tier will be modified (merge pauses)
        self.speaker = speaker


    @property
    def data(self):
        '''
        Dictionnary interface to data tiers
        '''
        return self._data


    @data.setter
    def data(self, indata):
        '''
        In:  GroupSegm or other sequence of Tiers
        '''
        if indata is None:
            return
        if isinstance(indata, gs.GroupSegm):
            self._data = indata
        else:
            self._data = gs.GroupSegm(indata)
        # One training example corresponds to one syllable
        self._data.reference_name = 'syllable'

        # Calculations
        self.avg_pause_dur = self._calc_average_pause_duration()
        if 'pitch-styl' in self.data.names:
            self.pitch_range = self._calc_pitch_range()
        else:
            self.pitch_range = None
        # Preprocess syllable tier
        self._merge_pauses(self.data.reference.Name)


    # ============= Feature subset calculation =============

    def calc_PD(self, index):
        '''
        In: (int) index of the syllable
        Out: (list) of duration-related features
        '''
        features = []
        features.append(self._feat_pd1(index))
        features.append(self._feat_pd2(index))
        features.append(self._feat_pd3(index))
        features.append(self._feat_pd4(index))
        features.append(self._feat_pd5(index))
        features.append(self._feat_pd6(index))
        features.append(self._feat_pd7(index))
        features.append(self._feat_pd8(index))
        return features


    def calc_PP(self, index):
        '''
        Prosody: Pitch
        In: (int) index of the syllable
        Out: (list) of values of pitch-related features
        '''
        if ('pitch-raw' not in self.data.names
                or 'pitch-styl' not in self.data.names):
            raise Exception("Raw and stylized PitchTiers must be loaded.")
        self._prep_pitch()

        # Get pitch values for this and neighbouring syllables
        s1_index = self._get_syllable_index(index, offset=1)
        s_1_index = self._get_syllable_index(index, offset=-1)
        s_2_index = self._get_syllable_index(index, offset=-2)

        if index < len(self._pitch_styl):
            s0 = self._pitch_styl[index]
        else:
            self._log.debug('_pitch_styl too short. token '+str(index))
            s0 = None
        if index < len(self._pitch_raw):
            s0raw = self._pitch_raw[index]
        else:
            self._log.debug('_pitch_raw too short. token '+str(index))
            s0raw = None
        if (s1_index is not None
                and s1_index < len(self._pitch_styl)
                and s1_index < len(self._pitch_raw)):
            s1 = self._pitch_styl[s1_index]
            s1raw = self._pitch_raw[s1_index]
        else:
            s1 = None
            s1raw = None
        if s_1_index is not None:
            s_1 = self._pitch_styl[s_1_index]
        else:
            s_1 = None
        if s_2_index is not None:
            s_2 = self._pitch_styl[s_2_index]
        else:
            s_2 = None

        features = []
        features.append(self._feat_pp1(index, s0, s1))  # pp1
        features.append(self._feat_pp2(index, s0raw, s1raw)) # pp2
        features.append(self._feat_pp3(index, s0, s1)) # pp3
        features.append(self._feat_pp4(index, s0, s1, s_1)) # pp4
        features.append(self._feat_pp5(index, s0, s1, s_1, s_2)) # pp5
        features.append(self._feat_pp6(index, s1)) # pp6
        features.append(self._feat_pp7(index)) # pp7
        features.append(self._feat_pp8(index)) # pp8
        features.append(self._feat_pp9(index)) # pp9
        features.append(self._feat_pp10(index)) # pp10
        return features


    def calc_PS(self, index):
        '''
        Prosody: Silences
        In: (int) index of the syllable
        Out: (list) of values of pitch-related features
        '''
        features = []
        features.append(self._feat_ps1(index)) # ps1
        features.append(self._feat_ps2(index)) # ps2
        features.append(self._feat_ps3(index)) # ps3
        return features


    def calc_SB(self, index):
        features = []
        features.append(self._feat_sb1(index)) # sb1
        return features


    def calc_SC(self, index):
        features = []
        features.append(self._feat_sc1(index)) # sc1
        features.append(self._feat_sc2(index)) # sc2
        features.append(self._feat_sc3(index)) # sc3
        features.append(self._feat_sc4(index)) # sc4
        features.append(self._feat_sc5(index)) # sc5
        features.append(self._feat_sc6(index)) # sc6
        features.append(self._feat_sc7(index)) # sc7
        features.append(self._feat_sc8(index)) # sc8
        return features


    def calc_SD(self, index):
        features = []
        features.append(self._feat_sd1(index)) # sd1
        features.append(self._feat_sd2(index)) # sd2
        features.append(self._feat_sd3(index)) # sd3
        features.append(self._feat_sd4(index)) # sd4
        return features


    def calc_DF(self, index):
        features = []
        features.append(self._feat_df1(index)) # sd1
        features.append(self._feat_df2(index)) # sd2
        features.append(self._feat_df3(index)) # sd3
        features.append(self._feat_sd4(index))
        return features

    def _feat_df1(self, index):
        '''
        Disfluence: D
        Out:
        '''
        disf = self._get_disf(index)
        return disf.TextValue[0] == 'D'


    def _feat_df2(self, index):
        '''
        Inside disfluence: I
        Out:
        '''
        disf = self._get_disf(index)
        return disf.TextValue[0] == 'I'


    def _feat_df3(self, index):
        '''
        Inside disfluence : R
        Out:
        '''
        disf = self._get_disf(index)
        return disf.TextValue[0] == 'R'

    def _feat_df4(self, index):
        '''
        Count of many reference units from
        '''
        pass


    # def check_disf(tier, time):
    #     '''
    #     === Out ===
    #     [False, u'-D', u'D', u'-I', u'D-R', u'R', u'I-', u'R-'])
    #     '''
    #     match = find_interval(tier, time)
    #     if match:
    #         text = [x.text.strip() for x in match]
    #         text = '-'.join(text)
    #         if text:
    #             return text
    #         else:
    #             return False
    #     else:
    #         # print 'Found no interval containing', time
    #         return False



    #================[ Features PD. Yi-Fen's duration features]====

    def _feat_ps1(self, index):
        '''
        Followed by pause
        Out: 0 or 1
        '''
        if index > len(self.data.dict['syllable'])-2:
            return 0
        if self._is_pause(index+1, mindur=self.pause_threshold):
            return 1
        return 0


    def _feat_ps2(self, index):
        '''
        Normalized duration of the following pause.
        Out: (float) pause duration / average pause duration
             or None if the next interval is not a pause.
        '''
        if index > len(self.data.dict['syllable'])-2:
            return None
        if self._is_pause(index+1):
            p = self.data.dict['syllable'][index+1].Time.Duration()
            return p / self.avg_pause_dur
        return None


    def _feat_pd1(self, index):
        '''
        Next syllable duration / current
        S[i+1] / S[i]
        Out: (float)
        '''
        # Jump only over small pauses
        index1 = self._get_syllable_index(index, offset=1, jump=True,
                                          jump_maxdur=self.pause_threshold)
        if index1 is None:
            return None

        d0 = self.data.dict['syllable'][index].Time.Duration()
        d1 = self.data.dict['syllable'][index1].Time.Duration()
        return d1 / d0


    def _feat_pd2(self, index):
        '''
        Average of 2 next syllables durations / current
        (S[i+1]+S[i+2]) / 2 / S[i]
        Out:float
        '''
        # Jump only over small pauses
        index1 = self._get_syllable_index(index, offset=1, jump=True,
                                          jump_maxdur=self.pause_threshold)
        index2 = self._get_syllable_index(index, offset=2, jump=True,
                                          jump_maxdur=self.pause_threshold)
        if None in (index1, index2):
            return None

        s0 = self.data.dict['syllable'][index].Time.Duration()
        s1 = self.data.dict['syllable'][index1].Time.Duration()
        s2 = self.data.dict['syllable'][index2].Time.Duration()
        return (s1+s2) / 2 / s0


    def _feat_pd3(self, index):
        '''
        Average of 3 next syllables durations / current
        (S[i+1]+S[i+2]+S[i+3]) / 2 / S[i]
        Out:float
        '''
        # Jump only over small pauses
        index1 = self._get_syllable_index(index, offset=1, jump=True,
                                          jump_maxdur=self.pause_threshold)
        index2 = self._get_syllable_index(index, offset=2, jump=True,
                                          jump_maxdur=self.pause_threshold)
        index3 = self._get_syllable_index(index, offset=3, jump=True,
                                          jump_maxdur=self.pause_threshold)
        if None in (index1, index2, index3):
            return None

        s0 = self.data.dict['syllable'][index].Time.Duration()
        s1 = self.data.dict['syllable'][index1].Time.Duration()
        s2 = self.data.dict['syllable'][index2].Time.Duration()
        s3 = self.data.dict['syllable'][index3].Time.Duration()
        return (s1+s2+s3) / 3 / s0


    def _feat_pd4(self, index):
        '''
        (S[i+1]+...+ S[i+N]) / N / S[i]
        where N is number of syllables until the next pause
        Out:float
        '''

        offset = 0 # How many syllables before long pause
        while (index+offset < len(self.data.dict['syllable'])
               and not self._is_pause(index+offset,mindur=self.pause_threshold)):
            offset += 1
        if offset == 0:
            return None
        next_indices = []
        for off in range(1, offset+1):
            next_indices.append(self._get_syllable_index(index, offset=off,
                                    jump=True, jump_maxdur=self.pause_threshold))
        next_indices = [x for x in next_indices if x] # Remove None values
        if len(next_indices) == 0:
            return None

        sum_dur_next = sum([self.data.dict['syllable'][x].Time.Duration()
                            for x in next_indices])
        s0 = self.data.dict['syllable'][index].Time.Duration()
        res = sum_dur_next / len(next_indices) / s0
        return res


    def _feat_pd5(self, index):
        '''
        Ratio of current syllable length to average length
        of currrent syllable and 2 next syllables.
          S[i] / (((S[i+1]+S[i+2])/2+S[i])/2)
        Out:float
        '''
        # Jump only over small pauses
        index1 = self._get_syllable_index(index, offset=1, jump=True,
                                          jump_maxdur=self.pause_threshold)
        index2 = self._get_syllable_index(index, offset=2, jump=True,
                                          jump_maxdur=self.pause_threshold)
        if None in (index1, index2):
            return None

        s0 = self.data.dict['syllable'][index].Time.Duration()
        s1 = self.data.dict['syllable'][index1].Time.Duration()
        s2 = self.data.dict['syllable'][index2].Time.Duration()
        return s0 / (((s1+s2)/2+s0)/2)


    def _feat_ps3(self, index):
        '''
        Ratio of pause duration to current syllable length.
        (If next interval is a pause).
        '''
        # End of the tier
        if index > len(self.data.dict['syllable'])-2:
            return None
        # Abandon if the next interval is not a pause
        if not self._is_pause(index+1):
            return None
        s0 = self.data.dict['syllable'][index].Time.Duration()
        s1 = self.data.dict['syllable'][index+1].Time.Duration()
        return s1 / s0


    def _feat_pd6(self, index):
        '''
        S[i] / ((S[i-1]+S[i-2])/2)
        '''

        # Jump only over small pauses
        index_1 = self._get_syllable_index(index, offset=-1, jump=True,
                                           jump_maxdur=self.pause_threshold)
        index_2 = self._get_syllable_index(index, offset=-2, jump=True,
                                           jump_maxdur=self.pause_threshold)
        if None in (index_1, index_2):
            return None
        s0 = self.data.dict['syllable'][index].Time.Duration()
        s_1 = self.data.dict['syllable'][index_1].Time.Duration()
        s_2 = self.data.dict['syllable'][index_2].Time.Duration()
        res = s0 / ((s_1+s_2)/2)
        return res


    #================[ Features P. Yi-Fen's pitch features. ]=====

    def _feat_pp1(self, index, s0, s1):
        '''
        Difference between the first raw F0 value of the next
        syllable nucleus and last value of the current syllable nucleus.

        S[i+1][0]-S[i][-1] / pitch_range
        '''
        if None in [s0, s1]:
            return None
        return (s1[0]-s0[-1]) / self.pitch_range


    def _feat_pp2(self, index, s0, s1):
        '''
        Difference between the first raw F0 value of the next
        syllable nucleus and last value of the current syllable nucleus.

        S[i+1][0]-S[i][-1] / pitch_range
        '''
        if None in [s0, s1]:
            return None
        return (s1[0]-s0[-1]) / self.pitch_range


    def _feat_pp3(self, index, s0, s1):
        '''
        Ratio of mean F0 difference of current syllable start
        and next syllable start to pitch range.
        Pitch of a syllable start is average of syllable's
        3 first pitch values.
        '''
        if None in [s0, s1]:
            return None
        s0 = self._calc_avg_3first(s0)
        s1 = self._calc_avg_3first(s1)
        return (s1-s0) / self.pitch_range


    def _feat_pp4(self, index, s0, s1, s_1):
        '''
        Ratio of pitch difference between the mean of 2 syllable
        starts and the next syllable start to pitch range.
        Pitch of a syllable start is average of syllable's
        3 first pitch values.
        '''
        if None in [s0, s1, s_1]:
            return None
        s0 = self._calc_avg_3first(s0)
        s1 = self._calc_avg_3first(s1)
        s_1 = self._calc_avg_3first(s_1)
        return (s1-(s_1+s0)/2) / self.pitch_range


    def _feat_pp5(self, index, s0, s1, s_1, s_2):
        '''
        Ratio of pitch difference between mean of 3 syllable
        starts and the next syllable start to pitch range.
        Pitch of a syllable start is average of syllable's
        3 first pitch values.
        '''
        if None in [s0, s1, s_1, s_2]:
            return None
        s0 = self._calc_avg_3first(s0)
        s1 = self._calc_avg_3first(s1)
        s_1 = self._calc_avg_3first(s_1)
        s_2 = self._calc_avg_3first(s_2)
        return (s1-(s_2+s_1+s0)/3) / self.pitch_range


    def _feat_pp6(self, index, s1):
        '''
        Ratio of difference of first pitch value after previous
        pause and first pitch value after current syllable boundary
        to pitch range.
        '''
        # Find previous pause
        pause_index = index-1
        while pause_index > 0 and not self._is_pause(pause_index):
            pause_index -= 1
        s_ap = self.calc_syll_styl_pitch(pause_index+1)
        if None in [s_ap, s1]:
            return None
        return s_ap[0]-s1[0] / self.pitch_range  # invert difference?



    # ===========[ Features S --- SIMON & MERTENS 2013 ]========== #

    def _feat_pd7(self, index):
        '''
        Duration of syl0 is 2 times higher than context mean and nucleus duration > 40 ms
        Out: 1 or 0
        '''
        dur_ratio = self._feat_pd8(index)
        if dur_ratio is None:
            return None
        if self.data.dict.has_key('nuclei'):
            nucleus = self.get_syllable_nucleus(index)
            # if nucleus is not detected, ignore nucleus duration rule
            if nucleus is not None:
                nucleus_dur = nucleus.Duration()
                return int(dur_ratio >= 2 and nucleus_dur > 0.04)
        return int(dur_ratio >= 2)


    def _feat_pp7(self, index):
        '''
        Intrasyllabic pitch rise >= 4 ST
        Out: 1 or 0
        '''
        rise = self._feat_pp9(index)
        if rise is None:
            return None
        return int(rise >= 4)


    def _feat_pp8(self, index):
        '''
        Average syllable pitch / context mean pitch >= 5 ST
        Out: (bool)
        '''
        ratio = self._feat_pp10(index)
        if ratio is None:
            return None
        return int(ratio >= 5)


    def _feat_pd8(self, index):
        '''
        Ratio of syllable's duration to context mean
        Out: (float)
        '''
        context = self._calc_context_duration(index)
        if context is None:
            return None
        return self.data.dict['syllable'][index].Time.Duration() / context


    def _feat_pp9(self, index):
        '''
        Intrasyllabic rise in ST
        Out: (float)
        '''
        syll = self._pitch_styl[index]
        if syll is None or len(syll) < 2:
            return None
        rise = 0
        i = 0
        while i < len(syll)-1:
            move = self._fq_to_semitone(syll[i],syll[i+1])
            if move > 0:
                rise += move
            i += 1
        return rise


    def _feat_pp10(self, index):
        '''
        Distance syllbale pitch to context mean pitch in semitones
        Out: (float)
        '''
        syll = self._pitch_styl[index]
        context = self._calc_context_pitch(index)
        if syll is None or context is None:
            return None
        syll_avg = sum(syll)/len(syll)
        res = self._fq_to_semitone(syll_avg, context)
        return res

    # === S auxilary ===

    def _calc_context_pitch(self, index):
        '''
        Calculate average of averaged pitch values of 2 left
        and 1 right neighbours of the current syllable.
        Exclude syllables situated further than 500 ms.

        TODO: Syllables marked as hesitations are not used.
           (Generate hesitations tier first)
        '''
        nindices = [self._get_syllable_index(index,offset=x,
                                             jump=True,maxdist=0.5)
                    for x in (-2,-1,1)]
        nindices = [x for x in nindices if x is not None]
        if not nindices:
            return None

        pitch = [self._pitch_styl[i] for i in nindices]
        pitch = [x for x in pitch if x]
        if not pitch:
            return None
        # generate list of average pitch values
        pitch_avg = [sum(x)/len(x) for x in pitch]
        # average of the averages
        res = sum(pitch_avg)/len(pitch_avg)
        return res


    def _calc_context_duration(self, index):
        '''
        Calculate average of durations of 2 left
        and 1 right neighbours of the current syllable.
        Exclude syllables situated further than 500 ms.

        TODO: Syllables marked as hesitations are not used.
           (Generate hesitations tier first)
        '''
        nindices = [self._get_syllable_index(
            index,offset=x,jump=True,maxdist=0.5) for x in (-2,-1,1)]
        nindices = [x for x in nindices if x is not None]
        if not nindices:
            return None
        durations = [self.data.dict['syllable'][i].Time.Duration()
                    for i in nindices]
        return sum(durations)/len(durations)


    def _fq_to_semitone(self, fq1, fq2):
        return (12/math.log(2)) * math.log (fq1 / fq2)


    # =============== Features C. Syntactic chunks =============

    def _feat_sb1(self, index):
        '''
        Syllable is final syllable of chunk
        Out: 1 or 0
        '''
        syll_end = self.data.reference[index].End
        chunk_end = self._get_chunk(index).End
        return int(syll_end == chunk_end)


    def _feat_sc1(self, index):
        '''
        Syllable belongs to VC chunk.
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'pos').TextValue == 'VC':
            return 1
        return 0


    def _feat_sc2(self, index):
        '''
        Syllable belongs to IC chunk.
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'pos').TextValue == 'IC':
            return 1
        return 0


    def _feat_sc3(self, index):
        '''
        Syllable belongs to NC chunk.
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'pos').TextValue == 'NC':
            return 1
        return 0


    def _feat_sc4(self, index):
        '''
        Syllable belongs to PC chunk.
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'pos').TextValue == 'PC':
            return 1
        return 0


    def _feat_sc5(self, index):
        '''
        Syllable belongs to AC chunk.
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'pos').TextValue == 'AC':
            return 1
        return 0


    def _feat_sc6(self, index):
        '''
        Syllable belongs to PVC chunk.
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'pos').TextValue == 'PVC':
            return 1
        return 0


    def _feat_sc7(self, index):
        '''
        Syllable belongs to RC chunk.
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'pos').TextValue == 'RC':
            return 1
        return 0


    def _feat_sc8(self, index):
        '''
        Syllable belongs to DisfError chunk.
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'pos').TextValue == 'DisfError':
            return 1
        return 0


    def _feat_sd1(self, index):
        '''
        Syllable belongs to a disfluent chunk
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'disf-bool').TextValue == '1':
            return 1
        return 0


    def _feat_sd2(self, index):
        '''
        Syllable belongs to an 'atro' chunk
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'disf-cat').TextValue == 'atro':
            return 1
        return 0


    def _feat_sd3(self, index):
        '''
        Syllable belongs to a 'hyper' chunk
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'disf-cat').TextValue == 'hyper':
            return 1
        return 0


    def _feat_sd4(self, index):
        '''
        Syllable belongs to a spoken-canonical chunk
        Out: 1 or 0
        '''
        if self._get_chunk(index, 'disf-cat').TextValue == 'spoken_canonical':
            return 1
        return 0


    # ======================== C aux ==========================
    def _get_chunk(self, index, which='pos'):
        '''
        === In ===
        index : int
            index of the reference unit
        which : {'pos', 'disf-bool', 'disf-cat'}
            'pos' - part-of-speech category
            'disf-bool' - disfluent or not
            'disf-cat' - disfluency category
        === Out ===
        Annotation
        '''
        allowed = ('pos', 'disf-bool', 'disf-cat')
        if which not in allowed:
            raise ValueError('Allowed values of "which": '+' '.join(allowed))
        tiername = 'chunk-' + which
        refunit = self.data.reference[index]
        try:
            chunk_index = self.data.dict[tiername].Near(refunit.Begin,-1)
            chunk = self.data.dict[tiername][chunk_index]
        except IndexError: #TODO not a very clean solution
            chunk = self.data.dict[tiername][-1]
            msg = 'ref unit {}, disf not found. Using last:{}.'.format(index, str(chunk))
            self._log.warning(msg)
        return chunk


    def _get_disf(self, index):
        '''
        === In ===
        index
        === Out ==
        Annotation
        '''
        tiername = 'disfluency'
        refunit = self.data.reference[index]
        try:
            disf_index = self.data.dict[tiername].Near(refunit.Begin,-1)
            disf = self.data.dict[tiername][disf_index]
        except IndexError: #TODO not a very clean solution
            disf = self.data.dict[tiername][-1]
            msg = 'ref unit {}, disf not found. Using last:{}.'.format(index, str(disf))
            self._log.warning(msg)
        return disf

    # ======================== P aux ==========================

    def _calc_pitch_range(self):
        '''
        Pitch range from stylized values
        '''
        pvalues = [float(x.TextValue) for x in self.data.dict['pitch-styl']]
        return max(pvalues) - min(pvalues)
        # p02 = np.percentile(pvalues, 2)
        # p98 = np.percentile(pvalues, 98)
        # return p98 - p02


    def _prep_pitch(self):
        if self._pitch_styl is None:
            self._prep_pitch_styl()
        if self._pitch_raw is None:
            self._prep_pitch_raw()


    def _prep_pitch_raw(self):
        '''
        Group raw pitch values by syllable
        '''
        self._log.info('Preparing raw pitch grouped by syllable')
        # Load intermediate data from disk if it exists
        pitch = da.load_interm_pitch_raw(self.speaker)
        if pitch is not None:
            if len(pitch) == len(self.data.dict['syllable']):
                self._pitch_raw = pitch
                return
            else:
                msg = 'Length mismatch: pitch:{}, syllables:{}'
                msg = msg.format(len(pitch), len(self.data.dict['syllable']))
                # if len(pitch) > len(self.data.dict['syllable']):
                #     self._log.warning(msg+'--> ignoring')
                #     self._pitch_raw = pitch
                #     return
                # else:
                #     self._log.warning(msg+'--> recalculating')
            self._log.warning(msg+'--> recalculating')
        self._log.info('Grouping raw pitch values by syllable')
        pitch = []
        for i in range(len(self.data.dict['syllable'])):
            pitch.append(self.calc_syll_raw_pitch(i))
            self._log_progress(i, len(self.data.dict['syllable']))
        self._pitch_raw = pitch
        # Write intermediate data
        da.write_interm_pitch_raw(pitch, self.speaker)



    def _prep_pitch_styl(self):
        '''
        Group stylized pitch values by syllable
        '''
        self._log.info('Preparing stylized pitch grouped by syllable')
        # Load intermediate data from disk if it exists
        pitch = da.load_interm_pitch_styl(self.speaker)
        if pitch is not None:
            if len(pitch) == len(self.data.dict['syllable']):
                self._pitch_styl = pitch
                return
            else:
                msg = 'Length mismatch: pitch:{}, syllables:{}'
                msg = msg.format(len(pitch), len(self.data.dict['syllable']))
                # if len(pitch) > len(self.data.dict['syllable']):
                #     self._log.warning(msg+' --> ignoring')
                #     self._pitch_styl = pitch
                #     return
                # else:
                #     self._log.warning(msg+' --> recalculating')
                self._log.warning(msg+' --> recalculating')
        self._log.info('Grouping stylized pitch values by syllable')
        pitch = []
        for i in range(len(self.data.dict['syllable'])):
            pitch.append(self.calc_syll_styl_pitch(i))
            self._log_progress(i, len(self.data.dict['syllable']))
        self._pitch_styl = pitch
        # Write intermediate data
        da.write_interm_pitch_styl(pitch, self.speaker)


    def _get_syllable_index(self, index, offset, jump=True, jump_maxdur=0,
                            maxdist=None):
        '''
        Get index of the syllable of a syllable's neighbour

        In:
          index (int) - index of the syllable whose neighbour we're looking for
          offset (int) - non-zero values let look for neighbours, for ex.:
              if offset==1, return values for the next syllable
          jump (bool) True: jump accross pauses to get to the neighbour,
              False: just return None if there's a pause on the way
          jump_maxdur (float) If the parameter is supplied, jump only
              over pauses shorter than this value
          maxdist (None or float) - radius of time-based symmetric
              window around the syllable.
              Window bounds:
                  ('time_limit'-syllable.Begin, syllable.EndValue+'time_limit')
              Returns 'None' if both borders of the neighbour fall
                outside of the window.

        Out:
          integer or None

        '''
        if offset > 0:
            if index > len(self.data.dict['syllable']) - (offset+2):
                return None # End of segmentation
        if offset < 0:
            if index < abs(offset)+2:
                return None # Beginning of segmentation

        if not jump:
            if offset > 0:
                # Abandon if there're pauses on our way.
                # If jump_maxdur is supplied, abandon only if they are this long.
                # Otherwise go on and jump over.
                if self._count_pauses(range(0,offset+1,1),mindur=jump_maxdur):
                    return None
            elif offset < 0:
                if self._count_pauses(range(0,offset-1,-1),mindur=jump_maxdur):
                    return None

        # Do jump
        if offset > 0:     # 0--->
            pauses_n = self._count_pauses(range(index, index+offset+1, 1))
            nindex = index + offset + pauses_n
            if self._is_pause(nindex):
                nindex += 1
        elif offset < 0:   # <---0
            pauses_n = self._count_pauses(range(index, index+offset-1, -1))
            nindex = index + offset - pauses_n
            if self._is_pause(nindex):
                nindex -= 1
        elif offset == 0:  # 0
            nindex = index

        if nindex not in range(len(self.data.dict['syllable'])):
            return None

        if self._is_pause(nindex):
            raise ValueError('syll0 is a pause or 2 pauses in a row')

        if maxdist:
            syll = self.data.dict['syllable'][index]
            nsyll = self.data.dict['syllable'][nindex]
            if syll.BeginValue-nsyll.EndValue > maxdist:
                return None # Does not overlap with the window from the left
            if nsyll.BeginValue-syll.EndValue > maxdist:
                return None # Does not overlap with the window from the right

        return nindex


    def calc_syll_styl_pitch(self, index):
        '''
        In: (int)
        Out: (list) Pitch values of a syllable
        '''
        # limit output to pitch values inside if self.data.dict['nuclei'] is present
        if self.data.dict.has_key('nuclei'):
            syll = self.get_syllable_nucleus(index)
            if syll is None: # use all syllable's values if nucleus is not detected
                syll = self.data.dict['syllable'][index]
        else:
            syll = self.data.dict['syllable'][index]
        pitch_values = [float(x.TextValue) for x in self.data.dict['pitch-styl']
                        if x.Time >= syll.Begin and x.Time <= syll.End]
        if pitch_values:
            return pitch_values
        else:
            return None


    def calc_syll_raw_pitch(self, index):
        '''
        In: (int)
        Out: (list) Pitch values of a syllable
        '''
        # limit output to pitch values inside if self.data.dict['nuclei'] is present
        if self.data.dict.has_key('nuclei'):
            syll = self.get_syllable_nucleus(index)
            if syll is None: # take all values if nucleus is not detected
                syll = self.data.dict['syllable'][index]
        else:
            syll = self.data.dict['syllable'][index]
        pitch_values = [float(x.TextValue) for x in self.data.dict['pitch-raw']
                        if x.Time >= syll.Begin and x.Time <= syll.End]
        if pitch_values:
            return pitch_values
        else:
            return None


    def get_syllable_nucleus(self, index):
        '''
        Voiced part of the syllable
        Out: (TimeInterval)
        '''
        if self.data.dict.has_key('nuclei'):
            raise Exception("Nuclei tier is not loaded.")
        syllable = self.data.dict['syllable'][index]
        nucl_ind = self.data.dict['nuclei'].Near(syllable.Begin,1)
        if nucl_ind > len(self.data.dict['nuclei'])-2:
            return None
        n0 = self.data.dict['nuclei'][nucl_ind]
        n1 = self.data.dict['nuclei'][nucl_ind+1]
        if n0.TextValue == n1.TextValue == 'a':
            nucleus = TimeInterval(n0.Begin, n1.End)
        elif n0.TextValue == 'a':
            nucleus = TimeInterval(n0.Begin, n0.End)
        elif n1.TextValue == 'a' and n1.Begin < syllable.End:
            nucleus = TimeInterval(n1.Begin, n1.End)
        else:
            #print 'No nucleus', index, syllable
            return None
        # Trim at syll boundaries
        if nucleus.Begin < syllable.Begin:
            nucleus.Begin = syllable.Begin
        if nucleus.End > syllable.End:
            nucleus.End = syllable.End
        return nucleus


    def _calc_avg_3first(self, s):
        '''
        In: list of numbers
        Out: (float) average over 3 first values
        '''
        if len(s) > 3:
            s = s[:3]
        return sum(s)/len(s)

    # # Maybe will work better for dur2 than the average of pause durations,
    # # because pauses' durations are too variable
    # def _calc_avg_syll_dur(self):
    #     '''
    #     Out: (float) Average syllable duration excluding pauses
    #     '''
    #     durations = []
    #     i = 0
    #     while i < len(self.data.dict['syllable']):
    #         if not is_pause(i, self.data.dict['syllable']):
    #             durations.append(self.data.dict['syllable'][i].Time.Duration())
    #         i += 1
    #     return sum(durations)/len(durations)



    # ========================[ I/O ]============================= #

    def write_csv(self, path, header=False):
        '''
        Write result to a simple comma-separated file.
        '''
        if self.extracted is None:
            raise Exception('First run extraction with "extract()"')

        data = []
        if header:
            if self.labels is None:
                raise
            data.append(self.labels)
        for row in self.extracted:
            row = ['?'
                   if x is None
                   else x
                   for x in row]
            data.append(row)
        da.write_csv(data, path)
        self._log.info('Written '+ path)
