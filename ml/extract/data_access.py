# built-in
import os
import pickle
import logging
import codecs
import re
import copy as cp

# 3d party
from numpy import nan
import arff
import annotationdata.io as adio
# project
import groupsegm as gs
import tierutil

_log = logging.getLogger(__name__)

LOCAL_DATA = '/Users/klimpeshkov/work/ML/data/'

# PATH_* and PATT_* are strings formatted for usage with str.format method

#PATH_PU = '/Users/klimpeshkov/work/data/stratCID/prosody800ms2/{corp}_{spk}_PU.TextGrid'
PATH_PU = '/Users/klimpeshkov/work/data/stratCID/prosody/{spk}_PU.TextGrid'
PATH_DU = '/Users/klimpeshkov/work/data/stratCID/discourse/{spk}_du_strat.TextGrid'
PATH_SYLLABLES = os.path.join(LOCAL_DATA, 'syllable', '{spk}_syllables.TextGrid') # syll Robert
PATH_TOKENS = os.path.join(LOCAL_DATA, 'tokens', '{spk}_tokens.TextGrid') # from Syntax v3.1
PATH_CHUNKS = '/Users/klimpeshkov/work/chunk_french/res_v2.2/{spk}_chunks.TextGrid'
PATH_IPU = '/Users/klimpeshkov/work/data/CID/IPU_transcription/{spk}_transcription.TextGrid'
PATH_NUCLEI = os.path.join(LOCAL_DATA, 'pitch', '{phonsegm}', '{spk}_nucl.TextGrid')
PATH_PITCH_RAW = os.path.join(LOCAL_DATA, 'pitch', 'raw', '{spk}.PitchTier')
PATH_PITCH_STYL = os.path.join(LOCAL_DATA, 'pitch', '{phonsegm}', '{spk}_styl.PitchTier')
PATH_NARRATIVES = '/Users/klimpeshkov/work/data/CID/narratives/{spk}_narrative.TextGrid'
PATH_DISFLUENCY = '/Users/klimpeshkov/work/data/CID/disfluency/LRE/gold/{}-gold06.TextGrid'


#DIR_TOKENS = '/Users/klimpeshkov/work/data/CID/tokens/'
#DIR_TOKENS = '/Users/klimpeshkov/work/chunk_french/res_v2.2/'
#DIR_TOKENS = '/Users/klimpeshkov/work/data/CID/syntax/morphosyntax/'

# Pickled 2D lists: pitch values grouped by syllables
DIR_INTERM_PITCH_RAW = os.path.join(LOCAL_DATA, 'intermediate/pitch/raw')
DIR_INTERM_PITCH_STYL = os.path.join(LOCAL_DATA, 'intermediate/pitch/styl')
# Pickled GroupSegm objects
DIR_INTERM_GROUPS_DU = os.path.join(LOCAL_DATA, 'intermediate/DU/groups')
DIR_INTERM_GROUPS_PU = os.path.join(LOCAL_DATA, 'intermediate/PU/groups')

DIR_INTERM_GRIDS_DU = os.path.join(LOCAL_DATA, 'intermediate/DU/groups/grids')
DIR_INTERM_GRIDS_PU = os.path.join(LOCAL_DATA, 'intermediate/PU/groups/grids')
DIR_INTERM_EXTRACTOR_DU = os.path.join(LOCAL_DATA, 'intermediate/DU/extractor')
DIR_INTERM_EXTRACTOR_PU = os.path.join(LOCAL_DATA, 'intermediate/PU/extractor')


PATT_INTERM_GROUP_DU = '{}_dugroup.pickle'
PATT_INTERM_GROUP_PU = '{}_pugroup.pickle'
PATT_INTERM_GRID_DU = '{}_dugroup.TextGrid'
PATT_INTERM_GRID_PU = '{}_pugroup.TextGrid'
PATT_INTERM_PITCH_RAW = '{}_syll_pitch_raw.pickle'
PATT_INTERM_PITCH_STYL = '{}_syll_pitch_styl.pickle'
PATT_INTERM_EXTRACTOR_DU = '{}_duextractor.pickle'
PATT_INTERM_EXTRACTOR_PU = '{}_puextractor.pickle'


