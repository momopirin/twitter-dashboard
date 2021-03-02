# -*- coding: utf-8 -*-
"""
Created on Tue Apr  9 18:48:55 2019

@author: shday
"""

import math
from collections import namedtuple
import pandas as pd
import numpy as np
from dateutil import parser
import dash_html_components as html
import plotly.express as px
import pytz
import plotly.graph_objects as go
import urllib
import string
#import pkuseg
from wordcloud import WordCloud
import json
import re
import ast
import os

# selected_features_tweetjs = ['created_at', 'favorite_count', 'favorited', 'id_str', 
#                      'in_reply_to_screen_name', 'in_reply_to_status_id_str', 'lang', 
#                      'retweet_count', 'retweeted', 'source', 'full_text']
pretty_weekday_dict = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thurs', 4: 'Fri', 5: 'Sat', 6: 'Sun'}

# load zh stopwords for wordcloud
# zh_stopword_list_url = 'https://raw.githubusercontent.com/stopwords-iso/stopwords-zh/master/stopwords-zh.txt'
# zh_stopwords = urllib.request.urlopen(zh_stopword_list_url).read().decode('utf-8').split('\n')

def parse_source_text(text):
    return text.split('>')[1].split('<')[0]

def convert_tweet_json_to_df_row(json_data, selected_feature):
    temp_list = []

    for f in selected_feature:
        if f == 'source':
            cleaned_source = parse_source_text(json_data[f])
            temp_list.append(cleaned_source)
        elif f in ['friends_count', 'followers_count', 'protected']:
            if 'user' in json_data:
                temp_list.append(json_data['user'][f])
            else:
                temp_list.append(0) if f in ['friends_count', 'followers_count'] else temp_list.append(False)
        elif f == 'created_at': # parsed at the display time instead
            dt_object = parser.parse(json_data[f])
            temp_list.append(dt_object)

        # TODO: get the in reply to link working
        # elif f == 'in_reply_to_status_id_str':
        #     if json_data[f] is not None:
        #         html_link = "https://twitter.com/"+json_data['in_reply_to_screen_name']+'/status/'+ json_data[f]
        #         temp_list.append(html_link)
        #     else:
        #         temp_list.append(None)
        else:
            temp_list.append(json_data[f]) if f in json_data else temp_list.append("")
            
    return pd.DataFrame([temp_list], columns = selected_feature, index=[0])

def tweet2dt(json_list, selected_features):
    for i in range(len(json_list)):
        if i == 0:
            processed_df = convert_tweet_json_to_df_row(json_list[i], selected_features)
        else:
            temp = convert_tweet_json_to_df_row(json_list[i], selected_features)
            processed_df = processed_df.append(temp, ignore_index=True)
    
    # remove duplicates
    processed_df.drop_duplicates(inplace=True)

    return processed_df

def extract_owner_from_json():
    res = read_json_file(os.environ.get('PARSED_TWEETS_PATH', ''))
    first_tweet = res[0]
    if 'user' not in first_tweet: # from official twitter archive - only tweets objects are in it
        user_info = {}
        base_path, filename = os.path.split(os.environ.get('ACCOUNT_INFO_PATH', ''))
        account_info = simple_parse_twitter_archive_json(base_path, filename)
        user_info['screen_name'] = account_info['account']['username']
        user_info['id_str'] = account_info['account']['accountId']
        return user_info
    else:
        return first_tweet['user']

def retrieve_data_from_db(db_object, user_id):
    query = "SELECT * FROM tweets where user_id = {};".format(user_id)
    tweet_data = pd.read_sql(query, con=db_object.get_connection(), parse_dates=[1])
    tweet_data['created_at'] = pd.to_datetime(tweet_data['created_at'], errors='coerce')
    tweet_data['last_insert_date'] = pd.to_datetime(tweet_data['last_insert_date'], errors='coerce')
    tweet_data['created_at'] = tweet_data['created_at'].dt.tz_localize('UTC')
    tweet_data['last_insert_date'] = tweet_data['last_insert_date'].dt.tz_localize('UTC')

    query = "SELECT DISTINCT DATE(last_insert_date) AS created_at, friends_count, followers_count, protected \
         FROM user_stats where user_id = {} ORDER BY created_at;".format(user_id)
    user_data = pd.read_sql(query, con=db_object.get_connection(), parse_dates=[0])
    user_data['created_at'] = pd.to_datetime(user_data['created_at'], errors='coerce')
    user_data['created_at'] = user_data['created_at'].dt.tz_localize('UTC')
    return tweet_data, user_data

