import os

# uncomment the lines below if you've imported everything to your local db
#os.environ['USE_DATABASE'] = 'True'
#os.environ['DATABASE_CONFIG'] = 'sample-config.ini'

# uncomment the line below and pass the path to parsed_tweets.json in
os.environ['PARSED_TWEETS_PATH'] = 'sample_tweets.json'
os.environ['ACCOUNT_INFO_PATH'] = 'path\account.js'