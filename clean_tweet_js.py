import pandas as pd
import datetime
import os
import argparse
import json

"""
Helper file for auto_tweet_delete; use to extract tweet id and created time from tweet.js (downloaded from Twitter)
"""

def get_tweet_object_from_tweet_js(seq, num_of_tweet_block):
    """
    Helper method to get each smaller tweet blocks. 
    Tested May 2020 on tweet.js (subject to change as Twitter rolls out new data layout)
    
    Parameters:
        seq: (file object) opens a file in read mode.
        num_of_tweet_block: (int) number of parsed tweet objects to return.
            Note: if num_of_tweet_block > total line in the file, the function will return with maximum # of blocks extracted from the file.
            Therefore, it is possible to have returned tweets fewer than the requested block.

    Return: a list with number of requested tweets in it.
    """

    data = ""
    res = []
    curr = 0
    start_flag = False
    
    for line in seq:
        line = line.rstrip()
        
        if "\"tweet\"" in line:
            start_flag = True
        if line != "}, {" and start_flag:
            if 'full_text' in line:
                line = line.replace('full_text', 'text')
            data += line
        if line == "}, {":
            start_flag = False
            curr += 1
            # remove the extra "tweet" in front
            res.append(data.split("\"tweet\" : ")[1])
            data = ""
            if curr >= num_of_tweet_block:
                return res
    
    return res # in case we have parsed all lines but still fewer than `num_of_tweet_block`, return the result anyways

def extract_tweet_info_from_local_file(tweet_js_path, max_extract=None, get_cleaned_df=False, item_to_extract=['id_str', 'created_at'], output_path=None, begin=None, end=None):
    """
    Parse tweet.js file. 
    Tested May 2020 on tweet.js (subject to change as Twitter rolls out new data layout)
    
    Parameters:
        tweet_js_path: (str) path to `tweet.js` file.
        max_extract: (int) maximum number of parsed tweet objects to return. If None, all tweets identified in `tweet.js` will be extracted (recommend).
        get_cleaned_df: (boolean) if True, will return a dataframe with requested attributes as specified in `item_to_extract`.
        item_to_extract: (list) use alongside with `get_cleaned_df`; needs to be valid attributes within a tweet object.
        output_path: (str) path to save the output result.

    Return: N/A
    """

    if max_extract is None: # extract all tweets by default
        with open(tweet_js_path, encoding='utf-8') as f:
            all_data = f.read()
            max_extract = all_data.count('\"tweet\"')

    final_file_name = 'parsed_tweets_df.csv' if get_cleaned_df else 'parsed_tweets.json'
    if output_path is None:
        output_path = final_file_name
    elif '.csv' not in output_path:
        output_path = os.path.join(output_path, final_file_name)

    if os.path.isfile(final_file_name):
        print("Found {}, assumed already parsed. Exiting".format(final_file_name))
        return
    else:
        # do the actual extraction
        extracted_info = []
        with open(tweet_js_path, encoding='utf-8') as f:
            res = get_tweet_object_from_tweet_js(f, max_extract)

        print("Extracted {} tweet objects.".format(len(res)))

        begin_mark = int(begin) if begin is not None else 0
        end_mark = int(end) if end is not None else len(res)

        for obj in res[begin_mark:end_mark]:
            tmp = []
            json_obj = json.loads(obj)
            if get_cleaned_df:
                for item in item_to_extract: # assume that item is a valid attribute of a status object
                    tmp.append(json_obj[item])
                extracted_info.append(tmp)
            else: # want the actual Tweet object
                extracted_info.append(json_obj)

        if get_cleaned_df:
            formatted_df = pd.DataFrame(extracted_info, columns=item_to_extract)
            formatted_df.to_csv(output_path, index=False)
        else:
            with open(output_path, 'w', encoding='utf8') as file:
                file.write(json.dumps(extracted_info, sort_keys=True, indent=4, ensure_ascii=False))

def main():
    arg_parser = argparse.ArgumentParser(
        description='Parse tweet.js to get tweet related info')
    arg_parser.add_argument('-lp','--local_path', required=True,
                        metavar="/path/to/tweet.js",
                        help='Used with parameter `-m local`; path to the tweet.js file.')
    arg_parser.add_argument('-n','--num', required=False,
                        metavar="2000",
                        help='Number of tweet object to be parsed from the given tweet.js file.')
    arg_parser.add_argument('-o','--output', required=False,
                        metavar="/path/to/output",
                        help='Path to save the extracted info')
    arg_parser.add_argument('-df','--get_dataframe', required=False,
                        help='Save a dataframe instead of a collection of json file',
                        action="store_true")
    arg_parser.add_argument('-i','--item_list', required=False,
                        metavar="['id_str', 'created_at']",
                        help='Valid tweet Status object attribute to extract')
    arg_parser.add_argument('-b','--begin', required=False,
                        metavar="1000",
                        help='Export tweet object starting at the begin position.')
    arg_parser.add_argument('-e','--end', required=False,
                        metavar="3000",
                        help='Export tweet object ending at the end position (exclusive).')
    args = arg_parser.parse_args()

    item_list = args.item_list if args.item_list is not None else ['id_str', 'created_at']
    num_to_extract = int(args.num) if args.num is not None else None

    extract_tweet_info_from_local_file(args.local_path, num_to_extract, args.get_dataframe, item_list, args.output, args.begin, args.end)


if __name__ == "__main__":
    main()