def tweet_time_freq_plot(df, normalized=True, timezone="utc", viewby="hours"):
    if timezone == "central":
        df['created_at'] = df['created_at'].apply(lambda x: x.astimezone(pytz.timezone("US/Central")))
    elif timezone == "beijing":
        df['created_at'] = df['created_at'].apply(lambda x: x.astimezone(pytz.timezone("Asia/Hong_Kong")))

    if viewby == "hours":
        data_time = df['created_at'].dt.hour.value_counts(normalize=normalized).reset_index()
    elif viewby == "day":
        data_time = df['created_at'].dt.day.value_counts(normalize=normalized).reset_index()
    else: #weekday
        data_time = df['created_at'].dt.weekday.value_counts(normalize=normalized, sort=False).reset_index()
        data_time['index'] = data_time['index'].apply(lambda x: pretty_weekday_dict[x])

    data_time.columns = ['x', 'y']
    fig = px.bar(data_time, x='x', y='y', labels={'x': 'time ('+timezone.capitalize()+')', 'y': 'relative frequency'}, 
        title="Tweet Frequency", color="y", height=350)
    return fig

def tweet_source_freq_plot(df, normalized=True):
    data_source = df['source'].value_counts(normalize=normalized).reset_index()
    data_source.columns = ['x', 'y']
    # fig = px.bar(data_source, x='y', y='x', labels={'x': 'source', 'y': 'relative frequency'}, 
    #          title="Tweet Source Distribution", orientation='h', height=400)
    fig = px.pie(data_source[:5], values='y', names='x', title="Top 5 Tweet Sources", height=400)
    return fig

def extract_mentioned_user(text, res_list):
    if not text.startswith('RT'):
        split_res = text.split()
        res_list.extend([x for x in split_res if len(re.findall('@\w+',x)) > 0])
        return res_list

def most_mentioned_user_plot(df, text_col='text'):
    res_list = []
    df[text_col].apply(lambda x: extract_mentioned_user(x, res_list))
    data_source = pd.Series(res_list).value_counts().reset_index()
    data_source.columns = ['x', 'y']
    
    data_source_top10 = data_source[:10].sort_values(by='y', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data_source_top10['y'],
        y=data_source_top10['x'],
        text=['screen_id', 'Frequency'],
        marker_color='indianred',
        orientation='h'
    ))

    fig.update_layout(
        autosize=False,
        #width=500,
        height=400,
        title={'text': "Top 10 Most Frequently Mentioned Users"},
        xaxis_title="count",
        yaxis_title="screen_name")

    return fig

def friends_foers_count_plot(df):
    df['created_at_dt'] = df['created_at'].dt.date

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['created_at_dt'], y=df['friends_count'],
                        name='Friends',
                        line = dict(color='royalblue')))
    fig.add_trace(go.Scatter(x=df['created_at_dt'], y=df['followers_count'],
                        name='Followers',
                        line = dict(color='deeppink')))

    fig.update_layout(
        title={'text': "Friends & Followers Count Overtime"},
        height=400,
        xaxis_title="date",
        yaxis_title="count")

    return fig

def get_top_by_col(df, col_name, top_num=5):
    if col_name == 'retweet_count':
        df = df[~df['text'].str.startswith('RT @')] # the author should be the user
    return df.sort_values(by=[col_name], ascending=False)[:top_num]

# def tokenize_text(sample, seg):
#     text = seg.cut(sample)
#     text = [x for x in text if x not in zh_stopwords]
#     text = [x for x in text if x not in string.punctuation]
#     text = [x for x in text if not x.startswith('http')]
#     return " ".join(text)

# disabled for now
# def generate_word_cloud(df, font_path, back_coloring=None):
#     # adapted from https://amueller.github.io/word_cloud/auto_examples/wordcloud_cn.html
#     seg = pkuseg.pkuseg(model_name='web')
#     string_elems = df['text'].apply(lambda x: tokenize_text(x, seg))
#     if back_coloring is not None:
#         wordcloud = WordCloud(font_path=font_path, background_color="white", max_words=100, mask=back_coloring,
#                max_font_size=100, random_state=42, width=1000, height=860).generate(' '.join(string_elems))
#     else:
#         wordcloud = WordCloud(font_path=font_path, max_words=100,
#                max_font_size=100, random_state=42, width=1000, height=860).generate(' '.join(string_elems))
#     return wordcloud

# below are json helper functions
def read_json_file(json_file):
    with open(json_file, 'r', encoding='utf-8') as fp:
        res = json.loads(fp.read())
    return res # a list of json objects

def simple_parse_twitter_archive_json(base_path, filename):
    with open(os.path.join(base_path, filename), encoding='utf-8') as f:
        raw_info = f.read()
    raw_info = raw_info.replace('\n', '')
    raw_info = re.sub(' {2,}', '', raw_info)
    raw_info = raw_info.replace(' : ', ':')
    parsed = ast.literal_eval(raw_info[raw_info.find('[') + 2:raw_info.find(']')])
    return parsed

def simple_parse_get_count_by_keyword(base_path, filename, keyword):
    with open(os.path.join(base_path, filename), encoding='utf-8') as f:
        raw_info = f.read()
    return raw_info.count(keyword)