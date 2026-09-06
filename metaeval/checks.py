import pandas as pd

def show_if_rises(path):
    """
    :param path: str
      csv file with evaluation of damaged copies
    :return: None
    """
    data = pd.read_csv(path, index_col=0)
    for col in data.columns:
        print col
        prev = 1
        for cur in data[col]:
            if cur > prev:
                print cur, cur-prev
            prev = cur