SPEAKERS = ['AB', 'AC', 'AG', 'AP',
            'BX', 'CM', 'EB', 'IM',
            'LJ', 'LL', 'MB', 'MG',
            'ML', 'NH', 'SR', 'YM']


# Speakers of stratified reference corpus (v800): 12 speakers
SPEAKERS_PU = ['AB', 'AG', 'BX', 'CM', 'EB', 'LJ',
               'LL', 'MB', 'ML', 'NH', 'SR', 'YM']
SPEAKERS_PU = {'A':['AB', 'CM'],
               'B':['EB', 'SR'],
               'C':['NH'],
               'D':['AB', 'AC', 'AG', 'AP', 'BX',
                    'EB', 'IM', 'LJ', 'MB', 'MG',
                    'ML', 'SR', 'YM']}

SPEAKERS_DU = {'A':['LL', 'NH'],
               'B':['AG', 'YM'],
               'C':['AB', 'AC', 'AG', 'AP',
                    'BX', 'CM', 'EB', 'IM',
                    'LJ', 'LL', 'MB', 'MG',
                    'ML', 'NH', 'SR', 'YM']}

STOP_TIMES_EXPERT_PU = {'EB':260.58, 'SR':262.102}
PHONSEGMS = ['auto', 'phon', 'syll', 'phonsyll', 'phonsyll_rhyme']

def load_syllables(speaker):
    path = PATH_SYLLABLES.format(spk=speaker)
    tier = adio.read(path)[0]
    tier.Name = 'syllable'
    return tier

def load_nuclei(speaker, phonsegm):
    path = PATH_NUCLEI.format(spk=speaker, phonsegm=phonsegm)
    tier = adio.read(path)[6]
    tier.Name = 'nuclei'
    return tier


def load_pitch_raw(speaker):
    path = PATH_PITCH_RAW.format(spk=speaker)
    tier = adio.read(path)[0]
    tier.Name = 'pitch-raw'
    return tier


def load_pitch_styl(speaker, phonsegm):
    path = PATH_PITCH_STYL.format(spk=speaker, phonsegm=phonsegm)
    tier = adio.read(path)[0]
    tier.Name = 'pitch-styl'
    return tier


def load_ip(speaker):
    '''Out: annotationdata.tier.Tier'''
    # if corpus not in SPEAKERS_PU.keys():
    #     raise ValueError('No such corpus:' + corpus)
    # if speaker not in SPEAKERS_PU[corpus]:
    #     msg = 'No such speaker ({}) in corpus {}'
    #     raise ValueError(msg.format(corpus, speaker))
    path = PATH_PU.format(spk=speaker)
    tier = adio.read(path)[0]
    tier.Name = 'ip'
    return tier


def load_ap(speaker):
    # if corpus not in SPEAKERS_PU.keys():
    #     raise ValueError('No such corpus:' + corpus)
    # if speaker not in SPEAKERS_PU[corpus]:
    #     msg = 'No such speaker ({spk}) in corpus {corp}'
    #     raise ValueError(msg.format(corp=corpus, spk=speaker))
    path = PATH_PU.format(spk=speaker)
    tier = adio.read(path)[1]
    tier.Name = 'ap'    
    return tier


def load_chunks(speaker, which):
    '''
    In:
    speaker (str)
    which - 'pos', 'disf-cat', 'disf-bool'
      - chunk's POS-category
      - chunk disfluence category
      - chunks disfluence boolean
    Out: tier
    '''
    path = PATH_CHUNKS.format(spk=speaker)
    tiers = adio.read(path)[5:]
    if which == 'pos':
        tier = tiers[0]
    elif which == 'disf-cat':
        tier = tiers[1]
    elif which == 'disf-bool':
        tier = tiers[2]
    else:
        raise ValueError('Wrong value of "which"')
    tier.Name = 'chunk-' + which
    return tier


def load_du(speaker):
    '''
    === In ===
    speaker (str)
    === Out ===
    annotationdata.tier.Tier
    '''
    # if corpus not in SPEAKERS_DU.keys():
    #     raise ValueError('No such corpus:' + str(corpus))
    # if speaker not in SPEAKERS_DU[corpus]:
    #     msg = 'No such speaker ({spk}) in corpus {corp}'
    #     raise ValueError(msg.format(corp=corpus, spk=speaker))
    path = PATH_DU.format(spk=speaker)
    tier = adio.read(path)[0]
    tier.Name = 'du'
    return tier

