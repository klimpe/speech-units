#!/usr/bin/env python
import os
# import argparse
import evalcv

PATH_PU = '/Users/klimpeshkov/work/ml/data/features/pu/v6/pu_v6bin.csv'
PATH_DU = '/Users/klimpeshkov/work/ml/data/features/du/v4/du_v4.csv'
FSET = '/Users/klimpeshkov/work/ml/eval/fsets/'
RESULT = '/Users/klimpeshkov/work/ml/eval/results/'

def run(fset, result, classifiers, which='du', ltmincount=100):
    '''
    === In ===
    fset : str
        feature set file name
    result : str
        result directory (to be created)
    classifiers : list
      List of strings identifying classifier groups.
      Available: log_lin, log_poly, dtree    
    which : {'du', 'ip', 'ap'}
        defines which data and which target to use
    inipu : bool default False
        Wheather to filter out instances corresponding to units situated
        right before IPU boundaries.
    ltminq : int default 100
        Minimum frequency a unigram or a bigram must have
        to be included in features.        
    === Out ===
    score summary as pd.DataFrame
    '''
    reload(evalcv)

    if which == 'du':
        path = PATH_DU
    elif which in ('ap', 'ip'):
        path = PATH_PU
    else:
        raise ValueError("which must be in {'du', 'ip', 'ap'}")
    target = which
    
    fset = os.path.join(FSET, fset)
    result_full = os.path.join(RESULT, result, 'full')
    result_inipu = os.path.join(RESULT, result, 'inipu')
    
    print '-'*20, 'full', '-'*20
    evalcv.run_eval(path, target, fset, result_full, classifiers, inipu=False, ltmincount=ltmincount)
    print '-'*20, 'inipu', '-'*20    
    evalcv.run_eval(path, target, fset, result_inipu, classifiers, inipu=True, ltmincount=ltmincount)


# def parse_arguments():
#     aparser = argparse.ArgumentParser()
#     aparser.add_argument('fset', type=str, help='feature set file name')
#     aparser.add_argument('result', type=str, help='result directory (to be created)')
#     return aparser.parse_args()


# if __name__ == '__main__':
#     args = parse_arguments()
#     run(args.fset, args.result)