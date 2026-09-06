#!/usr/bin/env python

import os
os.chdir('autoDU')
import launch_extractionDU as ledu
import annotationdata.io as adio


group = ledu.load_data('AB', 'C', 'phonsyll', 'intermediate_data')
group.reference_index = 1
group.realign_one(0)
group.write('AB-du-realigned.pickle')