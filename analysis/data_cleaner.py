import numpy as np
from scipy.stats import zscore
from random import sample


def remove_outliers(data, labels_to_ignore=[]):
    copy = data.drop(labels_to_ignore, axis=1)
    z = zscore(copy, nan_policy='omit')
    data_filter = (abs(z) < 2.5).all(axis=1)
    new = copy[data_filter]
    print(new)

    data.update({col : new[col] for col in data.columns if col not in labels_to_ignore})
    return data


def remove_bloated_range(datasets, min_for_removal, max_for_removal):
    """
    This function will remove the data that has responses within the range
    (min, max)
    """
    for i in range(len(datasets)):
        datasets[i] = list(filter(lambda x: x > max_for_removal or x < min_for_removal, datasets[i]))
        #  filter returns an iterator for a new sequence excluding all those in datasets that are within the range.
        #  converting filter to list turns the list we desire. This list is now shorter, though.
    return datasets


def normalize_size(datasets):
    """
    This function will take a list of datasets, and convert them all to the size
    of the smallest.
    """
    smallest_size = len(datasets[0])
    for dataset in datasets:
        if len(dataset) < smallest_size:
            smallest_size = len(dataset)
    deltas = np.zeros(len(datasets))
    for i, delta in enumerate(deltas):
        deltas[i] = len(datasets[i]) - smallest_size  # this is the amount that dataset[i] must lose
        datasets[i] = sample(datasets[i], smallest_size)

    return datasets
