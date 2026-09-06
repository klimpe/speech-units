from __future__ import unicode_literals
import math
import pandas as pd
from nltk import FreqDist
import matplotlib.pyplot as plt
import matplotlib

import dmstats


def cutoff_dict(d, thres=10):
    '''
    Remove items from dictionnary, which values are lower than thres
    '''
    d1 = dict()
    for k,v in d.iteritems():
        if v > thres:
            d1[k] = v
    return d1


def get_points(shortunit, longunit):
    iniS = FreqDist(shortunit.init)
    iniL = FreqDist(longunit.init)
    finS = FreqDist(shortunit.fin)
    finL = FreqDist(longunit.fin)

    # - LDU-fin >10 **OR** LDU-ini > 10
    fqthres = 40
    leave_keys = []
    common_keys = set(iniL.keys()).intersection(finL.keys())
    for ck in common_keys:
        if finL[ck] > fqthres or iniL[ck] > fqthres:
            leave_keys.append(ck)

    init_r = dmstats.calc_ratio(iniL, iniS)
    fin_r = dmstats.calc_ratio(finL, finS)
    fin_r_dict = dict(fin_r)

    x = []
    y = []
    lab = []
    for key, val in init_r:
        if (key in fin_r_dict
                and key in leave_keys
                and not pd.isnull(key)
                and not key in ('#','+')):
            print key, type(key)
            x.append(math.log(val,2))
            y.append(math.log(fin_r_dict[key],2))
            lab.append(key)
    x,y,lab = zip(*sorted(zip(x,y,lab), key=lambda x: x[0]))

    # test
    for i in range(len(x)):
        print x[i], y[i], lab[i]
    print len(x)

    return x, y, lab


thres = 3 # length threshold Short/Long

DU = pd.read_csv('data/du_dm.csv', encoding='utf8')
DU_short = DU[DU.length <= thres]
DU_long = DU[DU.length > thres]

PU = pd.read_csv('data/pu_dm.csv', encoding='utf8')
PU_short = PU[PU.length <= thres]
PU_long = PU[PU.length > thres]

xDU, yDU, labDU = get_points(DU_short, DU_long)
xPU, yPU, labPU = get_points(PU_short, PU_long)

# Plotting
fig = plt.figure(dpi=600, figsize=(25,10))
ax = fig.add_subplot(111)

plt.plot(xDU,yDU, 'bo')
plt.plot(xPU,yPU, 'ro')

plt.grid(True,which="both",ls="-", alpha=0.2)
plt.xlabel('DM-Initial LS-ratio')
plt.ylabel('DM-Final LS-ratio')
# ax.set_xticks([1, 10, 20])
# ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
# ax.set_yticks([1, 10, 20])
# ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

#ax.set_ylim((0, 14))
#ax.set_xlim((0, 9.5))

for i,j,l in zip(xDU,yDU,labDU):
    ax.annotate(l,xy=(i+0.05,j+0.05), alpha=0.7)
for i,j,l in zip(xPU,yPU,labPU):
    ax.annotate(l,xy=(i+0.05,j+0.05), alpha=0.7)
plt.savefig('bothXY.png')
#plt.show()