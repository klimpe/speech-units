import segmentools


tg = segmentools.aio.read(
    '/Users/wasser/work/segmentools/examples/testdata/ip10s.TextGrid')
ref = tg[0]
orig = tg[1]


dam_pu = segmentools.DamGroup(ref, orig)

dam_pu.damaged.generate_batch('shift', (10, 100, 10), shift_max_a=5,
                              multi_a=False, verbose=True, skip='#')
#dam_pu.damaged.generate_batch('insert', (0, 100, 20), verbose=True)
#dam_pu.damaged.generate_batch('remove', (0, 100, 20), verbose=True)

dam_pu.damaged[0].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/short_shiftA1.TextGrid')
dam_pu.damaged[1].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/short_shiftA2.TextGrid')
dam_pu.damaged[2].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/short_shiftA3.TextGrid')
dam_pu.damaged[3].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/short_shiftA4.TextGrid')
dam_pu.damaged[4].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/short_shiftA5.TextGrid')
#dam_pu.damaged[1].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/insert.TextGrid')
#dam_pu.damaged[2].save_as_textgrid('/Users/wasser/work/segmentools/examples/testdata/remove.TextGrid')