def load_tokens(speaker):
    path = PATH_TOKENS.format(spk=speaker)
    tier = adio.read(path)[0]
    tier.Name = 'token'
    return tier


def load_narratives(speaker):
    path = PATH_NARRATIVES.format(spk=speaker)
    tier = adio.read(path)[0]
    tier.Name = 'narrative'
    return tier


def load_ipu(speaker):
    path = PATH_IPU.format(spk=speaker)
    tier = adio.read(path)[0]
    tier.Name = 'transcript'
    return tier


def load_disf(speaker):
    path = PATH_DISFLUENCY.format(speaker)
    print path
    tier = adio.read(path)[0]
    tier.Name = 'disfluency'
    return tier
    

# ___________________ Intermediate data IO __________________



#              ___ Intermediate data : Groups ----

# def load_interm_group_du(speaker):
#     fname = PATT_INTERM_GROUP_DU.format(speaker)
#     path = os.path.join(DIR_INTERM_GROUPS_DU, fname)
#     if not os.path.isfile(path):
#         _log.debug('Intermediate DU group not found: '+path)
#         return None
#     with open(path) as f:
#         group = pickle.load(f)
#     return group


# def load_interm_group_pu(speaker):
#     fname = PATT_INTERM_GROUP_PU.format(speaker)
#     path = os.path.join(DIR_INTERM_GROUPS_PU, fname)
#     if not os.path.isfile(path):
#         _log.debug('Intermediate PU group not found: '+path)
#         return None
#     with open(path) as f:
#         group = pickle.load(f)
#     return group

def load_interm_pitch_raw(speaker):
    '''
    Raw pitch values for each syllable.
    (Not every syllable has any pitch points).
    Out: 2D list, len() == len(syllable_tier)
    '''
    fname = PATT_INTERM_PITCH_RAW.format(speaker)
    path = os.path.join(DIR_INTERM_PITCH_RAW, fname)
    if not os.path.isfile(path):
        _log.debug('Raw pitch not found at "{}"'.format(path))
        return None
    with open(path) as f:
        pitch = pickle.load(f)
    _log.debug('Loaded raw pitch from "{}"'.format(path))
    return pitch



def write_interm_pitch_raw(data, speaker):
    '''
    Write intermediate data: raw pitch values grouped by syllable.
    Write data silently overwriting if path exists.
    In: 2D list
    '''
    fname = PATT_INTERM_PITCH_RAW.format(speaker)
    path = os.path.join(DIR_INTERM_PITCH_RAW, fname)
    overwritten = ''
    if os.path.isfile(path):
        overwritten = '(OVERWRITTEN) '
    with open(path, 'w') as f:
        pickle.dump(data, f)
        _log.info('Written ' + overwritten + path)



def load_interm_pitch_styl(speaker):
    '''
    Stylized pitch values for each syllable.
    (Not every syllable has any pitch points).
    Out: 2D list, len() == len(syllable_tier)
    '''
    fname = PATT_INTERM_PITCH_STYL.format(speaker)
    path = os.path.join(DIR_INTERM_PITCH_STYL, fname)
    if not os.path.isfile(path):
        _log.debug('Stylized pitch not found at "{}"'.format(path))
        return None
    with open(path) as f:
        pitch = pickle.load(f)
    _log.debug('Loaded stylized pitch from "{}"'.format(path))
    return pitch

    

# def load_interm_extractor_du(speaker):
#     '''
#     Out: FeatureExtractor object
#     '''
#     fname = PATT_INTERM_EXTRACTOR_DU.format(speaker)
#     path = os.path.join(DIR_INTERM_EXTRACTOR_DU, fname)
#     if not os.path.isfile(path):
#         _log.debug('Extractor DU not found: '+path)
#         return None
#     with open(path) as f:
#         pitch = pickle.load(f)
#     return pitch


