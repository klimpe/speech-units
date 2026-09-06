# -*- coding : utf-8 -*-
# WindowDiff metrics : evaluation of the divergence of segmentations
# (Pevzner et Hearst 2002)


# import sys
# sys.path.append('../')
# import annotationdata

from nltk_windowdiff import windowdiff
from segmentools import tierutil


def eval_windowdiff_time(gold, algo, discretize='unit', step=0.01,
                         return_k=False, k='auto', verbose=False):
    """
    Calculates WindowDiff for two segmentations,
    represented as TextGrid tiers.

    === In ===
    gold : annotationdata.tier.Tier
    algo : annotationdata.tier.Tier
    discretize : {'unit', 'time'}
    step : float
        quantization step in seconds
    k : float or 'auto'   defalut 'auto'
        Window length (in seconds). If float, sets value of k manually,
        if 'auto', k is calculated based on gold tier boundaries.
    return_k : bool  defalut False
        when set to True, the function returns a tuple,
        where the second element is k (window length)
    
    === Out ===
    float or tuple
    """
    # if not (isinstance(gold, Tier)
    #         or isinstance(algo, Tier)):
    #     raise TypeError
    # if verbose:
    #     print 'WindowDiff of {} against {} with step {}'.format(
    #         algo.Name, gold.Name, step)
    # print  'algo duree =',algo[-1].maxTime - algo[0].minTime,
    #     '\ngold duree =' ,gold[-1].maxTime - gold[0].minTime
    if len(algo) == 0 or len(gold) == 0:
        raise ValueError('Empty segmentation')
    if k == 'auto':
        k = calc_k_time(gold, step)
        if verbose:
            print 'k = 1/2 of average gold unit = {} secs = {} steps'.format(
                step*k, k)
    elif type(k) in ('int','float'):
        if verbose: print 'manual k'
    else:
        raise TypeError
    wd = apply_wd_time(algo, gold, step, k)
    if return_k:
        return wd, k*step
    return wd

def eval_windowdiff_unit(algo, gold, reference,
                         return_k=False, k='auto', verbose=False):
    if k == 'auto':
        k = calc_k_unit(gold, reference)
        if verbose:
            print 'k = 1/2 of average gold unit = {}'.format(k)
    elif type(k) in ('int','float'):
        if verbose:
            print 'manual k'
    else:
        raise TypeError(k)
    wd = apply_wd_unit(algo, gold, reference, k)
    if return_k:
        return wd, k
    return wd

    
def calc_k_time(tier, step):
    """
    Calculates window as half the average interval
    length from an interval or point tier.
    returned length is in steps (sic!)
    """
    end_time = tier[-1].GetLocation().GetEndMidpoint()
    totDur =  end_time - tier[0].GetLocation().GetBeginMidpoint()
    meanDur = (totDur / float(len(tier)))
    meanSteps = meanDur / step
    k = int(round(meanSteps / 2))
    # print ('calcul de "k":',tier.name,'('+str(len(tier))+' segments)',\
    # 'mean_dur:',mean_dur,'mean_steps:',mean_steps)
    return k


def calc_k_unit(tier, reference):
    """
    Calculates window as half the average interval
    length from an interval or point tier.
    returned length is in steps (sic!)
    """
    lengths = []
    for unit in tier:
        ref_units = tierutil.units_of_interval(reference,
                                               unit.GetLocation().GetBeginMidpoint(),
                                               unit.GetLocation().GetEndMidpoint())
        length = len(ref_units)
        lengths.append(length)
    mean_length = sum(lengths)/len(lengths)
    return int(round(mean_length / 2.))


def apply_wd_time(algo, gold, step, k):
    ba = discretize_by_time(algo, step)
    bg = discretize_by_time(gold, step)
    ba, bg = equalize(ba, bg, step)
    wd = windowdiff(ba, bg, k)
    wd = wd / float(len(ba)) # scale
    return wd


def apply_wd_unit(algo, gold, reference, k):
    ba = discretize_by_reference_units(algo, reference)
    bg = discretize_by_reference_units(gold, reference)
    # equalize?
    wd = windowdiff(ba, bg, k)
    wd = wd / float(len(ba))
    return wd


def discretize_by_time(tier, step):
    """
    === In ===
    tier : annotationdata.tier.Tier
    step : int
        in seconds
    === Out ===
    list
    """
    tier_end = tier[-1].GetLocation().GetEndMidpoint()
    res = ['0'] * int(round(tier_end / step))
    # generate empty 
    for interval in tier:
        index = int(interval.GetLocation().GetEndMidpoint() / step)
        try:
            res[index] = '1'
        except IndexError:
            pass
    return ''.join(res)


def discretize_by_reference_units(tier, reference):
    """
    If after the reference unit
    there is a boundary of the main interval, it is coded with '1',
    if there is no boundary, with '0'

    the resulting string must be of the same length
    as reference tier

    :param tier: annotationdata.tier.Tier
    :param reference: annotationdata.tier.Tier
        most likely, tokens
    :return: str
    """
    res = []
    for interval in tier:
        ref_units = tierutil.units_of_interval(reference,
                                               interval.GetLocation().GetBegin(),
                                               interval.GetLocation().GetEnd())
        if len(ref_units) == 0:
            raise ValueError(interval)
        res += ((len(ref_units)-1) * '0') + '1'
    return ''.join(res)


def equalize(a1, a2, step):
    if len(a1) > len(a2):
        print 'A > G : {} steps or {} seconds. Equalisation applied'.format(
            len(a1)-len(a2),(len(a1)-len(a2))*step)
        return a1[:len(a2)], a2
    elif len(a1) < len(a2):
        print 'G > A', len(a2)-len(a1), 'steps. Equalisation applied'
        return a1, a2[:len(a1)]
    elif len(a1) == len(a2):
        return a1, a2
