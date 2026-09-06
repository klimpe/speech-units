"""
Utility functions for tiers (annotationdata.tier.Tier)
"""
from copy import deepcopy
from copy import copy
from matplotlib import pyplot as plt
# import matplotlib
# import random
from annotationdata.annotation import Annotation
from annotationdata.tier import Tier
from annotationdata.label.label import Label
from annotationdata.ptime.interval import TimeInterval
from annotationdata.ptime.point import TimePoint
from annotationdata.transcription import Transcription


def concat(a, b, verbose=False):
    """
    === In ===
    a : Tier
    b : Tier
    === Out ===
    """
    count = 0
    c = deepcopy(a)
    for annot in b:
        if annot.GetBegin() >= a.GetEnd():
            c.Add(annot)
            count += 1
    if verbose or count != len(b):
        print 'Concatenated', count, 'intervals from', len(b)
    return c


def split(tier, time):
    """
    Splits the 'tier' into to parts on the specified 'time'.
    Cuts through Annotation object if needed.

    In:
        tier - Tier
        time - float or TimePoint
    Out: tuple of two Tiers
    """
    # remove intervals from the beginning
    while tier.GetBegin() < time:
        last = tier.Pop(0)
    # fill if removed too much
    tier_start = tier.GetBegin()
    if tier_start > time:
        annot = Annotation(
            TimeInterval(TimePoint(time), TimePoint(tier_start)),
            last.Text)
        tier.Add(annot)


def trim_left(tier, time, copy=False):
    """
    Create a copy of a tier shortened from the beginning

    === In ===
    tier : Tier
    time : float
        new end time, before this time all data is removed
    === Out ===
    Tier
    """
    if copy:
        tier = deepcopy(tier)
    if time >= tier.GetEnd() or time < tier.GetBegin():
        raise ValueError("Cannot trim: value of 'time' is outside the range")
    if not tier.IsInterval():
        raise ValueError('Only interval tiers please')
    # 1. Remove intervals from the beginning.
    while tier.GetBegin() < time:
        last_removed = tier.Pop(0)
    # 2. Shorten and put back last deleted if removed too much.
    if tier.IsInterval():
        tier_start = tier.GetBegin()
        if tier_start > time:
            annot = create_annotation(time, tier_start, last_removed.TextValue)
            tier.Add(annot)
    if copy:
        return tier


def trim_right(tier, time, copy=False):
    """
    Create a copy of a tier shortened from the end

    === In ===
    tier : tier
    time : float
        after this time all data is removed
    copy : bool default True
        return a modified copy or modify in-place and return None
    === Out ===
    Tier
    """
    if copy:
        tier = deepcopy(tier)
    if time >= tier.GetEnd() or time < tier.GetBegin():
        raise ValueError("Cannot trim: value of 'time' is outside the range")
    if not tier.IsInterval():
        raise ValueError('Only interval tiers please')

    # 1. Remove intervals from the end.
    while tier.GetEnd() > time:
        last_removed = tier.Pop(-1)
    # 2. Shorten and put back last deleted if removed too much.
    if tier.IsInterval():
        tier_end = tier.GetEnd()
        if tier_end < time:
            annot = create_annotation(tier_end, time, last_removed.GetLabel().GetValue())
            tier.Add(annot)
    if copy:
        return tier


# def adjust_start(tier, time):
#     """
#     Move the first boundary of a tier to the desired time.
#
#     In:
#         tier tier,
#         'time': everything before this time is removed
#     Out:
#         tier (Tier)
#     Errors:
#         ValueError: when 'time' is after the end
#     """
#
#     if time >= tier.GetEnd():
#         raise ValueError("Cannot cut at/after tier\'s end")
#     # Case 1 'time' is after the  boundary
#     #          => lengthen the first interval
#     if time < tier[0].GetBeginValue():
#         tier = tier.Copy()
#         tier[0].SetBeginValue(time)
#     # Case 2: 'time' is a boundary
#     index = tier.Lindex(time)
#     if index != -1:
#         tier = create_tier(tier[index:])
#         return tier
#     # Case 3: 'time' is inside an interval
#     index = tier.Near(time)
#     tier = create_tier(tier[index:])
#     tier[0].SetBeginValue(time)
#     return tier
#
#
# def adjust_end(tier, time):
#     """
#     Move the last boundary of a tier to the desired time, removing
#     segments if necessary.
#
#     In:
#         tier (Tier)
#         time (float) new end time
#     Out:
#         tier (Tier)
#     Errors:
#         ValueError: when 'time' is before the beginning
#     """
#     if time <= tier.GetBegin():
#         raise ValueError("Cannot cut at/before tier's start")
#     # Case 1: 'time' is after the last boundary
#     #          => lengthen the last interval
#     if time > tier[-1].GetEndValue():
#         tier = tier.Copy()
#         tier[-1].SetEndValue(time)
#         return tier
#     # Case 2: 'time' falls on a boundary between segments
#     index = tier.Lindex(time)
#     if index != -1:
#         print 'on bound'
#         tier = create_tier(tier[:index])
#         return tier
#     # Case 3: 'time' is inside an interval
#     index = tier.Near(time)
#     tier = create_tier(tier[:index])
#     tier[-1].SetEndValue(time)
#     return tier
#

