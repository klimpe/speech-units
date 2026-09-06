#!/usr/bin/env python
import pickle
import os
import logging
import build_and_eval as be
import arffik
import subprocess


# Logger config
log_path = '/Users/klimpeshkov/work/ml/predict/predicting.log'
logfmt = ('%(asctime)s [%(levelname)s] %(filename)s:'
          '%(funcName)s():L%(lineno)d: %(message)s')
logging.basicConfig(level=logging.DEBUG,
                    format = logfmt, datefmt="%H:%M:%S", filename=log_path)
_log = logging.getLogger(__name__)


def main():
    _log.info('=' * 20+' New launch ' + '=' * 20)
    # Script parameters
    speaker = 14 # 14 for SR, speaker for whom we want em preditions generated
    class_label = 'du'
    classifier = 'trees.ADTree'
    fset_patt = r'p[dps]\d\d?$|s[bcd]\d$|lm\d$'
    fset_descr = 'P S LM'
    # Input path
    features='/Users/klimpeshkov/work/ml/data/features/du/v4/du_v4.arff' # path to ARFF
    outdir_full = '/Users/klimpeshkov/work/ml/predict/try3/full'
    outdir_np = '/Users/klimpeshkov/work/ml/predict/try3/nopause'
    print '----- FULL -----'
    predict(speaker, class_label, classifier, fset_patt, fset_descr,
            feat_path=features, outdir=outdir_full, nopause=False)
    print '----- NO PAUSE -----'
    predict(speaker, class_label, classifier, fset_patt, fset_descr,
            feat_path=features, outdir=outdir_np, nopause=True)


def predict(speaker, class_label, classifier, fset_patt, fset_descr,
            feat_path, outdir, nopause=False):
    '''
    Train model on all but one speakers and generate preditions

    creates 'intermediate' directory in outdir
    === In ===
    speaker (int)
    classifier (str)
    fset_patt (str or compiled regex)
    fset_descr (str)
    feat_path (str) path to the arff containing full feature set
    outdir (str) path directory for intermediate files (filtered arffs)
    model_path (str) path for saving the model (.model)
    predict_path (str) path for saving predictions
    no_pause (str default False)
        filter out units immediately before pauses
    '''
    namebase = '{0}_{1}'.format(classifier, prep_filename(fset_descr))
    if nopause:
        namebase += '_nopause'
    fset = be.prepare_fsets(class_label, [(fset_descr,fset_patt)])[0]
    fset.append('speaker')
    _log.info('Fset: ' + ' '.join(fset))

    # 1. Load data
    arffdata = arffik.read_arff(feat_path)
    data = arffdata['data']

    # 2. Apply filters
    _log.info('==== Creating filtered ARFFs... ====')
    fdir = be.make_interm_dir(outdir)

    filt_path = be.apply_filters(data, fset, fset_descr, fdir,
                                 nopause=nopause, relname=arffdata['relation'])

    # 3. Load filtered data
    data = arffik.read_arff(filt_path)['data']

    # 4. Separate traininig and test and write
    #    and remove 'speaker' column
    train = data[data.speaker!=speaker]
    test = data[data.speaker==speaker]
    train = train.drop('speaker', 1)
    test = test.drop('speaker', 1)

    bdir = be.make_interm_dir(outdir)
    train_path = os.path.join(bdir, 'train.arff')
    test_path = os.path.join(bdir, 'test.arff')

    arffik.write_arff(train, train_path)
    arffik.write_arff(test, test_path)

    # 5. Build model
    _log.info('==== Building model ====')

    model_path = os.path.join(bdir, namebase + '.model')
    be.build_and_eval(train_path, classifier, class_label, model_path=model_path)

    # 6. Predict using generated models
    _log.info('==== Predicting using generated model ====')

    pred_path = os.path.join(bdir, namebase + '.txt')
    # -p 1-39 to include all features in prediction output
    command = ['java', '-Xmx3g',
               'weka.classifiers.trees.ADTree','-i', '-l', model_path, '-T',
               test_path, '-p', '0']
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, err = p.communicate()
    if output:
        with open(pred_path, 'w') as pred_file:
            pred_file.write(output)
        _log.info('Predictions written to ' + pred_file)
    if err: raise Exception(err)



def prep_filename(s):
    '''
    Convert string to a valid filename
    '''
    return "".join([x if x.isalnum() else "_" for x in s])


if __name__ == '__main__':
    main()