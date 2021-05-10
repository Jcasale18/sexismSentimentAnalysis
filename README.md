# sexismSentimentAnalysis
Performing a sentiment analysis on tweets from Tweepy API to analyze presence of sexism


<h4> To run this script, you need an <a href='https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api' target="_blank"> API key</a> </h4>



# fill in the your_keys.ini file!
```python
[keys]
consumer_key = xxxx
consumer_secret_api_key = xxxx
access_token = xxxx
access_token_secret = xxxx
```

Primary class `TwitterAnalysis` provides two high level functions:
<br>
`analyze_keywords` is a method for retrieving data pertaining to number of desired categories, each containing a list of any number of desired keywords.
<br>
`load_existing_observation_set` is a static method for loading a set of data created and saved by the prior named method.
<br>

I wrote this code to do some research for a history class, but it is adaptable and can be used for other similar forms of analysis as well. The sentiment analysis is `vador lexicon`, which is optimized for social media, but is also a rather broad in it's uses, and is not perfect for all conditions.

There are some useful tools contained in the scripts as well, such as data size normalization, removal of outlier (with a definition of outlier being z_score > 2.5, not the standard 3), and a histogram utility.
