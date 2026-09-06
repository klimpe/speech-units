"""
G
Examples:
metaeval(10, (1, 66, 5), 'test')

metaeval(10, (1, 66), 'ip')
metaeval(10, (1, 66), 'ap')
metaeval(10, (1, 66), 'du')

"""

import os
import segmentools

# tg = segmentools.aio.read('examples/testdata/ip10s.TextGrid')
# orig = tg[1]
# ref = tg[0]

METRICS = ['windowdiff_time', 'windowdiff_unit',
           'boundary_similarity_time', 'boundary_similarity_unit',
           'kappa',
           'precision_start', 'precision_end', 'precision_unit',
           'recall_start', 'recall_end', 'recall_unit',
           'f1_start', 'f1_end', 'f1_unit']


def metaeval(path, runs, n, unit, shift_max_a=5):
    """
    :param path: str
        Path to directory inside which result directory will be created
    :param runs: int
        Number of iterations (runs) of the whole evaluation
    :param n: tuple
        Range of n values (n_min, n_max[, n_step])
    :param unit: str
        Determines which tiers will be loaded.
        Values: {'ap', 'ip', 'du', 'test'}
    :return: None
    """
    result_dir = create_result_dir(path, unit, n)
    for run in range(runs):
        print 'Unit:{}, Run:{}'.format(unit.upper(), run)
        run_dir = os.path.join(result_dir, 'run' + str(run))
        os.mkdir(run_dir)
        metaeval_unit(run_dir, n, unit, shift_max_a=shift_max_a)


def metaeval_unit(run_dir, n, unit, shift_max_a):
    """
    Generate and evaluate perturbed copies
    for one of the tested unit types.

    :param path:
    :param run_dir:
    :param n:
    :param unit: str
        unit type (du, ap, ip) or 'test'
    :return: damgroup.DamGroup
    """
    ref, orig = load_tiers(unit)
    dg = geneval(ref, orig, n, run_dir, shift_max_a=shift_max_a)
    return dg


def geneval(reference, original, n, directory, shift_max_a=5):
    print 'Generating...'
    methods = ['remove', 'insert', 'shift']
    dg = segmentools.DamGroup(reference, original)
    for method in methods:
        dg.generate_damaged_batch(method, n,
                                  shift_max_a=shift_max_a,
                                  multi_a=True,
                                  verbose=True)
    print 'Writing TextGrids...'
    for batch in dg:
        batch.write_textgrid(directory)
    print 'Calculating metrics...'
    dg.evaluate()
    print 'Writing metrics to CSV'
    dg.write_csv(directory)
    print 'Plotting...'
    for metric in METRICS:
        dg.plot_compare_methods(metric, directory)
    for batch in dg:
        batch.plot_compare_metrics(directory)
    return dg


def create_result_dir(path, unit, n):
    result_dir = os.path.join(path, unit.lower() + str(n).replace(' ',''))
    if not os.path.isdir(result_dir):
        os.mkdir(result_dir)
        return result_dir
    else:
        raise OSError(result_dir + ' already exists')


def load_tiers(unit):
    if unit.lower() == 'du':
        return load_du()
    elif unit.lower() == 'ip':
        return load_ip()
    elif unit.lower() == 'ap':
        return load_ap()
    elif unit.lower() == 'test':
        return load_test()


# Data loading
def load_ap():
    ref = segmentools.aio.read('data/tokens.TextGrid')[0]
    orig = segmentools.aio.read('data/pu_exp1.TextGrid')[1]
    return ref, orig


def load_ip():
    ref = segmentools.aio.read('/Users/wasser/work/metaeval/data/tokens.TextGrid')[0]
    orig = segmentools.aio.read('/Users/wasser/work/metaeval/data/pu_exp1.TextGrid')[0]
    return ref, orig


def load_du():
    ref = segmentools.aio.read('/Users/wasser/work/metaeval/data/NH_tokens.TextGrid')[0]
    orig = segmentools.aio.read('/Users/wasser/work/metaeval/data/NH_LP_du.TextGrid')[0]
    return ref, orig


def load_test():
    """ip_300_second"""
    tg = segmentools.aio.read('/Users/wasser/work/metaeval/data/test/tokens_ip_300s.TextGrid')
    ref = tg[0]
    orig = tg[1]
    return ref, orig
