import time


def series2tuples(ser):
    res = []
    N = ser.size
    for i, v in zip(list(ser.index.values), ser.tolist()):
        res.append((i, v))
    return res


def datetime_short():
    dt = time.localtime()
    return '{}{:02}{:02}_{:02}{:02}{:02}'.format(
        dt.tm_year,
        dt.tm_mon,
        dt.tm_mday,
        dt.tm_hour,
        dt.tm_min,
        dt.tm_sec)
