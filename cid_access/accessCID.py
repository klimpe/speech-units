import os
import annotationdata.io as adio

SPEAKERS = ['AB', 'AC', 'AG', 'AP', 'BX', 'CM', 'EB', 'IM',
            'LJ', 'LL', 'MB', 'MG', 'ML', 'NH', 'SR', 'YM']

DIR_TOKENS = '/Users/klimpeshkov/work/data/CID/PU_manual/PB_naive/tokens'
DIR_SYLLABLES = '/Users/klimpeshkov/work/data/CID/syllables'
DIR_PHONEMES = '/Users/klimpeshkov/work/data/CID/phonemes'

DIR_DU_NAIVE = '/Users/klimpeshkov/work/data/CID/DU_naive/'
DIR_DU_EXPERT = '/Users/klimpeshkov/work/data/CID/DU_expert/'

DIR_PU_NAIVE = '/Users/klimpeshkov/work/data/CID/PU_manual/PU_naive/'
DIR_PU_EXPERT = '/Users/klimpeshkov/work/data/CID/PU_manual/PU_expert/'

# NOTE: the two dictionaries below originally listed the initials of the
# real human annotators ("naive coders") who manually segmented each
# speaker's data. For this public release the initials have been replaced
# with pseudonyms (coder1, coder2, ...); the mapping of which coder worked
# on which speakers is preserved, but the real identities are not.

NAIVE_CODERS_DU = {'AB':['coder1', 'coder2'],
                   'AC':['coder3', 'coder4'],
                   'AG':['coder1', 'coder4', 'coder3'],
                   'AP':['coder5', 'coder2'],
                   'BX':['coder1', 'coder2'],
                   'CM':['coder1', 'coder2'],
                   'EB':['coder5', 'coder2'],
                   'IM':['coder1', 'coder4'],
                   'LJ':['coder5', 'coder2'],
                   'LL':['coder1', 'coder5', 'coder4', 'coder2'],
                   'MB':['coder3', 'coder4'],
                   'MG':['coder1', 'coder2'],
                   'ML':['coder1', 'coder4'],
                   'NH':['coder1', 'coder5', 'coder4', 'coder2'],
                   'SR':['coder5', 'coder2'],
                   'YM':['coder1', 'coder4', 'coder3']}

# # for NH and LL, corpus C
# NAIVE_CODERS_DU = {'NH':['coder5', 'coder4'],
#                    'LL':['coder5', 'coder4']}

NAIVE_CODERS_PU = {'AB':['coder1', 'coder2'],
                   'AC':['coder1', 'coder2'],
                   'AG':['coder3', 'coder1'],
                   'AP':['coder3', 'coder1'],
                   'BX':['coder4', 'coder2'],
                   'CM':['coder4', 'coder3'],
                   'EB':['coder1', 'coder2'],
                   'IM':['coder3', 'coder1'],
                   'LJ':['coder4', 'coder2'],
                   'LL':['coder1', 'coder2'],
                   'MB':['coder4', 'coder3'],
                   'MG':['coder3', 'coder1'],
                   'ML':['coder4', 'coder2'],
                   'NH':['coder4', 'coder3', 'coder2'],
                   'SR':['coder4', 'coder3'],
                   'YM':['coder4', 'coder2']}


def load_tokens(speaker):
    name = '{}_tokens.TextGrid'.format(speaker)
    path = os.path.join(DIR_TOKENS, name)
    tier = adio.read(path)[0]
    return tier    
    
def load_phonemes(speaker):
    name = '{}_phonemes.TextGrid'.format(speaker)
    path = os.path.join(DIR_PHONEMES, name)
    tier = adio.read(path)[0]
    return tier        

def load_syllables(speaker):
    name = '{}_syllables.TextGrid'.format(speaker)    
    path = os.path.join(DIR_SYLLABLES, name)
    tier = adio.read(path)[0]
    return tier

# ____DU___

def load_DU_expert(speaker):
    fname = '{}_LP_du.TextGrid'.format(speaker)
    tier = adio.read(os.path.join(DIR_DU_EXPERT, fname))[0]
    return tier


def load_DU_naive(speaker, coder):
    fname = '{}_{}_DU.TextGrid'.format(speaker, coder)
    tier = adio.read(os.path.join(DIR_DU_NAIVE, fname))[0]
    return tier
    
# ___PU___

def load_IP_naive(speaker, coder):
    path = os.path.join(DIR_PU_NAIVE,
                        '{}_PU_naive_{}.TextGrid'.format(speaker, coder))
    tier = adio.read(path)[0]
    return tier

def load_AP_naive(speaker, coder):
    path = os.path.join(DIR_PU_NAIVE,
                        '{}_PU_naive_{}.TextGrid'.format(speaker, coder))
    tier = adio.read(path)[1]
    return tier

def load_IP_expert(speaker, coder):
    path = os.path.join(DIR_PU_EXPERT,
                        '{}_{}_expert_PU_realigned.TextGrid'.format(speaker, coder))
    tier = adio.read(path)[0]
    return tier

def load_AP_expert(speaker, coder):
    path = os.path.join(DIR_PU_EXPERT,
                        '{}_{}_expert_pu_realigned.TextGrid'.format(speaker, coder))
    tier = adio.read(path)[1]
    return tier

