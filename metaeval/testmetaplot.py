import metaeval_plot as mp 

INDIR = "/Users/wasser/work/segmentools_apply/metaeval_results/ip(1,66)"


reload(mp)
pl = mp.Plotter(INDIR)
wd = pl.group_by_method('windowdiff_time')
wdi = wd['insert']
pl.plot_compare_methods('windowdiff_time', write_dir='/Users/wasser/Desktop/')


