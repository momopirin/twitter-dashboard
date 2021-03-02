import pathlib as pl
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import os
from datetime import datetime as dt
import json

import utils
import dbhelper
import environment

table_header_style = {
    "backgroundColor": "rgb(2,21,70)",
    "color": "white",
    "textAlign": "center",
}

APP_PATH = str(pl.Path(__file__).parent.resolve())
app = dash.Dash(__name__)

DISPLAY_COLS = ['created_at', 'text', 'favorite_count', 'retweet_count', 'in_reply_to_status_id_str']
available_timezones = {'UTC': 'utc', 'Central Time (US)': 'central', 'Beijing Time': 'beijing'}
available_timefilters = ['Hours', 'Day', 'Weekday']

if os.environ.get('USE_DATABASE', False):
    config_settings = dbhelper.parsed_config_file(filename=os.environ.get('DATABASE_CONFIG', 'config.ini'))
    db_connection = dbhelper.DBHelper(config_settings)
    DISPLAY_COLS = ['created_at', 'text', 'favorite_count', 'retweet_count', 'in_reply_to_status_id']

# get the list of available user
def get_user_id_screenname_map():
    option_list = []

    if os.environ.get('USE_DATABASE', False):
        user_id_query = """SELECT user_stats.user_id, user_stats.screen_name
        FROM user_stats
        INNER JOIN 
        (SELECT screen_name, MAX(last_insert_date) as TopDate
        FROM user_stats
        GROUP BY screen_name) AS EachItem ON 
            EachItem.TopDate = user_stats.last_insert_date 
            AND EachItem.screen_name = user_stats.screen_name;"""
        user_list = db_connection.read_records(user_id_query)

        for up in user_list:
            user_id_dict = {}
            user_id_dict['label'] = up[1]
            user_id_dict['value'] = up[0]
            option_list.append(user_id_dict)
    else: # loading from local json file
        curr_user = utils.extract_owner_from_json()
        option_list.append({'label': curr_user['screen_name'], 'value': curr_user['id_str']})

    return option_list

banner_layout = html.Div(
            className="pkcalc-banner",
            children=[
                html.H2("Twitter Dashboard"),
                html.A(
                    id="gh-link",
                    children=["View on GitHub"],
                    href="https://github.com/plotly/dash-sample-apps/tree/master/apps/dash-pk-calc",
                    style={"color": "white", "border": "solid 1px white"},
                ),
                html.Img(src=app.get_asset_url("GitHub-Mark-Light-64px.png")),
            ],
        )

user_selection_layout = html.Div(
            className="row",
            children=[
                html.Div(
                    className="user-selection",
                    children=[
                        html.Label("Current User:",
                            htmlFor='user-picker',
                            # style={
                            #     'display': 'inline-block',
                            #     'margin-right': '10px',
                            # }
                        ),
                        dcc.Dropdown(
                            id='user-picker',
                            options=get_user_id_screenname_map(),
                            value=get_user_id_screenname_map()[0]['value'], #need a default
                            placeholder="Select a user...",
                            style={
                                'width': '50%',
                                #'display': 'inline-block',
                                'margin-bottom': '5px',
                            }
                        ),
                    ]
                ),
            ],
        )

top_layout = html.Div(
                    className="row",
                    style={},
                    children=[
                        html.Div(
                            className="three columns pkcalc-settings",
                            children=[
                                html.P(["Filtering Criteria"]),
                                html.Div(
                                    [
                                        html.Div("Date Range", 
                                            id='output-container-date-picker-range'),
                                        dcc.DatePickerRange(
                                            id='my-date-picker-range',
                                            min_date_allowed=dt(1995, 8, 5),
                                            max_date_allowed=dt.today().date(),
                                            initial_visible_month=dt.today().replace(day=1).date(),
                                        ),
                                        html.Button(id='daterange-submit-button', n_clicks=0, children='Submit')
                                    ]
                                ),
                                html.Div(id="currently-showing-helper", style={
                                    "font-size": "10px",
                                    'font-family': "'Courier New', Courier, monospace"
                                })
                            ],
                        ),
                        html.Div(
                            className="nine columns pkcalc-data-table",
                            children=[
                                dash_table.DataTable(
                                    id="tweet-data-table",
                                    columns=[{"name": i, "id": i} for i in DISPLAY_COLS],
                                    style_header=table_header_style,
                                    page_size=8,
                                    style_data={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                    },
                                    filter_action="native",
                                    sort_action="native",
                                    sort_mode="multi",
                                )
                            ],
                        ),
                    ],
                )

tweet_frequency_source_layout = html.Div(
                    className="row",
                    children=[
                        html.Div(className="six columns",
                            children=[
                                html.Div([
                                    dcc.Dropdown(
                                        id='timezone-filter',
                                        options=[{'label': i, 'value': available_timezones[i]} for i in available_timezones],
                                        value='UTC',
                                        placeholder="Timezone...",
                                    ),
                                    dcc.Dropdown(
                                        id='timeview-filter',
                                        options=[{'label': i, 'value': i.lower()} for i in available_timefilters],
                                        value='hours',
                                        placeholder="View by hours...",
                                    ),
                                ],
                                ),
                                html.Div(
                                    children=[dcc.Graph(id="tweet-frequency-graph")],
                                ),
                            ]
                        ),
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="tweet-source-graph")],
                        ),
                        
                    ],
                )

mentioned_foers_layout = html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="most-mentioned-graph")],
                        ),
                        html.Div(
                            className="six columns",
                            children=[dcc.Graph(id="friends-foers-count-graph")],
                        ),
                        
                    ],
                )

top5_tweets_layout = html.Div(
                    className="row",
                    children=[
                        html.Div(
                            className="six columns",
                            children=[
                                html.H6("Top 5 Most Liked Tweets"),
                                dash_table.DataTable(
                                        id="most-liked-table",
                                        columns=[{"name": i, "id": i} for i in ['created_at', 'text', 'favorite_count']],
                                        style_header=table_header_style,
                                        style_data={
                                            'whiteSpace': 'normal',
                                            'height': '400',
                                        },
                                    )
                            ],
                        ),
                        html.Div(
                            className="six columns",
                            children=[
                                html.H6("Top 5 Most Retweeted Tweets"),
                                dash_table.DataTable(
                                        id="most-rt-table",
                                        columns=[{"name": i, "id": i} for i in ['created_at', 'text', 'retweet_count']],
                                        style_header=table_header_style,
                                        style_data={
                                            'whiteSpace': 'normal',
                                            'height': '400',
                                        },
                                    )
                            ],
                        ),
                    ],
                )

final_layout = html.Div(
                    className="row",
                    children=[
                        html.Div([
                            html.H6("Wordcloud"),
                            html.Img(src=app.get_asset_url("download.png")),
                        ])
                    ],
                )

bottom_layout = html.Div(
                    className="row",
                    children=[
                        html.Label("Designed & Implemented by Momo 2020.")
                    ],
                    style={
                        'text-align': 'center',
                        'margin-top': '10px',
                    }
                )

container_layout = html.Div(
            className="container",
            children=[
                user_selection_layout, top_layout, tweet_frequency_source_layout, mentioned_foers_layout, top5_tweets_layout, #final_layout
                bottom_layout
            ],
        )

layout = html.Div(
    className="",
    children=[banner_layout, container_layout]
)