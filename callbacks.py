from dash.dependencies import Input, Output, State
import utils
import plotly.graph_objs as go
from collections import OrderedDict
import statistics
from datetime import datetime as dt
import re
import utils
import json
import dash
from dateutil import parser
import pytz
from imageio import imread
import dbhelper
from dash.exceptions import PreventUpdate
import environment
import os


if os.environ.get('USE_DATABASE', False):
    config_settings = dbhelper.parsed_config_file(filename=os.environ.get('DATABASE_CONFIG', 'config.ini'))
    db_connection = dbhelper.DBHelper(config_settings)
    DISPLAY_COLS = ['created_at', 'text', 'favorite_count', 'retweet_count', 'in_reply_to_status_id']
else:
    with open(os.environ.get('PARSED_TWEETS_PATH', ''), 'r', encoding='utf-8') as fp:
        res = json.loads(fp.read())
    DISPLAY_COLS = ['created_at', 'text', 'favorite_count', 'retweet_count', 'in_reply_to_status_id_str']

selected_features_api_tweets = ['created_at', 'favorite_count', 'favorited', 'id_str', 
                     'in_reply_to_screen_name', 'in_reply_to_status_id_str', 'lang', 
                     'retweet_count', 'retweeted', 'source', 'text']
selected_features_api_users = ['created_at', 'friends_count', 'followers_count', 'protected']

def register_callbacks(app):
    @app.callback(
        [Output('tweet-data-table', 'data'),
        Output('currently-showing-helper', 'children'),
        Output('tweet-frequency-graph', 'figure'),
        Output('tweet-source-graph', 'figure'),
        Output('most-mentioned-graph', 'figure'),
        Output('friends-foers-count-graph', 'figure'),
        Output('most-liked-table', 'data'),
        Output('most-rt-table', 'data'),
        ],
        [Input('user-picker', 'value'),
        Input('daterange-submit-button', 'n_clicks'),
        Input('my-date-picker-range', 'start_date'),
        Input('my-date-picker-range', 'end_date'),
        Input('timezone-filter', 'value'),
        Input('timeview-filter', 'value'),]
    )
    def update_output(user_id_selected, n_clicks, start_date, end_date, timezone_info, viewby_time):
        if os.environ.get('USE_DATABASE', False):
            tweet_data, user_data = utils.retrieve_data_from_db(db_connection, user_id_selected)
        else:
            tweet_data = utils.tweet2dt(res, selected_features_api_tweets)
            user_data = utils.tweet2dt(res, selected_features_api_users)
        tweet_data = tweet_data.sort_values(by=['created_at'], ascending=False)

        if n_clicks is not None and int(n_clicks) > 0: # actively filtering 'daterange-submit-button' in changed_id
            start_date_parsed = dt.strptime(re.split('T| ', start_date)[0], '%Y-%m-%d') if start_date is not None else dt.strptime('Jan 1 2008', '%b %d %Y')
            end_date_parsed = dt.strptime(re.split('T| ', end_date)[0], '%Y-%m-%d') if end_date is not None else dt.today()
            start_date_parsed = pytz.utc.localize(start_date_parsed)
            end_date_parsed = pytz.utc.localize(end_date_parsed)

            helper_date_str = "Currently showing tweets from {} to {}".format(start_date, end_date)

            filtered_tweet_data = tweet_data[(tweet_data['created_at'] >= start_date_parsed) & (tweet_data['created_at'] <= end_date_parsed)]
            tweet_freq_plot = utils.tweet_time_freq_plot(filtered_tweet_data, timezone=timezone_info, viewby=viewby_time)
            tweet_src_plot = utils.tweet_source_freq_plot(filtered_tweet_data)
            most_mentioned_plot = utils.most_mentioned_user_plot(filtered_tweet_data, text_col='text')

            filtered_user_data = user_data[(user_data['created_at'] >= start_date_parsed) & (user_data['created_at'] <= end_date_parsed)]
            friend_foers_plot = utils.friends_foers_count_plot(filtered_user_data)

            filtered_tweet_data['created_at'] = filtered_tweet_data['created_at'].apply(lambda x: x.strftime("%m/%d/%Y, %H:%M:%S"))
            top_5_liked = utils.get_top_by_col(filtered_tweet_data, 'favorite_count')[['created_at', 'text', 'favorite_count']]
            top_5_rt = utils.get_top_by_col(filtered_tweet_data, 'retweet_count')[['created_at', 'text', 'retweet_count']]
            return filtered_tweet_data[DISPLAY_COLS].to_dict('rows'), helper_date_str, tweet_freq_plot, tweet_src_plot, most_mentioned_plot, friend_foers_plot, top_5_liked.to_dict('rows'), top_5_rt.to_dict('rows')
        else:
            tweet_freq_plot = utils.tweet_time_freq_plot(tweet_data, timezone=timezone_info, viewby=viewby_time)
            tweet_src_plot = utils.tweet_source_freq_plot(tweet_data)
            most_mentioned_plot = utils.most_mentioned_user_plot(tweet_data, text_col='text')
            friend_foers_plot = utils.friends_foers_count_plot(user_data)

            helper_date_str = "Currently showing tweets from {} to {}".format(tweet_data['created_at'].dt.date.min().strftime('%Y-%m-%d'), tweet_data['created_at'].dt.date.max().strftime('%Y-%m-%d'))

            tweet_data['created_at'] = tweet_data['created_at'].apply(lambda x: x.strftime("%m/%d/%Y, %H:%M:%S"))
            top_5_liked = utils.get_top_by_col(tweet_data, 'favorite_count')[['created_at', 'text', 'favorite_count']]
            top_5_rt = utils.get_top_by_col(tweet_data, 'retweet_count')[['created_at', 'text', 'retweet_count']]

            return tweet_data[DISPLAY_COLS].to_dict('rows'), helper_date_str, tweet_freq_plot, tweet_src_plot, most_mentioned_plot, friend_foers_plot, top_5_liked.to_dict('rows'), top_5_rt.to_dict('rows')