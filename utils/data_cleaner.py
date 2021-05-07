import pandas as pd
import numpy as np
from scipy.stats import zscore


class DataCleaner:
    """
    IN PROGRESS(Outlier removal most likely unneeded for this particular dataset)

    give DataCleaner constructor a dataframe,
    and the methods will work with that dataframe
    """

    def __init__(self, dataframe=None):
        self.data = dataframe

    def update_data(self, dataframe):
        self.data = dataframe

    def retrieve_data(self):
        return self.data

    def remove_outliers(self, labels_to_ignore=[]):
        copy = self.data.drop(labels_to_ignore, axis=1)
        z = zscore(copy, nan_policy='omit')
        data_filter = (abs(z) < 2.5).all(axis=1)
        new = copy[data_filter]
        print(new)

        self.data.update({col : new[col] for col in self.data.columns if col not in labels_to_ignore})
        return self.data


if __name__ == "__main__":
    datacleaner = DataCleaner(pd.DataFrame([[1, 2], [3, 2], [8, 20], [3, 2], [2, 2], [2, 3], [2, 1], [1, 2]],
                                            columns=['label', 'label2']))
    print(datacleaner.retrieve_data())
    print(datacleaner.remove_outliers())
