# Author: Joseph Casale
""""
sexismSentimentAnalysis

Copyright © <2021> <Joseph Casale>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import configparser
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
        self.categories = dict()  # categories of keywords e.g masculine = ['men', 'beard']
        nltk.download('vader_lexicon')
        config = configparser.ConfigParser()
        config.read("your_keys.ini")
        # fill in
        info = {
            'consumer_key': config['keys']['consumer_key'],
            'consumer_secret_api_key': config['keys']['consumer_secret_api_key'],
            'access_token': config['keys']['access_token'],
            'access_token_secret': config['keys']['access_token_secret'],
        }

        try:
            self.api = self.__authenticate(info)
        except Exception as e:
            print("Authentication Error: " + repr(e))

    def __authenticate(self, info):
        """
            Takes info dict:
            {
                'consumer_key': val
                'consumer_secret_api_key' : val
                'access_token' : val
                'access_token_secret' : val
            }
        """
        auth = OAuthHandler(info['consumer_key'], info['consumer_secret_api_key'])
        auth.set_access_token(info['access_token'], info['access_token_secret'])
        print("Success!" + info['consumer_key'])
        return tweepy.API(auth, wait_on_rate_limit=True)

    def __clean_tweet(self, tweetstr):
        tweet = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) |(\w+:\/\/\S+)", " ", tweetstr).split())
        if (tweet[0:3] == 'RT '):
            tweet = tweet[2:]
        return tweet

    def __get_tweets(self, query, count=20):
        """
        fetch and parse tweets

        query : String for search query (keyword)

        count : batch size
        """

        tweets = []
        final = count  # to guarantee we get the proper amount of unique tweets.
        filter_duplicates = True  # Filters out duplicates
        previous = 0  # will never be equal to final at start
        failed_to_retrieve_unique_tweet = 0  # if it fails 3 times in a row to get a unique tweet, we will accept duplicates
        try:
            print(str(count) + " sampling")

            while final > 0:
                bat = [tweet for tweet in tweepy.Cursor(
                    self.api.search, q=query + " -filter:retweets", include_entities=True, leng="en").items(final)]
                for tweet in bat:
                    parsed_tweet = dict()

                    parsed_tweet['sentiment'] = self.__get_sentiment(tweet)
                    parsed_tweet['tweet'] = tweet.text

                    # Depending on popularity of search, duplicates may be impossible to avoid.
                    if parsed_tweet not in tweets or not filter_duplicates:  #if filter is not on, add it anyways
                        final -= 1
                        tweets.append(parsed_tweet)

                    if final == 0:
                        break

                    if filter_duplicates:
                        if final > 0:
                            if previous == final:
                                failed_to_retrieve_unique_tweet += 1
                                if failed_to_retrieve_unique_tweet > 2:
                                    print("Unable to get more unique tweets, accepting duplicates now")
                                    filter_duplicates = False
                            else:
                                failed_to_retrieve_unique_tweet = 0
                            print("Looks like there were some duplicates, {} more to go!".format(final))
                            previous = final



        except tweepy.TweepError as e:
            print(str(e))
        return list(tweets)

    def __get_sentiment(self, tweet):
        """
        get_sentiment will clean the tweet object in the process of returning a dict
        of form {'neg': double, 'neu':double, 'pos': double, 'compound':double}
        """
        # clean text
        tweet.text = self.__clean_tweet(tweet.text)
        return SentimentIntensityAnalyzer().polarity_scores(tweet.text)

    def analyze_keywords(self, size, filename=None, **kwargs):
        """
            size : batch size for each keyword

            filename : optional csv file to save to

            This code is designed to analyze tweets on a masculine/feminine basis, but
            you may specify your own type. These will be the names of the labels.
            kwargs : masculine = [keyword_1, keyword_2...keyword_k] 
                     feminine = [keyword_1, keyword_2...keyword_k] .. allows for additional categories
            
            NOTE: Keywords categories must be equal number.

            Retrieves batch size unique tweets for each keyword, performs a sentiment analysis,
            and returns a pandas dataframe indexed by KEYWORD + T[count], 1 <= count <= size
        """

        if len(kwargs) == 0:
            raise (InvalidDataException("No keywords passed into analyze_keyword"))

        for category in kwargs.keys():
            df = pd.DataFrame()
            for keyword in kwargs[category]:
                print(keyword)
                tweet_data = self.__get_tweets(query=keyword, count=size)
                count = 0
                for tweet in tweet_data:
                    count += 1
                    sentiment = tweet['sentiment']
                    trial = (str(keyword) + f' T{count % size}')  # trial label, mod size for trial number for each word
                    new_rec = pd.DataFrame(
                        [[trial, sentiment['pos'], sentiment['neu'], sentiment['neg'], sentiment['compound']]],
                        columns=['trial', 'Pos.', 'Neu.', 'Neg.', 'Summary'])
                    df = df.append(new_rec, ignore_index=True)  # ignoring index allows count to keep going
            self.categories[category] = df

        if filename is not None:
            for frame in self.categories.keys():
                self.categories[frame].to_csv('data/' + filename.strip() + frame.strip() + '.csv',  # frame is category
                                              columns=['trial', 'Pos.', 'Neu.', 'Neg.', 'Summary'],
                                              index=False)

        return self.categories

    def load_existing_observation_set(self, filename, category):
        print(filename)
        filename = filename.strip()
        category = category.strip()
        if os.path.exists('data/' + filename + category + '.csv'):
            try:
                data = pd.read_csv('data/' + filename + category + '.csv')
                # data = pd.concat(data, ignore_index=True)
                return data
            except:
                raise (InvalidDataException(('data/' + filename + category + '.csv file exists but is not valid')))
        else:
            raise (FileNotFoundError('data/' + filename + category + '.csv does not exist.'))


def main():
    client = TwitterClient()

    client.analyze_keywords(150, filename="set2",
                            masculine=['Sergey Brin', 'Bill Gates', 'Adam Steltzner', 'Michio Kaku', 'Neil deGrasse Tyson'],
                            feminine=['Susan Kare', 'Melinda Gates', 'Diana Trujillo', 'Mae Jemison', 'Grace Hopper'])
    data = client.load_existing_observation_set("set2", 'masculine')
    data2 = client.load_existing_observation_set("set2", 'feminine')
    print(data)
    print("-----------------------------------------------------------")
    print(data2)


if __name__ == '__main__':
    main()