def create_tier(seq=None, name=None):
    """
    Convert a sequence of Annotations to a Tier

    == In ==
    seq : an iterable
      Sequence of Annotation instances
    name : string
    == Out ==
    annotationdata.tier.Tier

    """
    tier = Tier()
    if seq is not None:
        for annot in seq:
            tier.Add(annot)
    if name is not None:
        tier.SetName(name)
    return tier


def create_annotation(start, end=None, label=''):
    """
    Create an annotationdata.annotation.Annotation object

    In:
        start (float)
        end (float)
        label (str)
    Out:
        (annotationdata.annotation.Annotation)
    """
    label = Label(label)
    if not isinstance(start, TimePoint):
        start = TimePoint(start)
    if not isinstance(end, TimePoint):
        end = TimePoint(end)
    # Point annotation
    if end is None:
        annot = Annotation(start, label)
        return annot
    # Interval annotation
    interval = TimeInterval(start, end)
    annot = Annotation(interval, label)
    return annot


def create_transcription(tiers):
    transcr = Transcription()
    for tier in tiers:
        transcr.Add(tier)
    return transcr

    # if time >= tier.GetEnd() or time < tier.GetBegin():
    #     return None
    # # remove end intervals
    # while tier.GetEnd() > time:
    #     last = tier.Pop(-1)
    # if tier.IsInterval():
    #     # fill
    #     tier_end = tier.GetEnd()
    #     if tier_end < time:
    #         annot = Annotation(
    #             TimeInterval(TimePoint(tier_end), TimePoint(time)),
    #             last.Text)
    #         tier.Add(annot)

    # ==Another way==
    # # index of the first interval to remove
    # index = tier.Mindex(time, 1)
    # border_annot = tier[index]
    # tier.Remove(border_annot.End, tier[-1].End) # not working
    # if time < border_annot.End:
    #     border_annot.EndValue = time


def boundary_insert(tier, t, left_text=None, right_text=None):
    """
    Insert a boundary at given time if it does not exist.
    Modifies the segmentation in-place.
    Insertion of a boundary is equivalent to splitting an interval.

    :param tier: annotationdata.tier.Tier
        segmentation that will be shuffled
    :param t:
        time for insertion
    :param left_text:
    :param right_text:
    :return: bool
        success or not
    """
    # Check if there's already a boudary at this location
    occupied = [x for x in tier if x.GetLocation().GetEnd() == t]
    if occupied:
        return False
    i = 0
    while i < len(tier) and tier[i].GetLocation().GetBegin() < t:
        if i == len(tier) - 1:
            print 'No interval containing t=', t
            return False
        i += 1

    old = tier.Pop(i-1)
    if not left_text and not right_text:
        old_text = old.GetLabel().GetValue()
        left_text = old_text
        right_text = old_text

    new_left = Annotation(
        TimeInterval(old.GetLocation().GetBegin(), TimePoint(t)),
        Label(left_text))
    new_right = Annotation(
        TimeInterval(TimePoint(t), old.GetLocation().GetEnd()),
        Label(right_text))
    tier.Add(new_left)
    tier.Add(new_right)
    return True


def boundary_remove(tier, t):
    """
    Removes boundary at a given time by merging two segments.
    Modifies tier in-place.
    The label is taken from the left segment, the right label is
    discarded.

    :param tier: tier to modify
    :param t: location of the boundary to remove (seconds)
    :return: None
    """
    i = 0
    while i < len(tier)-2 and t_end != t:
        t_end = tier[i].GetLocation().GetEndMidpoint()
        i += 1
    unit_left = tier.Pop(i)
    unit_right = tier.Pop(i)
    new = Annotation(
        TimeInterval(unit_left.GetLocation().GetBegin(),
                     unit_right.GetLocation().GetEnd()),
        unit_left.GetLabel())
    tier.Add(new)


