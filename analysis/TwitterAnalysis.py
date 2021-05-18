# Author: Joseph Casale
""""
sexismSentimentAnalysis

Copyright © <2021> <Joseph Casale>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import time
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

    def __get_tweets(self, query, count=20, filter_duplicates=True):
        """
        fetch and parse tweets

        query : String for search query (keyword)

        count : batch size - Guaranteed this amount, may contain duplicates no matter what.

        filter_duplicates=True, Will FILTER duplicates, but will not guarantee uniqueness.

        Returns list of dicts, one for each tweet.
        """

        tweets = []
        final = count  # to guarantee we get the proper amount of unique tweets.
        previous = 0  # will never be equal to final at start
        failed_to_retrieve_unique_tweet = 0  # if it fails to get a unique tweet 5 times, we will accept duplicates
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
                    if parsed_tweet not in tweets or not filter_duplicates:  # if filter is not on, add it anyways
                        final -= 1
                        tweets.append(parsed_tweet)
                    if final == 0:
                        break

                    # A little bit ugly, but helps improve tweet unique-ness.
                    if filter_duplicates:
                        if final > 0:
                            if previous == final:
                                print("Looks like there were some duplicates, {} , {} prev more to go!".format(final, previous))
                                failed_to_retrieve_unique_tweet += 1
                                if failed_to_retrieve_unique_tweet > 8:
                                    print("Unable to get more unique tweets, accepting duplicates now")
                                    filter_duplicates = False
                            else:
                                failed_to_retrieve_unique_tweet = 0
                            previous = final
        except tweepy.TweepError as e:
            print(str(e))
        return list(tweets)

    def __get_unique_tweets(self, query, count=20):
        """
        Returns a list of dict of UNIQUE tweets. May not be specified count in size.

        Will attempt to get as many as reasonably possible without consuming the rate limit excessively
        """
        tweets = []

        current = 0
        previous = 0
        try:
            print(str(count) + " sampling")
            while current < count:
                bat = [tweet for tweet in tweepy.Cursor(
                    self.api.search, q=query + " -filter:retweets", include_entities=True, leng="en").items(count - current)]
                for tweet in bat:
                    parsed_tweet = dict()
                    parsed_tweet['sentiment'] = self.__get_sentiment(tweet)
                    parsed_tweet['tweet'] = tweet.text
                    if parsed_tweet not in tweets:
                        tweets.append(parsed_tweet)
                        current += 1
                        if current == count:
                            break
                if current == previous:
                    # failed to get more on this run
                    break
                previous = current
            print("Received {} out of requested {} tweets.".format(current, count))
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

    def analyze_keywords(self, size, filename=None, duplicate_filter=1, **kwargs):
        """
            size : batch size for each keyword

            filename : optional csv file to save to (default None)
            Files it saves to will be under "data/filename+category", a file for each category given under kwargs.

            duplicate_filter: 1 for attempt to filter, 2 for strict filter, anything else will not filter(default 1)

            This code is designed to analyze tweets on a masculine/feminine basis, but
            you may specify your own type. These will be the names of the labels.
            kwargs : masculine = [keyword_1, keyword_2...keyword_k] 
                     feminine = [keyword_1, keyword_2...keyword_k] .. allows for additional categories
            
            NOTE: Keywords categories must be equal number.

            Retrieves batch size for each keyword, performs a sentiment analysis,
            and returns a pandas dataframe indexed by KEYWORD + T[count], 1 <= count <= size

            WARNING: duplicate_filter=2 DOES NOT guarantee receiving the specified number of tweets.
        """

        if len(kwargs) == 0:
            raise (InvalidDataException("No keywords passed into analyze_keyword"))

        for category in kwargs.keys():
            recdict = dict()
            for keyword in kwargs[category]:

                if duplicate_filter == 1:
                    tweet_data = self.__get_tweets(query=keyword, count=size)
                if duplicate_filter == 2:
                    tweet_data = self.__get_unique_tweets(query=keyword, count=size)
                else:
                    tweet_data = self.__get_tweets(query=keyword, count=size, filter_duplicates=False)
                start = time.perf_counter_ns()
                count = 0
                for tweet in tweet_data:
                    count += 1
                    sentiment = tweet['sentiment']
                    trial = (str(keyword) + f' T{count % size}')  # trial label, mod size for trial number for each word
                    recdict[trial] = [sentiment['pos'], sentiment['neu'], sentiment['neg'], sentiment['compound']]
                    
            df = pd.DataFrame.from_dict(recdict, orient='index')
            self.categories[category] = df
            end = time.perf_counter_ns()
            print(end-start + "nanoseconds to append data")

        if filename is not None:
            dir = os.path.dirname(os.path.realpath(__file__))
            os.chdir(dir)
            for frame in self.categories.keys():
                self.categories[frame].to_csv('../data/' + filename.strip() + frame.strip() + '.csv')

        return self.categories

    @staticmethod
    def load_existing_observation_set(filename, category):
        print(filename)
        filename = filename.strip()
        category = category.strip()
        dir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(dir)
        if os.path.exists('../data/' + filename + category + '.csv'):
            try:
                data = pd.read_csv('../data/' + filename + category + '.csv')
                # data = pd.concat(data, ignore_index=True)
                return data
            except:
                raise (InvalidDataException(('../data/' + filename + category + '.csv file exists but is not valid')))
        else:
            raise (FileNotFoundError('../data/' + filename + category + '.csv does not exist.'))


def main():
    client = TwitterClient()

    client.analyze_keywords(250, filename="set6",
                            masculine=['masculinity', 'Masculinity'],
                            feminine=['feminism', 'Feminism'],
                            duplicate_filter=2)
                            # There are a couple twitter handles there at the end for some social media CS influencers
                            # this is one trial of many, and this one will be stricly filtered
    data = client.load_existing_observation_set("set6", 'masculine')
    data2 = client.load_existing_observation_set("set6", 'feminine')
    print(data)
    print("-----------------------------------------------------------")
    print(data2)


if __name__ == '__main__':
    main()
