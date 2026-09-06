#!/usr/bin/env python

import csv
import annotationdata.io as adio

from annotationdata.transcription import Transcription
from annotationdata.tier import Tier
from annotationdata.annotation import Annotation
from annotationdata.ptime.interval import TimeInterval
from annotationdata.ptime.point import TimePoint 
from annotationdata.label.label import Label

import data_access as da


fname = 'data/output/du/SR_DUv3_predictions.tx'
outpath = 'predictions/SR_DUv3_predictions.TextGrid'
lines = list(csv.reader(open(fname)))

tier_tokens = da.load_tokens('SR')
tier_du = da.load_DU('C', 'SR')
#tier_ipu = da.load_IPU('SR')

outtier = Tier('DUpredict')
for line in lines:
    prediction = int(line[-3])
#    tmin = float(line[-5])
    tmax = float(line[-4])
    prob = line[-1]
    if prediction:
        outtier.Add(Annotation(TimePoint(tmax),Label(prob)))
    
outgrid = Transcription()
#outgrid.Add(tier_ipu)
outgrid.Add(tier_tokens)
outgrid.Add(tier_du)
outgrid.Add(outtier)
adio.write(outpath, outgrid)