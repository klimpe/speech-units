import segmentools


orig = segmentools.aio.read(
    '/Users/wasser/work/segmentools/examples/testdata/pu_exp1.TextGrid')[0]
ref = segmentools.aio.read(
    '/Users/wasser/work/segmentools/examples/testdata/tokens.TextGrid')[0]

dam_pu = segmentools.DamGroup(ref, orig)

dam_pu.damaged.generate_batch('shift', (1, 100, 10),
                              shift_max_a=2,
                              verbose=True)
#dam_pu.damaged.generate_batch('insert', (0, 100, 20), verbose=True)
#dam_pu.damaged.generate_batch('remove', (0, 100, 20), verbose=True)

dam_pu.damaged[0].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/shift1a1.TextGrid')
dam_pu.damaged[1].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/shift1a2.TextGrid')
#dam_pu.damaged[1].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/insert.TextGrid')
#dam_pu.damaged[2].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/remove.TextGrid')

