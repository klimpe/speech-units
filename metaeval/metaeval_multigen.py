import os
import segmentools#     'examples/testdata/pu_exp1.TextGrid')[0]
# reference = segmentools.aio.read(
#     'examples/testdata/tokens.TextGrid')[0]



def main():
    tg = segmentools.aio.read('examples/testdata/ip10s.TextGrid')
    ref = tg[0]
    orig = tg[1]
    n = (0.5, 99, 0.1)
    out_dir = '/Users/wasser/Desktop/segmentools/metaeval_multi_10s'

    launch(ref, orig, out_dir, n)
    
    #original = segmentools.aio.read('examples/testdata/pu_exp1.TextGrid')[0]
    #reference = segmentools.aio.read('examples/testdata/tokens.TextGrid')[0]


def launch(reference, original, directory, n_range):
    damgroups = []
    for i in range(20):
        sub_dir = os.path.join(directory,'multi'+str(i))
        os.mkdir(sub_dir)
        print '************** ITERATION {} ***************'.format(i)
        damgroups.append(launch_one(reference, original, sub_dir, n_range))
    return damgroups


def launch_one(reference, original, directory, n_range):
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
    print '  PLOT: COMPARE METRICS'
    for b in pu:
        b.plot_compare_metrics(directory)
    print 'Writing textgrids'
    for batch in pu:
        batch.write_textgrid(directory)
    return pu


if __name__ == '__main__':
    main()


