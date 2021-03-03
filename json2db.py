# Works for status object obtained through API.
# TODO: modify for tweet.js
import dbhelper
import json
import uuid
from dateutil import parser
import argparse
import datetime
import utils
import os

# given the list of Twitter Status objects
def update_user_table(json_list, db_object):
    distinct_user_pair = list(set([(x['user']['id_str'], parser.parse(x['user']['created_at']).strftime('%Y-%m-%d %H:%M:%S')) for x in json_list]))
    for id_creation_pair in distinct_user_pair:
        query = "INSERT INTO users (id, created_at) SELECT %s,%s \
            WHERE NOT EXISTS (SELECT id FROM users WHERE id = %s);"
        args = (id_creation_pair[0], id_creation_pair[1], id_creation_pair[0])
        db_object.write_one_record(query, args)

# given multiple elements from Twitter official archive
def update_user_table_from_archive(account_dict, db_object):
    parse_creation_date = parser.parse(account_dict['account']['createdAt']).strftime('%Y-%m-%d %H:%M:%S')
    query = "INSERT INTO users (id, created_at) SELECT %s,%s \
            WHERE NOT EXISTS (SELECT id FROM users WHERE id = %s);"
    args = (account_dict['account']['accountId'], parse_creation_date, account_dict['account']['accountId'])
    db_object.write_one_record(query, args)

# given the list of Twitter Status objects
def update_user_stats_table(json_list, last_updated_dt, db_object):
    distinct_user_stats_pairs = list(set([(x['user']['id_str'], x['user']['description'], \
        x['user']['followers_count'], x['user']['friends_count'], x['user']['name'], \
        x['user']['screen_name'], x['user']['statuses_count'], x['user']['protected']) for x in json_list]))
    for data in distinct_user_stats_pairs:
        unique_id = str(uuid.uuid4())
        query = "INSERT INTO user_stats (id, user_id, last_insert_date, description, followers_count, friends_count, name, screen_name, statuses_count, protected) \
            SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s \
            WHERE NOT EXISTS (SELECT * \
                FROM user_stats WHERE user_id = %s AND description = %s AND followers_count = %s \
                    AND friends_count = %s AND name = %s AND screen_name = %s AND statuses_count = %s \
                        AND protected = %s);"
        args = (unique_id, data[0], parser.parse(last_updated_dt).strftime('%Y-%m-%d %H:%M:%S'),
            data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[0], data[1], data[2], 
            data[3], data[4], data[5], data[6], data[7])
        db_object.write_one_record(query, args)

# given multiple elements from Twitter official archive
def update_user_stats_table_from_archive(account_dict, profile_dict, pretected_history, foing_count, foer_count, status_count, last_updated_dt, db_object):
    try:
        protect_status = True if pretected_history[-1]['protectedHistory']['action'].lower() == 'protect' else False
    except KeyError:
        protect_status = True if pretected_history['protectedHistory']['action'].lower() == 'protect' else False
    unique_id = str(uuid.uuid4())
    query = "INSERT INTO user_stats (id, user_id, last_insert_date, description, followers_count, friends_count, name, screen_name, statuses_count, protected) \
        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s \
        WHERE NOT EXISTS (SELECT * \
            FROM user_stats WHERE user_id = %s AND description = %s AND followers_count = %s \
                AND friends_count = %s AND name = %s AND screen_name = %s AND statuses_count = %s \
                    AND protected = %s);"
    args = (unique_id, account_dict['account']['accountId'], parser.parse(last_updated_dt).strftime('%Y-%m-%d %H:%M:%S'),
        profile_dict['profile']['description']['bio'], foer_count, foing_count, account_dict['account']['accountDisplayName'], account_dict['account']['username'], status_count, protect_status, account_dict['account']['accountId'], profile_dict['profile']['description']['bio'], foer_count, 
        foing_count, account_dict['account']['accountDisplayName'], account_dict['account']['username'], status_count, protect_status)
    db_object.write_one_record(query, args)

