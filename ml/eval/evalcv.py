# coding: utf-8
import os
import sys
from copy import copy
import argparse
import logging
import logging.config
import re
import pandas as pd
import numpy as np
import pydot  # for saving trees
from scipy import sparse
from sklearn import feature_extraction
from sklearn import cross_validation
from sklearn import metrics

from sklearn.externals.six import StringIO   # for saving trees
from sklearn.tree import export_graphviz    # for saving trees

import classifiers as clfs

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)


FEATURE_ORDER = ['time', 'speaker',
                 'pd1', 'pd2', 'pd3', 'pd4', 'pd5', 'pd6', 'pd7', 'pd8',
                 'pp1', 'pp2', 'pp3', 'pp4', 'pp5', 'pp6', 'pp7', 'pp8',
                 'pp9','pp10', 'ps1', 'ps2', 'ps3', 'sb1', 'sc1', 'sc2',
                 'sc3', 'sc4', 'sc5', 'sc6', 'sc7', 'sc8', 'sd1', 'sd2',
                 'sd3', 'sd4', 'lm1', 'lm2', 'lm3', 'lm4', 'lm5', 'lt1',
                 'lt2', 'lt3', 'lt4', 'ap', 'ip', 'du']



def run_eval(data_path, target, fset_path, res_dir, classifiers,
             inipu=False, ltmincount=100):
    '''
    Run cross-validation evaluation for a list of feature subsets.

    Write evaluation results to file.
    === In ===
    fset_path : string
        Path to a csv file defining feature subsets with regexes.
    target : string  {'du', 'ip', 'ap'}
    data_path : string
        Path to the dataset in csv format.
    res_dir : string
        Path to directory where results sub-directory will be created.
    classifiers : list
        List of strings identifying classifier groups.
    inipu : bool default False
        Wheather to filter out instances corresponding to units situated
        right before IPU boundaries.
    ltminq : int default 100
        Minimum frequency a unigram or a bigram must have
        to be included in features.
    === Out ===

    '''
    print '='*20 + 'new launch' + '='*20
    fsets = read_fsets(fset_path)
    fsets = prepare_fsets(fsets) # regexes -> feature labels
    data = pd.read_csv(data_path, na_values='?')
    os.makedirs(res_dir)
    classifiers = clfs.list_classifiers(classifiers)
    for descr, clf in classifiers:
        print '\n\n=== Task: ' + descr + ' ==='
        name = os.path.split(res_dir)[1]
        cur_res_path = os.path.join(res_dir, descr + '_' + name + '.csv')
        scores = eval_fsets(clf, data, target, fsets, tree_path=cur_res_path,
                            inipu=inipu, ltmincount=ltmincount)
        scores_summary = format_scores(scores)
        scores_summary.to_csv(cur_res_path) # Write results
        # write classifier params
        with open(os.path.splitext(cur_res_path)[0] + '_params.txt', 'w') as fparam:
            fparam.write(str(clf))




def eval_fsets(clf, data, target, fsets, tree_path=None,
               cv=10, inipu=False, ltmincount=100):
    '''
    Cross-validate every feature set
    === In ===
    clf
        Classifier object
    data : pandas.DataFrame
    target : string
    fsets : 2d list
    tree_path : str default None
        Save tree as image file if path is specified
    ltminq : int default 100
        Minimum frequency a unigram or a bigram must have
        to be included in features.
    === Out ===
    Scores for each feature set
    '''
    all_scores = []
    print str(cv) + '-fold cross-validation'
    print 'only inside IPU?', inipu
    for fset in fsets.iteritems():
        scores, best_clf, featnames = eval_one(clf, data, fset, target, cv=cv,
                                               inipu=inipu, ltmincount=ltmincount)
        featlist = ''.join(fset[1])
        all_scores.append((fset[0], featlist, scores))
        # If tree, save tree graph as image
        if tree_path and hasattr(best_clf, 'tree_'):
            write_tree(best_clf, fset[0], tree_path, featnames)
    return all_scores



## Version using cross_val_score (=> returns only f1)
# def eval_one(data, fset, target):
#     '''
#     === In ===
#     data : pandas.DataFrame
#     === Out ===
#     pandas.DataFrame
#     '''
#     y = data[target]
#     y = np.nan_to_num(y)
#     X = subset_features(data, fset)
#     X = vectorize_strings(X) # NaNs are replaced during this step
#     print 'X', X.shape, 'y', y.shape
#     clf = tree.DecisionTreeClassifier()
#     # 10-fold cross validataion
#     scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring='f1')
#     return scores


