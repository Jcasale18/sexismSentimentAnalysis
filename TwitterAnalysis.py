# Author: Joseph Casale
'''
sexismSentimentAnalysis

Copyright © <2021> <Joseph Casale>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
import os
import inspect
import tweepy
import re
import pandas as pd
from tweepy import OAuthHandler
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

class InvalidDataException(Exception):
    def __init__(self, message):
        super().__init__(message)

class TwitterClient(object):

    def __init__(self):
        nltk.download('vader_lexicon')


        #fill in
        info = {
            'consumer_key' : '',
            'consumer_secret_api_key' : '',
            'access_token' : '',
            'access_token_secret' : '',
        }


        try:
            self.api = self.authenticate(info)
        except Exception as e:
            print("Authentication Error: " + e.__repr__)

    def authenticate(self, info):
        '''
            Takes info dict:
            {
                'consumer_key': val
                'consumer_secret_api_key' : val
                'access_token' : val
                'access_token_secret' : val
            }
        '''
        auth = OAuthHandler(info['consumer_key'], info['consumer_secret_api_key'])
        auth.set_access_token(info['access_token'], info['access_token_secret'])

        return tweepy.API(auth, wait_on_rate_limit=True)

    def clean_tweet(self, tweetstr): 
        tweet = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) |(\w+:\/\/\S+)", " ", tweetstr).split()) 
        if (tweet[0:3] == 'RT '):
            tweet = tweet[2:]
        return tweet
    def get_tweets(self, query, count = 20):
        '''fetch and parse tweets'''

        tweets = []

        try:

            while count > 0:
                print(str(count) + " sampling")
                #batch = self.api.search(q = query, count=count)
                bat = [tweet for tweet in tweepy.Cursor(
                        self.api.search, q = query+" -filter:retweets", include_entities=True, leng="en").items(count)]
                for tweet in bat:

                    parsed_tweet = {}

                    parsed_tweet['sentiment'] = self.get_sentiment(tweet)
                    parsed_tweet['tweet'] = tweet.text
                    tweets.append(parsed_tweet)
                
                count = count - len(tweets)#to guarentee unique tweets. len(list) time complexity is apparently constant.

        except tweepy.TweepError as e:
            print(str(e))
        return list(tweets)



    def get_sentiment(self, tweet):
        """
        get_sentiment will clean the tweet object in the process of returning a dict
        of form {'neg': double, 'neu':double, 'pos': double, 'compound':double}
        """
        #clean text
        tweet.text = self.clean_tweet(tweet.text)
        return SentimentIntensityAnalyzer().polarity_scores(tweet.text)


    def analyze_keywords(self, size, filename = None, **kwargs) :
        """
            size : batch size for each keyword

            filename : optional csvfile to save to

            This code is designed to analyze tweets on a masculine/feminine basis, but
            you may specify your own type. These will be the names of the labels.
            kwargs : masculine = [keyword_1, keyword_2...keyword_k] 
                     feminine = [keyword_1, keyword_2...keyword_k] .. allows for additional categories
            
            NOTE: Keywords categories must be equal number.

            Retrieves batch size unique tweets for each keyword, performs a sentiment analysis,
            and returns a pandas dataframe indexed by KEYWORD + T[count], 1 <= count <= size
        """

        if len(kwargs) == 0:
            raise(InvalidDataException("No keywords passed into analyze_keyword"))


        Client = TwitterClient()

        df = pd.DataFrame()
        indeces = []
        for category in kwargs.keys():
            for keyword in kwargs[category]:
                tweet_data = Client.get_tweets(query=keyword, count=size)
                count = 0
                for tweet in tweet_data:
                    count+=1
                    sentiment = tweet['sentiment']
                    index = [(str(keyword) + f' T{count}')]#index for the new data entry
                    indeces.append(index[0])#store it in a collection of indeces to use later on
                    new_rec = pd.DataFrame([[sentiment['pos'], sentiment['neu'], sentiment['neg'], sentiment['compound']]], columns=[ 'Pos.', 'Neu.', 'Neg.', 'Summary'], index=index)
                    df = df.append(new_rec) 
        if filename is not None:
            df.to_csv('data/' + filename, columns=[ 'Pos.', 'Neu.', 'Neg.', 'Summary'])
        
        return df
    def load_existing_observation_set(self, filename):
        if os.path.exists('data/' + filename.strip() + ".csv"):
            try:
                return pd.read_csv('data/' + filename.strip() + ".csv")
            except:
                raise(InvalidDataException(('data/' + filename + '.csv file exists but is not valid')))
        else:
            raise(FileNotFoundError('data/' + filename + " does not exist."))
def main():
    Client = TwitterClient()
 
    Client.analyze_keywords(2,filename="set1.csv", masculine=['men', 'mgtow', 'dudes', 'boys', 'Neil deGrasse Tyson'], 
                              feminine=[ 'women', 'feminism', 'ladies', 'girls', 'Grace Hopper'])
    data = Client.load_existing_observation_set("set1")
    print(data)
if __name__ == '__main__':
    main()
    