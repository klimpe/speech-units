import segmentools


tg = segmentools.aio.read(
    '/Users/wasser/work/segmentools/examples/testdata/ip10s.TextGrid')
ref = tg[0]
orig = tg[1]


dam_pu = segmentools.DamGroup(ref, orig)

dam_pu.damaged.generate_batch('shift', (1, 101, 10), shift_max_a=5,
                              multi_a=False, verbose=True, skip='#')

dam_pu.damaged.generate_batch('insert', (1, 101, 10), verbose=True)
dam_pu.eval_kappa()
print dam_pu.damaged[0].list_results('kappa')

dam_pu.plot_by_metric('kappa', '/Users/wasser/work/segmentools/kappaPU.pdf')

#dam_pu.damaged.generate_batch('insert', (0, 100, 20), verbose=True)
#dam_pu.damaged.generate_batch('remove', (0, 100, 20), verbose=True)

#dam_pu.damaged[1].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/insert.TextGrid')
#dam_pu.damaged[2].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/remove.TextGrid')

