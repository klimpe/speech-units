#!/usr/bin/env python
import os
import logging
import build_and_eval as be
import arffik
import subprocess


log_path = '/Users/klimpeshkov/work/ml/predict/predicting.log'

# Logger config
logfmt = ('%(asctime)s [%(levelname)s] %(filename)s:'
          '%(funcName)s():L%(lineno)d: %(message)s')
logging.basicConfig(level=logging.DEBUG,
                    format = logfmt, datefmt="%H:%M:%S", filename=log_path)
_log = logging.getLogger(__name__)


# Script parameters
speaker_index = 14 # 14 for SR, speaker for whom we want em preditions generated
classifier = 'trees.ADTree'
subset_patt = r'p[dps]\d\d?$|s[bcd]\d$|lm\d$'
subset_descr = 'P S LM'

# Input path
features='/Users/klimpeshkov/work/ml/data/features/du/v4/du_v4.arff' # path to ARFF

# Output paths
intermdir = '/Users/klimpeshkov/work/ml/predict/try2'
model_path = os.path.join(intermdir, 'models/trees.ADTree_P_S_LM_noSR.model')
model_np_path = os.path.join(intermdir, 'models/trees.ADTree_P_S_LM_noSR_np.model')
predictions_path = os.path.join(intermdir, 'predictSR.txt')
predictions_np_path = os.path.join(intermdir, 'predictSR_np.txt')



# 1. Load data
subset = be.prepare_subsets('du', [(subset_descr,subset_patt)])[0]
print subset
arffdata = arffik.read_arff(features)
relname = arffdata['relation']
data = arffdata['data']


# 2. Separate traininig and test
train = data[data.speaker!=14]
test = data[data.speaker==14]


# 3. Filter corpus
# with pauses
idir = be.make_interm_dir(intermdir)
train_filt_path = be.apply_filters(data, subset, subset_descr, idir,
                                   nopause=False, relname=relname)
print 'Training filtered path:', train_filt_path
idir = be.make_interm_dir(intermdir)
test_filt_path = be.apply_filters(data, subset, subset_descr, idir,
                                  nopause=False, relname=relname)
print 'Test filtered path:', test_filt_path
# 'in IPU'
idir = be.make_interm_dir(intermdir)
train_filt_np_path = be.apply_filters(data, subset, subset_descr, idir,
                                      nopause=True, relname=relname+'-nopause')
print 'Training filtered inIPU path:', train_filt_np_path
idir = be.make_interm_dir(intermdir)
test_filt_np_path = be.apply_filters(data, subset, subset_descr, idir,
                                     nopause=True, relname=relname+'-nopause')
print 'Test filtered inIPU path:', test_filt_np_path

# 4. Build models
print '---- Build models ----'
# w/pauses
be.build_and_eval(train_filt_path, classifier, 'du', model_path=model_path)
# w/o pauses
be.build_and_eval(train_filt_path, classifier, 'du', model_path=model_np_path)


# 5. Predict using generated models
print '---- Predict using generated model ----'
# w/pauses
# -p 1-39 to include all features in prediction output
command = ['java', '-Xmx3g',
           'weka.classifiers.trees.ADTree','-i', '-l', model_path, '-T',
           test_filt_path, '-p', '0']
p = subprocess.Popen(command, stdout=subprocess.PIPE)
output, err = p.communicate()
if output:
    with open(predictions_path, 'w') as pred_file:
        pred_file.write(output)
_log.info('Written predictions' + predictions_path)
if err: _log.warning(err)   

# w/o pauses
command = ['java', '-Xmx3g',
           'weka.classifiers.trees.ADTree','-i', '-l', model_np_path, '-T',
           test_filt_np_path, '-p', '0']
print ' '.join(command)
p = subprocess.Popen(command, stdout=subprocess.PIPE)

output, err = p.communicate()
if output:
    with open(predictions_np_path, 'w') as pred_file:
        pred_file.write(output)
_log.info('Written predictions' + predictions_np_path)
if err: _log.warning(err)   
