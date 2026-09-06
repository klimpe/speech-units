import segmentools

orig = segmentools.aio.read(
    '/Users/wasser/work/segmentools/examples/testdata/pu_exp1.TextGrid')[0]
ref = segmentools.aio.read(
    '/Users/wasser/work/segmentools/examples/testdata/tokens.TextGrid')[0]

dam_pu = segmentools.DamGroup(ref, orig)
# dam_pu.damaged.generate_batch('shift', (1, 100, 10),
#                               shift_max_a=2,
#                               verbose=True)
print '1. damaging'
dam_pu.damaged.generate_batch('shift', (1, 100, 10),
                              shift_max_a=1,
                              verbose=True)

print '2. evaluating BS'
dam_pu.eval_boundary_similarity()
print '3. evaluating WD'
dam_pu.eval_windowdiff()


print 'BS:'
print dam_pu.damaged[0].list_results('boundary_similarity')
print 'kappa:'
print dam_pu.damaged[0].list_results('windowdiff')

dam_pu.damaged[0].write_csv('dampu.csv')