# def load_interm_extractor_ip(corpus, speaker):
#     '''
#     In:
#       corpus (str) possible values: 'A', 'B', 'C'
#       speaker (str)
#     Out: FeatureExtractor object
#     '''
#     fname = PATT_INTERM_EXTRACTOR_PU.format(speaker)
#     path = os.path.join(DIR_INTERM_EXTRACTOR_PU, fname)
#     if not os.path.isfile(path):
#         _log.debug('Extractor PU not found: ' + path)
#         return None
#     with open(path) as f:
#         pitch = pickle.load(f)
#     return pitch


# def write_interm_group_du(group, speaker):
#     fname = PATT_INTERM_GROUP_DU.format(speaker)
#     path = os.path.join(DIR_INTERM_GROUPS_DU, fname)
#     if not os.path.isfile(path):
#         with open(path, 'w') as f:
#             pickle.dump(group, f)
#         _log.info('Intermediate: DU group written to '+path)


# def write_interm_group_pu(group, speaker):
#     print type(group)
#     for x in group: print(type(x))
#     fname = PATT_INTERM_GROUP_PU.format(speaker)
#     path = os.path.join(DIR_INTERM_GROUPS_PU, fname)
#     if not os.path.isfile(path):
#         with open(path, 'w') as f:
#             pickle.dump(group, f)
#         _log.info('Intermediate: PU group written to '+path)


def write_interm_pitch_styl(data, speaker):
    '''
    In: 2D list
    '''
    fname = PATT_INTERM_PITCH_STYL.format(speaker)
    path = os.path.join(DIR_INTERM_PITCH_STYL, fname)
    overwritten = ''
    if os.path.isfile(path):
        overwritten = '(OVERWRITTEN) '
    with open(path, 'w') as f:
        pickle.dump(data, f)
        _log.info('Written ' + overwritten + path)


def write_interm_grid_du(group, speaker):
    fname = PATT_INTERM_GRID_DU.format(speaker)
    path = os.path.join(DIR_INTERM_GRIDS_DU, fname)
    if not os.path.isfile(path):
        group.write(path)
        _log.info('Intermediate: DU TextGrid written to '+path)


def write_interm_grid_pu(group, speaker):
    fname = PATT_INTERM_GRID_PU.format(speaker)
    path = os.path.join(DIR_INTERM_GRIDS_PU, fname)
    if not os.path.isfile(path):
        group.write(path)
        _log.info('PU TextGrid written to '+path)


def write_interm_extractor_du(extractor, speaker):
    '''
    In: extractor -  FeatureExtractor object
        speaker (str)
    '''
    fname = PATT_INTERM_EXTRACTOR_DU.format(speaker)
    path = os.path.join(DIR_INTERM_EXTRACTOR_DU, fname)
    if not os.path.isfile(path):
        with open(path, 'w') as f:
            pickle.dump(extractor, f)
        _log.info('Extractor DU written to '+path)


def write_interm_extractor_pu(extractor, speaker):
    '''
    In: extractor -  FeatureExtractor object
        speaker (str)
    '''
    fname = PATT_INTERM_EXTRACTOR_PU.format(speaker)
    path = os.path.join(DIR_INTERM_EXTRACTOR_PU, fname)
    if not os.path.isfile(path):
        with open(path, 'w') as f:
            pickle.dump(extractor, f)
        _log.info('Extractor PU written to ' + path)


# def _test(index):
#     speaker = 'AB'
#     ab_syll = load_syllables(speaker)
#     ab_raw = load_pitch_raw(speaker)
#     ab_styl_list = []
#     for phonsegm in PHONSEGMS:
#         ab_styl_list.append(load_pitch_styl(speaker, phonsegm))

#     i = 0
#     print ab_syll[index].TextValue
#     print 'raw', syll_pitch(index, ab_syll, ab_raw)
#     while i < len(ab_styl_list):
#         print phonsegms[i], syll_pitch(1, ab_syll, ab_styl_list[i])
#         i+=1


def write_csv(data, path):
    '''
    Write rows to a simple comma-separated file.
    In:
      data - 2d list. level 1: rows, level 2: cells
      path (string) -  path for CSV output
    Out: None
    '''
    with codecs.open(path, mode='w', encoding='utf-8') as _file:
        for row in data:
            # Quote string values
            row1 = []
            for cell in row:
                # value is int/floating point number
                if isinstance(cell, float) or isinstance(cell, int):
                    row1.append(unicode(cell))
                else:
                    row1.append(u'"{}"'.format(cell))
            # Insert separator
            line = ','.join(row1) + '\n'
            # Write
            _file.write(line)


