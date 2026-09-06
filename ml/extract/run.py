#!/usr/bin/env python
import logging
import logging.config
import os
#import groupsegm
import argparse
import data_access as da
import duextractor as due
import puextractor as pue


def launch_extraction(unit_type, outdir, version, speakers=None,
                      du=False, pu=False, featureset=None):
    """
    Extract from multiple speakers and write extracted data
    to individual and one joined CSV tables.

    === In ===
    unit_type : str
        Which type of units we extract features about:
        prosodic or discourse. The difference is that a training item
        will correspond either to a syllable or to a token respectively.
        Possible values: "PU", "DU"
    outdir : str
        Path to directory for CSV output
    version : str
        Used for naming output files.
        Name patterns:
          per speaker CSVs: {speaker}_{unit_type}_v{version}.csv
          joined CSV: {unit_type}_v{version}.csv
    speakers : list; optional; default None
        Possible values: cf. data_access.SPEAKERS
    du : bool; optional; default None
        Which stratum of DU annotations to use.
        If None => do not load DU annotations.
    pu : bool; optional; default False
        load AP and IP annotations
    featureset: list; default None
        If is None, all subsets are used.
        Possible values:
         - 'time', 'speaker'
         - prosody: 'PD', 'PP', 'PS'
         - syntax: 'SB', 'SC', 'SD',
         - (only for DU) lexics: 'LM', 'LT',
         - annotations: 'AP', 'IP', 'DU'

    === Out ===
    None

    """
    unit_type = unit_type.upper()
    if speakers is None:
        speakers = da.SPEAKERS
    
    fname_individ = '{speaker}'+'_{which}_v{version}.csv'.format(
        which=unit_type, version=version)
    fname_joined = '{which}_v{version}.csv'.format(which=unit_type, version=version)
    path_individ = os.path.join(outdir, fname_individ)
    path_joined = os.path.join(outdir, fname_joined)
    data = []

    for speaker in speakers:
        _log.info('Speaker: ' + speaker)
        # use kwargs  'phonsegm' and 'nuclei'
        group = da.load_extractor_group(speaker, du=du, pu=pu)
        if unit_type == 'du':
            extractor = due.DUExtractor(speaker, group)
        elif unit_type == 'pu':
            extractor = pue.PUExtractor(speaker, group)
        extractor.extract(subset=featureset)
        data.extend(extractor.extracted)
        extractor.write_csv(path_individ.format(speaker=speaker),
                            header=True)
    _log.info('Writing joined csv to ' + path_joined)
    da.write_csv([extractor.labels] + data, path_joined)


def parse_arguments():
    all_speakers = da.SPEAKERS
#    default_outdir = '/Users/klimpeshkov/work/ML/data/output/DU'
    parser = argparse.ArgumentParser()
    parser.description = 'Extract DU features and save CSVs'
    help_featsub = ("Feature subset list, separated with column (:). "
                    "Available subsets: 'time', 'speaker', "
                    "'PD', 'PP', 'PS', 'SB', 'SC', 'SD', "
                    "'AP', 'IP', 'DU', (only for DU): 'LM', 'LT'")
    help_stratum_du = 'Stratum of DU annotations'
    help_speakers = 'List of speakers.\nDefault: ' + ' '.join(all_speakers)
    help_outdir = 'Path for output.'
    parser.add_argument('which', type=str, help="'pu' or 'du'")
    parser.add_argument('version', type=str, help='Version of features')
    parser.add_argument('outdir',help=help_outdir)
    parser.add_argument('--feature_subset', help=help_featsub)
    parser.add_argument('--stratum_du', default=None, help=help_stratum_du)
    parser.add_argument('--pu', help='Include AP and IP annotations')
    parser.add_argument('speakers', metavar='S', type=str, nargs='*',
                         help=help_speakers, default=all_speakers)
    return parser.parse_args()

    
script_dir = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig(os.path.join(script_dir, 'logging-extract.ini'))
_log = logging.getLogger(__name__)

if __name__ == '__main__':
    args = parse_arguments() # testing stuff
    feature_subset = None
    if args.feature_subset:
        feature_subset = args.feature_subset.split(':')
    launch_extraction(args.which, args.speakers, args.outdir, args.version,
                      args.stratum_du, args.stratum_pu, feature_subset)
