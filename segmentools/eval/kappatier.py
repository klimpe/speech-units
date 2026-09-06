# utilisation:
# a0 = textgrid.TextGridFromFile('x.TextGrid')[0]
# a1 = textgrid.TextGridFromFile('y.TextGrid')[0]
# t = textgrid.TextGridFromFile('token.TextGrid')[0]
# print kappaGrid(a0,a1,t)

import os
import re
import kappa


def kappatier(annot0, annot1, reference=None, verbose=False):
    '''
    'annot0' and 'annot1' are Interval or Point tiers
    'token' is Interval tier
    'multicat' multiple categories. works only for pointTiers
    '''
    data = convert_interval_tier(annot0, annot1, reference)
#    data = getData(annot0, annot1, reference, multicat)
    k = kappa.kappa(data, verbose=verbose)
    return k


def convert_point_tier(annot0, annot1, token=None, multipleCat=False):
    '''
    Convert annotations to a list of items,
    each represented by a list containing ratings
    by two annotators
    ex. [[0,0][0,1][1,1]...[0,0]]
    'annot0','annot1' - Point tiers
    'token' - Interval tier

    *TODO: adapt to the new textgrid library
    '''
    data = []
    if multipleCat: print 'PointTier, items from tokens, categories > 2'
    else: print 'PointTier, items from tokens, categories = 2'
    if token:
        i = 0
        for t in token:
            if t.mark not in '#+' and t.mark != 'dummy':
                if multipleCat:
                    k0 = pointLabel(annot0, t.maxTime) # category
                    k1 = pointLabel(annot1, t.maxTime)
                else:
                    # 1 if point exists in annot
                    k0 = len([p for p in annot0 if p.time == t.maxTime]) 
                    # 0 otherwise
                    k1 = len([p for p in annot1 if p.time == t.maxTime])
                data.append([k0, k1])
                i += 1
    else:
        print 'PointTier, no token, categories = 2'
        # no token tier => take union of boundaries in annotations
        bounds = [x.time for x in annot0] + [x.time for x in annot1] 
        bounds = list(set(bounds))
        bounds.sort()
        for b in bounds:
            k0 = len([x for x in annot0 if x.time == b])
            k1 = len([x for x in annot1 if x.time == b])
            data.append([k0, k1])
    return data
    
def convert_interval_tier(annot0, annot1, token=None):
    '''
    Convert annotations to a list of items,
    each represented by a list containing ratings
    by two annotators
    ex. [[0,0][0,1][1,1]...[0,0]]
    'annot0','annot1', 'token' - Interval tiers
    '''
    data = []
    if token:
        print 'IntervalTier, items, categories = 2'
        i = 0 # item
        for t in token:
            if t.TextValue not in '#+' and t.TextValue != 'dummy':
                #check existence of a boundary at t.maxTime
                k0 = len([x for x in annot0 if x.End == t.End]) 
                k1 = len([x for x in annot1 if x.End == t.End])
                data.append([k0, k1])
                i += 1
    else:
        print 'IntervalTier, no token, categories = 2'
        # union of boundaries in annotations
        bounds = [x.EndValue for x in annot0] + [x.EndValue for x in annot1] 
        bounds = list(set(bounds))
        bounds.sort()
        for b in bounds:
            k0 = len([x for x in annot0 if x.End == b])
            k1 = len([x for x in annot1 if x.End == b])
            data.append([k0, k1])
    return data
    
    
def pointLabel(tier, t):
    '''get mark of the point in the PointTier 'tier'
    for time 't'. If the point does not exist, returns 0.'''
    mark = [p.mark for p in tier if p.time == t]
    if len(mark) == 0: return 0
    if re.match(r'[1-3]', mark[0]): return int(mark[0])
    else:
        print 'ommited mark:', t, mark

        
    
def getData(a0, a1, t=None, multicat=False):
    if a0.__class__.__name__ and a1.__class__.__name__ == 'PointTier':
        data = convert_point_tier(a0, a1, t, multicat)
    elif a0.__class__.__name__ and a1.__class__.__name__ == 'IntervalTier':
        data = convert_interval_tier(a0, a1, t)
    else:
        raise ValueError
    return data


