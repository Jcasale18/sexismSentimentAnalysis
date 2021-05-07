import matplotlib
import matplotlib.pyplot as plt 
import TwitterAnalysis
import numpy as np
keys=[]

def parse_data(dataframe):
    labels = dataframe.columns
    dataarrays = []
    for col in labels:
        dataarrays.append(dataframe[col])
    
    return list(labels), list(dataarrays[1:])[1:]
def make_histo(label, dataarrays):
    #if(len(labels) != len(dataarrays)):
    #    raise TwitterAnalysis.InvalidDataException
    plt.xlabel('Aggregate Sentiment (-1 : 1 ; Neg : Pos)')
    plt.ylabel('Tweets Corresponding')
    keys.append(label)
    plt.hist(dataarrays, bins=np.linspace(-1, 1, 21), alpha=0.5, label=keys)
    plt.legend(keys)
def main():
    client = TwitterAnalysis.TwitterClient()
    labelsm, datam = parse_data(client.load_existing_observation_set("set2", "masculine"))
    labelsf, dataf = parse_data(client.load_existing_observation_set("set2", "feminine"))
    f_data = [[d[index] for index in range(1000)] for d in dataf]
    m_data = [[d[index] for index in range(1000)] for d in datam]
    aggregate_feminine_data = f_data[2]
    aggregate_masculine_data = m_data[2]
    print(len(aggregate_masculine_data))
    make_histo('M', aggregate_masculine_data)
    make_histo('F', aggregate_feminine_data)
    plt.title("Sentiment Polarity in Keywords")
    plt.show()

if __name__ == '__main__':
    main()
    
    


    


