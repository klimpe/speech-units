import os
import pickle
from glob import glob
from nltk import FreqDist


from tierutil import units_of_interval
from corpus import Corpus
import data_access as da
import annotationdata.io as adio

def load_corpus(which, savetmp=True):
    '''
    which : {"du", "pu"}
    '''
    if which.lower() == 'du':
        glob_patt = '/Users/klimpeshkov/work/data/stratCID/discourse/*.TextGrid'
        picklepath = './pickle/corpus_du.pickle'
    elif which.lower() == 'pu':
        glob_patt = '/Users/klimpeshkov/work/data/stratCID/prosody/*.TextGrid'
        picklepath = './pickle/corpus_pu.pickle'
    else:
        raise ValueError('"which" must be in {"du", "pu"}')

    if os.path.isfile(picklepath):
        try:
            crp = pickle.load(open(picklepath))
            print 'Loaded pickle', picklepath
            return crp
        except:
            print 'Faliure loading from pickle'
            pass


    # Load corpus
    crp = Corpus(glob(glob_patt)) # Units
    print 'Loading tokens, POS and chunks..'
    for i, group in enumerate(crp):
        spk = os.path.basename(crp.pathlist[i])[:2]
        print spk
        group.add(da.load_tokens(spk), tiername='tokens')
        group.add(da.load_chunks(spk, 'pos'), tiername='chunks-pos')
        group.add(da.load_chunks(spk, 'disf-cat'), tiername='chunks-disf-cat')
        group.add(da.load_chunks(spk, 'disf-cat'), tiername='chunks-disf-bool')
        group.add(load_pos(spk), tiername='pos')
    try:
        with open(picklepath, 'wb') as pfile:
            pickle.dump(crp, pfile, protocol=pickle.HIGHEST_PROTOCOL)
    except:
        print 'Could not write pickle'
    finally:
        print 'Pickle written:', picklepath
    return crp


def load_pos(speaker):
    PATH_POS = '/Users/klimpeshkov/work/data/cid/syntax/morphosyntax/{spk}_syntax_v3_1_utf8.TextGrid'
    path = PATH_POS.format(spk=speaker)
    tier = adio.read(path)[4]
    tier.Name = 'pos'
    return tier


def extract_dm(corp, unit_index):
    '''
    Extract first tokens of unit
    === In ===
    corp : Corpus
    '''
    initials = []
    finals = []
    lengths = []
    empty_count = 0
    single_count = 0
    pause_count = 0
    for i_g, group in enumerate(corp):
        print group.name, 'group', i_g, 'out of', len(corp), 
        token_tier = group.get_tier('token')
        unit_tier = group[unit_index]
        for i, unit in enumerate(unit_tier):
            if i % 100 == 0:
                print 'unit', i, 'out of', len(unit_tier)
            tokens = units_of_interval(
                token_tier,unit.GetBeginValue(), unit.GetEndValue())
            if tokens:
                if len(tokens) == 1:
                    if tokens[0].GetTextValue() in ('#', 'dummy'):
                        pause_count += 1
                        continue
                    single_count += 1
                initials.append(tokens[0].GetTextValue())
                finals.append(tokens[-1].GetTextValue())
                lengths.append(len(tokens))
            else:
                empty_count += 1
    print 'Empty:', empty_count, 'Single token in unit:', single_count, 'Pauses', pause_count
    return initials, finals, lengths


def synt_distrib(corp, dm, unit_index, synt_tier_name='pos', position='initial'):
    '''
    For each DM in the list,
    extract distribution of POS tags or Chunk for unit which contain given DM
    Units containing only one token are ignored.

    corp : corpus.Corpus
    dm : str
        'Discourse marker' - search for this string
    unit_index : int
        index of the unit tier (DU/IP/AP)
    synt_tier : str
        name of the syntactic tier (ex. 'pos', 'chunk-pos')
    position : {'initial', 'final'}
        every DM must be either in the start or in the end of the unt
    '''
    if position not in ('initial', 'final'):
        raise ValueError('"position" must be in {"initial", "final"}')
    result = []
    for g_i, group in enumerate(corp):
        print 'Group:', g_i, group.name
        token_tier = group.get_tier('token')
        synt_tier = group.get_tier(synt_tier_name)
        unit_tier = group[unit_index]
        for i, unit in enumerate(unit_tier):
            if i % 100 == 0: print 'unit', i, 'out of', len(unit_tier)                

            bounds = (unit.GetBeginValue(), unit.GetEndValue())
            tokens = units_of_interval(token_tier, bounds[0], bounds[1])
            if len(tokens) > 1:
                synt = False
                if position == 'initial':
                    if tokens[0].GetTextValue() == dm:
                        synt = units_of_interval(synt_tier, bounds[0], bounds[1])                        
                elif position == 'final':
                    if tokens[-1].GetTextValue() == dm:
                        synt = units_of_interval(synt_tier, bounds[0], bounds[1])
                if synt:
                    result.append([x.GetTextValue() for x in synt])
    return result


def calc_ratio(dlong, dshort):
    '''
    Ratio between short and long
    dshort, dlong : nltk.FreqDist
    '''
    ratios = {}
    for key in dlong:
        if key in dshort:
            ratios[key] = dlong[key]/float(dshort[key])
    ratios = sorted(ratios.items(), key=lambda x: x[-1], reverse=True)    
    return ratios