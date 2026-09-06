#!/usr/bin/env python
import argparse
import csv
import re

ap = argparse.ArgumentParser()
ap.description = ('Merge prediction file and features in CSV format, outputs a CSV.'
                  'Four columns from predictions file are added: '
                  'predicted_class, error, pred_class_probability.')
ap.add_argument('predictions', type=str, help='File with Weka\'s predictions')
ap.add_argument('features', type=str, help='Path to CSV file with features')
ap.add_argument('output', type=str, help='Path for merged CSV')
args = ap.parse_args()


featlines = list(csv.reader(open(args.features)))
predfile = open(args.predictions)

predlines = []
patt = re.compile('\s+\d+\s+\d:\d\s+(\d):\d\s+(\+\s+)?(\d(\.\d+)?)')
for line in predfile:
    match = re.match(patt, line)
    if match:
        predline = list(match.groups())[:3]
        # Prepare error field
        if predline[1]:
            predline[1]=1
        else:
            predline[1]=0
        predline[0]=predline[0].replace('1', '0')
        predline[0]=predline[0].replace('2', '1')        
        predlines.append(predline)


if len(featlines) != len(predlines):
    raise ValueError('Features({}) and predictions({}) must contain the same '
                     'number of items.'.format(len(featlines),len(predlines)))

# Join lines and write out
outcsv = csv.writer(open(args.output,'w'))
for i in range(len(featlines)):
    line = featlines[i] + predlines[i]
    outcsv.writerow(line)
print args.output, 'written'