def load_extractor_group(speaker, du=False, pu=False,
                         phonsegm='phonsyll', nuclei=False):
    '''
    === In ===
    speaker : string
        cf. SPEAKERS
    du : boolean
        Include annotation of DU boundaries    
    pu : boolean
        Include annotation of PU boundaries
    phonsegm - 'phonsyll', '', ...  If False, nuclei are not loaded.
    nuclei (bool) - load nuclei tier
	=== Out ===
    groupsegm.GroupSegm

    '''
    group = gs.GroupSegm()
    group.add(load_tokens(speaker))
    group.add(load_syllables(speaker))
    if pu:
        group.add(load_ip(speaker))
        group.add(load_ap(speaker))
    if du:
        group.add(load_du(speaker))
    group.equalize(modify=True)
    if nuclei:
        group.add(load_nuclei(speaker, phonsegm))
    group.add(load_pitch_raw(speaker))
    group.add(load_pitch_styl(speaker, phonsegm))
    group.add(load_chunks(speaker, 'pos'))
    group.add(load_chunks(speaker, 'disf-cat')) 
    group.add(load_chunks(speaker, 'disf-bool')) 
    group.add(load_disf(speaker))
    return group


# def preprocess_tokens(tier, onlycheck=False):
#     '''
#     If sequence of labels '[^#]+', '', '#' is detected,
#     the second interval is removed. Modifies the tier in-place.

#     In:
#       tier (Tier)
#       onlycheck (bool) Don't modify, only count
#     '''
#     itr = 0
#     to_remove = []
#     labels = [x.TextValue.strip() for x in tier]
#     print 'Empty intervals', labels.count('')
#     while itr < len(tier)-2:
#         if tier[itr].TextValue.strip() not in ('#', ''):
#             if tier[itr+1].TextValue.strip()=='':
#                 if tier[itr+2].TextValue.strip()=='#':
#                     to_remove.append(tier[itr].End)
#         itr += 1

#     print 'Before token preprocessing len(tokens):',len(tier)
#     print len(to_remove)
#     if not onlycheck:
#         for boundary in to_remove:
#             tierutil.boundary_remove(tier, boundary)
#     print 'After len(tokens):', len(tier)






def write_arff(data, path, relation='noname', copy=True):
    '''
    === In ===
    data : pandas.DataFrame
    
    path (str)

    === Out ===
    None
    '''
    if copy:
        data = cp.copy(data)
    # Get rid of endtime column
    data = data.drop('time', 1)

    # # None > NaN
    data = data.replace('None', nan)
    data = data.fillna(value=nan)
    
    attributes = []
    for label in data.keys():
        if label == 'speaker': #
            attributes.append((label,  [str(x) for x in range(16)]))
        elif feature_type(label) == 'binary':
            attributes.append((label, ['0','1']))
            # For binary features, replace NaNs  and string 'None' with 0.
            data[label] = data[label].fillna(0)
            data[label] = data[label].astype(int)
        elif feature_type(label) == 'string':
            attributes.append((label, 'STRING'))
        elif feature_type(label) == 'float':
            attributes.append((label, 'NUMERIC'))

    data = data.fillna('?')
    data = data.values.tolist()
    print data.values[:10]
    
    arffdata = {u'relation': relation,
               u'attributes': attributes,
               u'data': data}
    # return arffdata # debug
    with codecs.open(path, 'w', encoding='utf-8') as outfile:
        arff.dump(arffdata, outfile)


def feature_type(label):
    patterns = {'binary':r'pd7|pp[7-8]|ps1|sb1|sc[1-8]|sd[1-4]|lm[1-5]|ap|ip|du',
                'nominal':r'speaker',
                'string':r'lt[1-4]',
                'float':r'pd[1-68]|pp[1-69]|pp10|ps[23]'}
    for kind, patt in patterns.items():
        if re.match(patt, label):
            return kind

# def read_csv(path):
#     '''
#     Read a comma separated table
#     == In ==
#     path : str : Path to the csv file
#     == Out ==
#     list
#     '''
#     with open(path) as infile:
#         reader = csv.reader(infile)
#         data = pandas.DataFrame(reader)
#     return data