def eval_one(clf, data, fset, target, cv=10, inipu=False, ltmincount=100):
    '''
    === In ===
    clf
    data : pandas.DataFrame
    fset : tuple
       (description, list_of_features)
    target
    cv : int
       Number of cross-validation folds
    inipu : bool
    ltmincount : int
    === Out ===
    pandas.DataFrame
    '''
    if inipu:
        data = apply_inipu(data)
    y = data[target]
    y = np.nan_to_num(y)
    X = subset_features(data, fset[1])
    X, featnames = vectorize_strings(X, mincount=ltmincount) # NaNs are replaced during this step

    X =  np.nan_to_num(X)

    print '\n', fset[0], ':', ' '.join(fset[1])
    print 'Features:{}, Instances:{}'.format(X.shape[1], X.shape[0])
    # 10-fold cross validataion
    #scores = cross_validation.cross_val_score(clf, X, y, cv=10, scoring='f1')
    scores, best_clf = cross_val_scores(clf, X, y, cv=cv)
    print 'f =', round(scores.f.mean(), 4), '+/-', round(scores.f.std()*2, 4)
    return scores, best_clf, featnames


def cross_val_scores(clf, X, y, cv=10, path=None):
    '''
    Compute the recall, precision and f-measure of a cross validation test
    for given classifier

    === In ==
    clf
        Classifier object
    X : array
        Features
    y : array
        Target classes
    cv : int
        Number of folds for cross-validation
    === Out ===
    2d list: three measures for every fold

    based on http://stackoverflow.com/questions/23339523/sklearn-cross-validation-with-multiple-scores
    '''
    # kfold = cross_validation.KFold(X.shape[0], cv, shuffle=True) # non-stratified k-fold
    kfold = cross_validation.StratifiedKFold(y, cv, shuffle=True)
    models = [] # List of fitted classifier objects for each fold
    column_labels = ['precision','recall', 'f', 'tp', 'fp', 'fn', 'tn']
    scores = pd.DataFrame(0, index=range(cv), columns=column_labels,
                          dtype=float)
    for fold, (train, test) in enumerate(kfold):
        clf = copy(clf)
        # Learn: fit model to the data
        clf.fit(X[train], y[train])
        models.append(clf)
        # Generate predictions for test data
        y_pred = clf.predict(X[test])
        # Evaluate:
        cm = metrics.confusion_matrix(y[test], y_pred)
        scores.tp[fold] = cm[1,1] / float(cm.sum())
        scores.fp[fold] = cm[0,1] / float(cm.sum())
        scores.fn[fold] = cm[1,0] / float(cm.sum())
        scores.tn[fold] = cm[0,0] / float(cm.sum())
        sc = calc_scores(cm[1,1], cm[0,1], cm[1,0], cm[0,0])
        scores.precision[fold] = sc[0]
        scores.recall[fold] = sc[1]
        scores.f[fold] = sc[2]

    # Write best classifiers tree as image
    # Classifier with the best f-score
    best_clf = models[scores.f.idxmax(axis=1)]
    return scores, best_clf


def calc_scores(tp, fp, fn, tn):
    '''
    Computes measures given a confusion matrix.
    '''
    try:
        precision = float(tp) / (tp + fp)
    except ZeroDivisionError:
        precision = 0
    try:
        recall = float(tp) / (tp + fn)
    except ZeroDivisionError:
        recall = 0
    try:
        fmeasure = 2 * (precision * recall) / (precision + recall)
    except ZeroDivisionError:
        fmeasure = 0
    return precision, recall, fmeasure


def vectorize_strings(d, mincount=100):
    '''
    === In ===
    d : pandas.DataFrame
    mincount : int
       Minimum number of string occurences
    === Out ===
    d where each string feature is replaced by a set of numeric features
    '''
    all_strfeat = ['lt1', 'lt2', 'lt3', 'lt4']
    strfeat = [x for x in all_strfeat if x in d.columns]
    featnames_all = d.columns
    if not strfeat:
        d = d.fillna(-1)
        d = d.values
        d =  np.nan_to_num(d) # not needed?
        return d, featnames_all

    # == Separate all string features from data ==
    dstr = d[strfeat]
    d = d.drop(strfeat, axis=1)
    d = d.fillna(-1)
    dstr = dstr.fillna('')

    # == Convert strings to many one-hot features ==
    dstr = dstr.to_dict('records')
    vzr = feature_extraction.DictVectorizer(sparse=True)
    dstr = vzr.fit_transform(dstr) # dstr is csr sparse matrix of one-hot features now

    # == Remove rare strings ==
    counts = np.ravel(dstr.sum(axis=0)) # sum column-wise
    print 'Before low fq stirng removal:', len(counts)
    hicount_index = []
    featnames_str = []
    for index, count in enumerate(counts):
        if count > mincount:
            hicount_index.append(index)
            featnames_str.append(vzr.feature_names_[index])
    dstr = dstr[:,hicount_index]
    print 'After:', dstr.shape[1]

    # == Recombine non-string and string features ==

    d = sparse.csr_matrix(d.values)
    print dstr.shape
    print d.shape
    if d.shape[1] == 0:
        d = dstr
        featnames = featnames_str
    else:
        d = sparse.hstack((d, dstr))
        featnames = list(featnames_all) + featnames_str
    d = d.toarray() # Sparse to dense
    msg = '{} string features converted to one-hot (mincount={}): {}'.format(
        len(strfeat), mincount, ' '.join(strfeat))
    print msg
    return d, featnames


