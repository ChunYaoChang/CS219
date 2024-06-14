import streamlit as st
import pandas as pd
import numpy as np
import redis
from redis.commands.json.path import Path
import re
import json
import os
import xml.etree.cElementTree as ET 
from datetime import datetime, timedelta
from streamlit_date_picker import date_range_picker, PickerType
import subprocess
import pickle
import time

from mobile_insight.analyzer.analyzer import *
from mobile_insight.monitor import OfflineReplayer
from my_analyzer import my_analysis

st.set_page_config(layout="wide")
st.title('MobileInsight-Cloud')
cur_path = os.getcwd()

r = redis.Redis(
    host='127.0.0.1',
    port=6379
)

def transform_datetime(date_string):
    # Define the format of the date string
    date_format = "%Y-%m-%d %H-%M-%S.%f"
    # Parse the string into a datetime object
    date_object = datetime.strptime(date_string, date_format)
    return date_object


# @st.cache_data
def load_data():
    keys = [s.decode() for s in r.keys()]
    # Define a regular expression pattern to extract filename, type_id, timestamp, and order
    pattern = re.compile(r"(?P<filename>[^:]+):(?P<type_id>[^:]+):(?P<timestamp>[^:]+):(?P<order>[^:]+)")

    # Extract filename and type_id from each key using regular expressions
    data = []
    for key in keys:
        match = pattern.match(key)
        if match:
            data_dict = match.groupdict()
            data_dict["original_key"] = key
            data.append(data_dict)

    if not data:
        return pd.DataFrame()

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data)
    # Convert 'order' column to integer type for proper sorting
    df['order'] = df['order'].astype(int)
    df['timestamp'] = df['timestamp'].apply(transform_datetime)

    # Sort the DataFrame by 'filename' and 'order'
    df_sorted = df.sort_values(by=['filename', 'order'])

    # Reset the index
    df_sorted.reset_index(drop=True, inplace=True)
    return df_sorted

def filter_df(keys_df, filename_selector, type_id_selector, datetime_selector):

    start_date, end_date = None, None

    if filename_selector:
        keys_df = keys_df[keys_df['filename'] == filename_selector]

    if datetime_selector:
        date_format = "%Y-%m-%d %H:%M:%S"
        start_date = datetime.strptime(datetime_selector[0], date_format)
        end_date = datetime.strptime(datetime_selector[1], date_format)
        keys_df = keys_df[(keys_df['timestamp'] >= start_date) & (keys_df['timestamp'] <= end_date)]

    if type_id_selector:
        keys_df = keys_df[keys_df['type_id'].isin(type_id_selector)]

    args = {
        'filename': filename_selector,
        'type_ids': type_id_selector,
        'start_date': start_date,
        'end_date': end_date
    }

    return keys_df, args

def upload_log(uploaded_log):
    bytes_log = uploaded_log.getvalue()
    log_name = uploaded_log.name
    stats = my_analysis(log_name)
    log_json = {}
    if len(stats.field_list) > 0:
        # stats.field_list = log messages in each log file
        log_json[log_name] = stats.field_list

    categorized_items = {}

    for filename, file_contents in log_json.items():
        if filename not in categorized_items:
            categorized_items[filename] = {}
        for e, content in enumerate(file_contents):
            type_id = content['type_id']
            if type_id not in categorized_items[filename]:
                categorized_items[filename][type_id] = []
            content['order'] = e
            content['filename'] = filename
            categorized_items[filename][type_id].append(content)

    for filename, file_contents in categorized_items.items():
        r.set(f'{filename}:mi2log', bytes_log)
        for type_id, contents in file_contents.items():
            for content in contents:
                r.json().set(f'{filename}:{type_id}:{content["timestamp"].replace(":", "-")}:{content["order"]}', Path.root_path(), content)

display_tab, upload_tab = st.tabs(["Display", "Upload"])

with display_tab:
    keys_df = load_data()
    if not keys_df.empty:
        filename_selector = st.selectbox(
            "Filename",
            keys_df['filename'].unique()
        )
        keys_df = keys_df[keys_df['filename'] == filename_selector]
        type_id_selector = st.multiselect(
            "type_id",
            keys_df['type_id'].unique(),
            []
        )
        st.markdown('timestamp')
        datetime_selector = date_range_picker(picker_type=PickerType.time,
                                            start=keys_df['timestamp'].min() + timedelta(hours=8), end=keys_df['timestamp'].max() + timedelta(hours=8, seconds=1),
                                            key='time_range_picker')

        keys_filtered_df, keys_filtered_args = filter_df(keys_df, filename_selector, type_id_selector, datetime_selector)
        left_column, right_column = st.columns(2)


        # @st.cache_data
        def download_json(selected_json):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return json.dumps(selected_json)
        
        left_button, right_button = left_column.columns(2)
        if left_button.button(label="Download Filtered mi2log file"):
            # Run the script and capture the output
            with left_column.status("Downloading mi2log file..."):
                result = subprocess.run(['python', 'download_mi2log.py', repr(pickle.dumps(keys_filtered_args))], capture_output=True, text=True)

        filtered_json = list(keys_filtered_df['original_key'].apply(lambda k : r.json().get(k))),
        right_button.download_button(
            label="Download Filtered JSON",
            data=download_json(filtered_json),
            file_name='filtered_log.json',
            mime="application/json",
        )
        key_table = left_column.dataframe(keys_filtered_df[['filename', 'type_id', 'timestamp', 'order']], on_select="rerun", selection_mode="single-row")
            
        if key_table['selection']['rows']:
            selected_json = r.json().get(keys_filtered_df.iloc[key_table['selection']['rows'][0]]['original_key'])
            right_column.download_button(
                label="Download Selected JSON",
                data=download_json(selected_json),
                file_name='selected_log.json',
                mime="application/json",
            )
            right_column.json(selected_json)

    else:
        st.write("No records in Redis")

with upload_tab:
    uploaded_log = st.file_uploader("Choose a file", accept_multiple_files=True)
    if len(uploaded_log) > 0:
        progress_text = "Uploading mi2log file..."
        progress_bar = st.progress(0, text=progress_text)
        # with st.status("Uploading mi2log file..."):
        start_time = time.time()
        for e, log in enumerate(uploaded_log):
            upload_log(log)
            progress_bar.progress(int((e + 1) / len(uploaded_log) * 100), text=progress_text + f'({(e+1)}/{len(uploaded_log)})')
        time.sleep(1)
        progress_bar.empty()
        # st.success(f'Finish uploading with {time.time() - start_time} seconds', icon="✅")
        st.success(f'Finish uploading', icon="✅")