# given the list of Twitter Status objects
def update_tweets_table(json_list, last_updated_dt, db_object):
    distinct_tweets = [(x['id_str'], parser.parse(x['created_at']).strftime('%Y-%m-%d %H:%M:%S'), \
        x['favorite_count'], x['favorited'], x['in_reply_to_status_id_str'], \
        x['in_reply_to_user_id_str'], x['in_reply_to_screen_name'], x['lang'],\
        x['retweet_count'], x['retweeted'], utils.parse_source_text(x['source']), x['text'], x['user']['id_str'], last_updated_dt) for x in json_list]
    print("Loaded {} tweets.".format(len(distinct_tweets)))
    query = "INSERT INTO tweets (id, created_at, favorite_count, favorited, in_reply_to_status_id, \
       in_reply_to_user_id, in_reply_to_screen_name, lang, \
       retweet_count, retweeted, source, text, user_id, last_insert_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
       ON DUPLICATE KEY UPDATE last_insert_date = last_insert_date"
    db_object.write_multiple_records(query, distinct_tweets)

# given multiple elements from Twitter official archive
def update_tweets_table_from_archive(tweets_list, user_id, last_updated_dt, db_object):
    distinct_tweets = []
    elements = ['id_str', 'created_at', 'favorite_count', 'favorited', 'in_reply_to_status_id_str', 'in_reply_to_user_id_str', 'in_reply_to_screen_name', 'lang', 'retweet_count', 'retweeted', 'source', 'text']
    for t in tweets_list:
        temp = []
        for f in elements:
            if f not in t:
                temp.append("")
            else:
                if f == 'created_at':
                    temp.append(parser.parse(t[f]).strftime('%Y-%m-%d %H:%M:%S'))
                elif f == 'source':
                    temp.append(utils.parse_source_text(t[f]))
                else:
                    temp.append(t[f])
        temp.extend([user_id, last_updated_dt])
        distinct_tweets.append(tuple(temp))

    print("Loaded {} tweets.".format(len(distinct_tweets)))
    query = "INSERT INTO tweets (id, created_at, favorite_count, favorited, in_reply_to_status_id, \
       in_reply_to_user_id, in_reply_to_screen_name, lang, \
       retweet_count, retweeted, source, text, user_id, last_insert_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
       ON DUPLICATE KEY UPDATE last_insert_date = last_insert_date"
    db_object.write_multiple_records(query, distinct_tweets)

