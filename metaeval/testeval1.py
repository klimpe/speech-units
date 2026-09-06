import segmentools

orig = segmentools.aio.read(
    '/Users/wasser/work/segmentools/examples/testdata/pu_exp1.TextGrid')[0]

gs = segmentools.GroupSegm()
gs.load_textgrid('/Users/wasser/work/segmentools/examples/testdata/insert.TextGrid')
gs.reference_index=0
gs.eval_precision(subset=[1,2,3,4,5])