def apply_inipu(data):
    '''
    === In ===
    data : pandas.DataFrame
    '''
    if 'ps1' in data.columns:
        _log.info('Filter out pauses')
        filtered = data[data.ps1 != 1]
        filtered = filtered.copy(deep=True)
        filtered.index = range(len(filtered))
        return filtered
    else:
        raise ValueError("Can't filter based on ps1 feature - it's missing")
    return data


def prepare_fsets(fsets):
    '''
    === In ===
    fsets (list of tuples)
        form: [(description, fset_pattern), ...]
    === Out ===
    ordered list of feature names for each feature fset
    '''
    descriptions = []
    label_sets = []
    for descr, pattern in fsets:
        labels = pattern_to_fset(pattern)
        label_sets.append(labels)
        descriptions.append(descr)
    return pd.Series(label_sets, index=descriptions)


def format_scores(scores):
    '''
    Create data frame with properly named columns summarizing scores
    '''
    row_names = []
    col_names = []
    for metric in scores[0][2]:
        col_names += [metric, metric+'-std', metric+'-min', metric+'-max']
    col_names = ['featlist'] + col_names
    data = []
    for descr, featlist, sc in scores:
        row_names.append(descr)
        row = [featlist]
        for metric in sc:
            row += [round(x, 5) for x in [sc[metric].mean(),
                                          sc[metric].std()*2,
                                          sc[metric].min(),
                                          sc[metric].max()]]
        data.append(row)
    return pd.DataFrame(data, index=row_names, columns=col_names)


def pattern_to_fset(pattern):
    '''
    === In ===
    pattern str
        regex pattern to match feature labels
    === Out ===
    list of features labels
    '''
    return [x for x in FEATURE_ORDER if re.match(pattern, x)]


def read_fsets(path):
    '''
    Read feature sets from file with two columns:
    - description
    - fset (Regex)
    '''
    fsdata = pd.read_table(path, sep=',', header=None, comment='#',
                           names=['description', 'pattern'])
    for i in range(len(fsdata.pattern)):
        patt = fsdata.pattern.irow(i).replace('$', '').strip()
        patt = patt.split('|')
        patt = '$|'.join(patt) + '$'
        fsdata.pattern.loc[i] = patt
    return zip(fsdata.description, fsdata.pattern)


def subset_features(d, fset):
    '''
    === In ===
    data (pandas.DataFrame)
    fset (list)
        What features to leave
    path (str)
        Path for writing filtered ARFF
    === Out ===
    pandas.DataFrame
    '''
    not_fset = set(d.columns) - set(fset)
    d = d.drop(not_fset, axis=1)
    return d


def write_tree(clf, descr, path, featnames):
    dot_data = StringIO()
    export_graphviz(clf, out_file=dot_data, feature_names=featnames)
    graph = pydot.graph_from_dot_data(dot_data.getvalue())
    path = ''.join(os.path.splitext(path)[0]) + '_' + descr + '.pdf'
    graph.write_pdf(path)
    print 'Written tree graph:' + path



def parse_arguments():
    aparser = argparse.ArgumentParser()
    aparser.add_argument('data', type=str, help='Training data CSV.')
    aparser.add_argument('target', type=str, help='Accepted values: {du, ap, ip}.')
    aparser.add_argument('fset', type=str, help='Path to list feature sets.')
    aparser.add_argument('result', type=str, help='Path for writing scores.')
    aparser.add_argument('name', type=str, help='Name of the experiment.')
    return aparser.parse_args()



# ======================================================================





if __name__ == '__main__':
    args = parse_arguments()
    score = run_eval(args.data, args.target, args.fset, args.result, args.name)
