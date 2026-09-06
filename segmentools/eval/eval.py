"""
Metrics for segmentations

TODO: move everything into tierwd, tierpr etc.
so that file contains only imports
"""

import tierpr
import tierwd
import segeval
import kappatier

from nltk.metrics.agreement import AnnotationTask


from tierwd import eval_windowdiff_time
from tierwd import eval_windowdiff_unit


def eval_boundary_similarity_time(gold, hyp, step):
    gold = tierwd.discretize_by_time(gold, step)
    hyp = tierwd.discretize_by_time(hyp, step)
    gold = segeval.convert_nltk_to_masses(gold)
    hyp = segeval.convert_nltk_to_masses(hyp)
    res = segeval.boundary_similarity(hyp, gold)
    return res


def eval_boundary_similarity_unit(reference, gold, hyp):
    """
    :param reference: annotationdata.tier.Tier
        tier containing all possible boundaries
    :param gold: annotationdata.tier.Tier
    :param hyp: annotationdata.tier.Tier
    :return:
    """
    gold = tierwd.discretize_by_reference_units(gold, reference)
    hyp = tierwd.discretize_by_reference_units(hyp, reference)
    gold = segeval.convert_nltk_to_masses(gold)
    hyp = segeval.convert_nltk_to_masses(hyp)
    res = segeval.boundary_similarity(hyp, gold)
    return res


def eval_kappa(items):
    """
    Calculate kappa agreement statistic
    (multi-kappa if there are multiple coders)

    :param agreement: list
      tuples of form (annotator, item:int, boundary label:int or str)
    :return: float
    """
    task = AnnotationTask(data=items)
    return task.multi_kappa()


def eval_pi(items):
    """
    Calculate pi agreement statistic
    """
    task = AnnotationTask(data=items)
    return task.pi()


def eval_precision_recall_f1(tiers, pause_labels=('#', ''), delta=0):
    prf = dict()
    pr = tierpr.PrecisionRecall(tiers, pause_labels=pause_labels, delta=delta)
    prf['start'] = (pr.precision('start'), pr.recall('start'), pr.f1('start'))
    prf['end'] = (pr.precision('end'), pr.recall('end'), pr.f1('end'))
    prf['unit'] = (pr.precision('unit'), pr.recall('unit'), pr.f1('unit'))
    return prf


def eval_kappa_2(reference, gold, hypothesis):
    return kappatier.kappatier(gold, hypothesis, reference)


def convert_to_nltk_format(reference, tier, coder_label):
    """
    Boundary presence for every decision point (item),
    i.e. for every boundary in reference segmentation.

    TODO: upgrade to take labels into account = multiple categories

    In:
    :param reference: annotationdata.tier.Tier
      Segmentation containing all decision points
    :param tier: annotationdata.tier.Tier
    :param coder_label: int or str
      coder's or algorithm's label
    :return: list of tuples of form (annotator, item:int, agree:int{0,1})
    """
    res = []
    for item, ref_unit in enumerate(reference):
        decision_t = ref_unit.GetLocation().GetEnd()
        if tier.HasPoint(decision_t):
            res.append((coder_label, item, 1))
        else:
            res.append((coder_label, item, 0))
    return res
