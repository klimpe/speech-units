import segmentools
import os

#     'examples/testdata/pu_exp1.TextGrid')[0]
# reference = segmentools.aio.read(
#     'examples/testdata/tokens.TextGrid')[0]

orig = segmentools.aio.read('examples/testdata/pu_exp1.TextGrid')[0]
ref = segmentools.aio.read('examples/testdata/tokens.TextGrid')[0]

def main(subdir, n):
    # tg = segmentools.aio.read('examples/testdata/ip10s.TextGrid')
    # orig = tg[1]
    # ref = tg[0]
    

    #n = (0.5, 99, 0.5)
    root_dir = '/Users/wasser/Desktop/segmentools/metaeval_results/ip{}/'.format(str(n).replace(' ',''))
    if not os.path.isdir(root_dir):
        os.mkdir(root_dir)
    os.mkdir(subdir)
    pu = launch(ref, orig, n, os.path.join(root_dir,subdir))
    return pu

def launch(reference, original, n_range, directory):
    pu = segmentools.DamGroup(reference,original)
    print '=== INSERT ==='
    pu.generate_damaged_batch('insert', n_range, verbose=True)
    print '=== REMOVE ==='
    pu.generate_damaged_batch('remove', n_range, verbose=True)
    print '=== SHIFT ==='
    pu.generate_damaged_batch('shift', n_range, shift_max_a=5, multi_a=True, verbose=True)
    print '=== EVAL ==='
    pu.evaluate()
    print pu.methods
    print '=== WRITE CSVs ==='
    pu.write_csv(directory)
    print '  PLOT: COMPARE METHODS'
    pu.plot_compare_methods('windowdiff', directory)
    pu.plot_compare_methods('boundary_similarity', directory)
    pu.plot_compare_methods('kappa', directory)
    pu.plot_compare_methods('precision_start', directory)
    pu.plot_compare_methods('precision_end', directory)
    pu.plot_compare_methods('precision_unit', directory)
    pu.plot_compare_methods('recall_start', directory)
    pu.plot_compare_methods('recall_end', directory)
    pu.plot_compare_methods('recall_unit', directory)
    pu.plot_compare_methods('f1_start', directory)
    pu.plot_compare_methods('f1_end', directory)
    pu.plot_compare_methods('f1_unit', directory)
    

    print '  PLOT: COMPARE METRICS'
    for b in pu:
        b.plot_compare_metrics(directory)
    print 'Writing textgrids'
    for batch in pu:
        batch.write_textgrid(directory)
    return pu

if __name__ == '__main__':
    main()