def boundary_shift(tier, reference, index, a, skip=''):
    """
    Shifts right boundary of a unit 'a' reference units
    to the right by resizing two adjacent intervals.

    :param tier: Tier
    :param reference: Tier
    :param index: index of a unit in 'tier'
    :param a: amplitude of the shift in reference units
    :param skip: str
       skip if one of the reference units in the affected interval
       contains this text (usually pauses)
    :return: bool
        True if success
    """
    if index + 2 > len(tier):
        # last segment > don't shift
        return False
    main_left = tier[index]
    main_right = tier[index + 1]
    main_left_start = main_left.GetLocation().GetBegin()
    main_right_end = main_right.GetLocation().GetEnd()
    old_t = main_left.GetLocation().GetEnd()
    ref_unit_index = reference.Lindex(old_t)
    if ref_unit_index == -1 or (ref_unit_index + a - 1) > len(reference)-1:
        return False
    ref_unit = reference[ref_unit_index + a - 1]
    new_t = ref_unit.GetLocation().GetEnd()
    limit = main_right.GetLocation().GetEnd()

    if skip:
        refs = units_of_interval(reference, main_left_start, main_right_end)
        ref_labs = [x.GetLabel().GetValue() for x in refs]
        if skip in ref_labs:
            return False
    if new_t >= limit:
        return False  # no space on the right

    # remove & recreate both units with the middle boundary at 'new_t'
    label_left = main_left.GetLabel().GetValue()
    label_right = main_right.GetLabel().GetValue()

    tier.Pop(index)
    tier.Pop(index)
    new_left_unit = create_annotation(main_left_start, new_t, label=label_left)
    new_right_unit = create_annotation(new_t, main_right_end, label=label_right)
    tier.Add(new_left_unit)
    tier.Add(new_right_unit)
    return True


def units_of_interval(tier, start, end):
    """
    Returns full Annotations belonging to a given interval.

    In:
      tier (Tier)
      start (float): start of the time interval, seconds
      end (float): end of the time interval, seconds
    Out:
      (list)
    """
    units = [x for x in tier
             if x.GetLocation().GetBeginMidpoint() >= start
             and x.GetLocation().GetEndMidpoint() <= end]
    return units


def stats_label_distrib(tier):
    """
    :return: tuple of three lists - Label, Count, Durations
    """
    label_items = [x.GetLabel().GetValue() for x in tier]
    label_list = sorted(set(label_items))
    count_list = []
    duration_list = []
    for label in label_list:
        count = 0
        i = 0
        duration_cat = []
        while i < len(label_items):
            if label_items[i] == label:
                count += 1
                dur = tier[i].GetLocation().GetDuration()
                duration_cat.append(dur)
            i += 1
        count_list.append(count)
        duration_list.append(duration_cat)
    return label_list, count_list, duration_list


# def units_untill_end(ind_t1, t1, t2):
#     """
#     Count how many intervals of the first tier are there
#     before the end of the corresponding interval of the second tier.
#     (i.e. makes sence when units in t2 are larger, otherwise)
#     """
#     # Count the number of intervals in the 1st tier
#     # between the beginning of the correspoinding interval of the second tier
#     i1 = t1[ind_t1]
#     i2 =


# def contains(tmin, tmax, tier):
#     """
#     === In ===
#     === Out ===
#     int : Index of
#     """
#     tier.


def print_annot(annot):
    if annot.IsInterval:
        print '\t'.join([str(annot.GetBeginValue()),
                         str(annot.GetEndValue()),
                         '"'+annot.GetTextValue()+'"'])
    elif annot.IsPoint():
        print '\t'.join([str(annot.GetEndValue()), annot.GetTextValue()])


def search_regex(tier, patts, index=False, verbose=False):
    """
    Iterative search regex search in tier's labels
    === In ===
    tier : annotationdata.tier.Tier
    patts : list
    index : bool
        If True, return indices instead of Annotation instances
    === Out ===
    list
        List of annotation objects matching one of the regexes.
    """
    pos_list = []
    annot_list = []
    pos = 0  # position
    while pos < len(tier):
        pos = tier.Search(copy(patts), function='regexp',
                            pos=pos, forward=True, reverse=False)
        if pos == -1:
            break
        pos_list.append(pos)
        annot_list.append(tier[pos])
        pos += 1
    if verbose:
        if len(pos_list) == 0:
            print 'No match (patterns: {})'.format(','.join(patts))
        else:
            print len(pos_list), 'matches'
            text_list = [a.GetLabel().GetValue() for a in annot_list]
            print 'Unique:', len(set(text_list))
    if index:
        return pos_list
    return annot_list
