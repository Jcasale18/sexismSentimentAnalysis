import matplotlib.pyplot as plt
import TwitterAnalysis
import numpy as np
import data_cleaner
keys = []


def parse_data(dataframe):
    """
    Dataframe looks like:
        label1  label2  label3  ...
        trial1    0.4     0.4   ...
        trial2    0.6     0.1   ...
           .       .       .
           .       .       .
    """
    print(dataframe)
    labels = dataframe.columns
    data_arrays = []
    for col in labels:
        data_arrays.append(dataframe[col])
    
    return list(labels), list(data_arrays[1:])[:]  # excluding trial strings in data arrays


def make_histo(label, data_arrays, custom_bins=np.linspace(-1, 1, 21)):
    plt.xlabel('Aggregate Sentiment (-1 : 1 ; Neg : Pos)')
    plt.ylabel('Tweets Corresponding')
    keys.append(label)
    plt.hist(data_arrays, bins=custom_bins, alpha=0.5, label=keys)
    plt.legend(keys)


def main():
    labelsm, datam = parse_data(TwitterAnalysis.TwitterClient.load_existing_observation_set("set2", "masculine"))
    labelsf, dataf = parse_data(TwitterAnalysis.TwitterClient.load_existing_observation_set("set2", "feminine"))
    f_data = [[d[index] for index in range(150 * 5)] for d in dataf]
    m_data = [[d[index] for index in range(150 * 5)] for d in datam]

    aggregate_data = [f_data[3], m_data[3]]

    # I'm filtering out some of the neutral data.
    # I've already gotten graphs including it, and decided that we could visualize the shift better without it
    aggregate_data = data_cleaner.remove_bloated_range(aggregate_data, -0.08, 0.08)
    aggregate_data = data_cleaner.normalize_size(aggregate_data)

    # Since I've filtered out some data, I'm going to close the gap as so:
    cust_bins = np.linspace(-1, 1, 21)
    cust_bins = cust_bins[(cust_bins <= -0.1) | (cust_bins >= 0.1)]
    print(cust_bins)
    make_histo('M', aggregate_data[1], custom_bins=cust_bins)
    make_histo('F', aggregate_data[0], custom_bins=cust_bins)
    plt.title("Sentiment Polarity in Keywords")
    plt.show()


if __name__ == '__main__':
    main()
    
    


    


