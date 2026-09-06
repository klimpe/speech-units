import segmentools

orig = segmentools.aio.read(
    '/Users/wasser/work/segmentools/examples/testdata/pu_exp1.TextGrid')[0]
ref = segmentools.aio.read(
    '/Users/wasser/work/segmentools/examples/testdata/tokens.TextGrid')[0]

dam_pu = segmentools.DamGroup(ref, orig)
# dam_pu.damaged.generate_batch('shift', (1, 100, 10),
#                               shift_max_a=2,
#                               verbose=True)
dam_pu.damaged.generate_batch('insert', (1, 100, 10), verbose=True)
dam_pu.eval_kappa()
print dam_pu.damaged[0].eval_list('kappa')

dam_pu.plot_by_metric('kappa', '/Users/wasser/work/segmentools/kappaPU.pdf')