# given the list of Twitter Status objects
# not supported for tweet archive yet.
def update_media_table(json_list, last_updated_dt, db_object):
    # only store info for tweets with media
    tweets_with_media = [x for x in json_list if 'extended_entities' in x and 'media' in x['extended_entities']]
    
    distinct_media = []
    for tweet in tweets_with_media:
        tweet_id = tweet['id_str']
        for index, m in enumerate(tweet['extended_entities']['media']):
            filename = tweet_id+'_'+str(index)+'.'+m['media_url_https'].split('.')[-1]
            distinct_media.append((m['id_str'], m['type'], filename, m['media_url_https'], tweet_id, parser.parse(last_updated_dt).strftime('%Y-%m-%d %H:%M:%S')))
    print("Loaded {} tweets with media.".format(len(distinct_media)))
    query = "INSERT INTO media (id, media_type, filename, media_url, tweet_id, last_insert_date) \
       VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE last_insert_date = last_insert_date"
    db_object.write_multiple_records(query, distinct_media)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Save tweet json to local database')
    arg_parser.add_argument('-s','--secret', required=True,
                        metavar="/path/to/config.ini",
                        help='Path to database config info')
    arg_parser.add_argument('-f','--filename', required=False,
                        metavar="/path/to/tweet_json",
                        help='Path to the json file that contains tweet objects (retrieved from API)')
    arg_parser.add_argument('-m','--mode', required=True,
                        metavar="api",
                        help='Specify how tweets are going to be removed. api: crawl through API (subject to 3,200 tweets limitation). \
                         local: need to provie path to the \data folder.')
    arg_parser.add_argument('-lp','--local_path', required=False,
                        metavar="/path/to/data/",
                        help='Used with parameter `-m local`; path to the /data folder.')
    arg_parser.add_argument('-pchunk','--parsed_chunk', required=False,
                        metavar="parsed_tweet_10000.json",
                        help='Used with parameter `-m local`; filename of the small parsed json file. It should be under the /data folder.')
    arg_parser.add_argument('-d','--date', required=False,
                        metavar="2020-05-01",
                        help='Insert date, if applicable')
    args = arg_parser.parse_args()

    # local mode must come with path to /data folder (as of June 2020)
    if args.mode.lower() == 'local' and args.local_path is None:
        raise Exception("ERROR: local mode specified, but path to the /data folder is not found. Exited.")
    if args.mode.lower() == 'api' and args.filename is None:
        raise Exception("ERROR: api mode specified, but path to the json file is not found. Exited.")

    config_settings = dbhelper.parsed_config_file(filename=args.secret)
    db_connection = dbhelper.DBHelper(config_settings)
    db_connection.confirm_connection()

    if args.mode == "api":
        print("Enter api mode.")
        tweet_jsons = utils.read_json_file(args.filename)

        # get the time string
        try:
            split_seg = args.filename.split('/')[-1].split('_')[1].split('-')
            time_str = '-'.join(split_seg[:3])+' '+':'.join(split_seg[3:])
            parsed_insertion_date_str = parser.parse(time_str).strftime('%Y-%m-%d %H:%M:%S')
        except parser.ParserError:
            if args.date is not None:
                parsed_insertion_date_str = parser.parse(args.date).strftime('%Y-%m-%d %H:%M:%S')
            else:
                parsed_insertion_date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        update_user_table(tweet_jsons, db_connection)
        update_user_stats_table(tweet_jsons, parsed_insertion_date_str, db_connection)
        update_tweets_table(tweet_jsons, parsed_insertion_date_str, db_connection)
        update_media_table(tweet_jsons, parsed_insertion_date_str, db_connection)
    else:
        print("Enter local archive mode.")
        print("Please ensure that you've preprocessed the tweet.js file first and put it in the same folder as other data files.")

        if args.date is not None:
            parsed_insertion_date_str = parser.parse(args.date).strftime('%Y-%m-%d %H:%M:%S')
        else:
            parsed_insertion_date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        account_info = utils.simple_parse_twitter_archive_json(args.local_path, "account.js")
        profile_info = utils.simple_parse_twitter_archive_json(args.local_path, "profile.js")
        pretected_history = utils.simple_parse_twitter_archive_json(args.local_path, "protected-history.js")

        foing_count = utils.simple_parse_get_count_by_keyword(args.local_path, "following.js", '"following"')
        foer_count = utils.simple_parse_get_count_by_keyword(args.local_path, "follower.js", '"follower"')
        status_count = utils.simple_parse_get_count_by_keyword(args.local_path, "tweet.js", '"tweet"')

        if args.parsed_chunk is None:
            with open(os.path.join(args.local_path, 'parsed_tweets.json'), encoding='utf8') as f:
                tweets = json.load(f)
            print("{} tweets loaded from parsed_tweets.json.".format(len(tweets)))
        else:
            with open(os.path.join(args.local_path, args.parsed_chunk), encoding='utf8') as f:
                tweets = json.load(f)
            print("{} tweets loaded from {}.".format(len(tweets), args.parsed_chunk))

        user_id = account_info['account']['accountId']

        update_user_table_from_archive(account_info, db_connection)
        update_user_stats_table_from_archive(account_info, profile_info, pretected_history, foing_count, foer_count, status_count, parsed_insertion_date_str, db_connection)
        update_tweets_table_from_archive(tweets, user_id, parsed_insertion_date_str, db_connection)

    db_connection.close_connection()