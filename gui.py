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
import time
from pymongo import MongoClient
from gridfs import GridFS
from streamlit_js_eval import streamlit_js_eval

from mobile_insight.analyzer.analyzer import *
from mobile_insight.monitor import OfflineReplayer
from my_analyzer import my_analysis, download_bytes
from config import PAGE_TOP_STYLE

# st.set_page_config(layout='wide')
screen_inner_width, screen_inner_height = 0, 0
st.title('MobileInsight-Cloud')
st.markdown(PAGE_TOP_STYLE, unsafe_allow_html=True)
cur_path = os.getcwd()
screen_inner_width = streamlit_js_eval(js_expressions='parent.window.innerWidth', key = 'SCR')
screen_inner_height = streamlit_js_eval(js_expressions='parent.window.innerHeight', key = 'SCR1')
time.sleep(0.1)
client = MongoClient('localhost', 27017)
db = client['mobile_insight']
fs = GridFS(db)

def transform_datetime(date_string):
    # Define the format of the date string
    date_format = '%Y-%m-%d %H:%M:%S.%f'
    # Parse the string into a datetime object
    date_object = datetime.strptime(date_string, date_format)
    return date_object

@st.cache_data
def load_data(filename):
    df = pd.DataFrame(db[filename].find({}, {'type_id': 1, 'timestamp': 1, 'order': 1, '_id': 0}))

    # Sort the DataFrame by 'filename' and 'order'
    df_sorted = df.sort_values(by=['order'])

    # Reset the index
    df_sorted.reset_index(drop=True, inplace=True)
    return df_sorted

def upload_log(uploaded_log):
    bytes_log = uploaded_log.getvalue()
    log_name = uploaded_log.name
    stats = my_analysis(bytes_log)
    if len(stats.field_list) > 0:
        # stats.field_list = log messages in each log file
        log_json = stats.field_list
        # with open('tmp.json', 'w') as f:
        #     json.dump(log_json, f, indent=4)
        collection = db[log_name]
        if log_name in db.list_collection_names():
            collection.delete_many({})
        collection.create_index([('type_id', 1), ('timestamp', 1), ('order', 1)])

        processed_data = []
        batch_size = 1024
        for e, content in enumerate(log_json):
            content['order'] = e
            content['timestamp'] = transform_datetime(content['timestamp'])
            if 'Subpackets' in content:
                if isinstance(content['Subpackets'], list):
                    for sub in content['Subpackets']:
                        if 'SRB Ciphering Keys' in sub:
                            sub['SRB Ciphering Keys'] = str(sub['SRB Ciphering Keys'])
                            sub['DRB Ciphering Keys'] = str(sub['DRB Ciphering Keys'])

            processed_data.append(content)

        # Function to split list into chunks
        def chunk_list(data, chunk_size):
            for i in range(0, len(data), chunk_size):
                yield data[i:i + chunk_size]
        # Insert in batches
        for batch in chunk_list(processed_data, batch_size):
            collection.insert_many(batch)

        mi2log_collection = db['mi2log']
        # Check if the file already exists
        existing_file = mi2log_collection.find_one({'filename': log_name})
        if existing_file:
            # Delete the existing file from GridFS if you want to replace it
            fs.delete(existing_file['data_id'])

        # Save the large file in GridFS
        file_id = fs.put(bytes_log, filename=log_name)

        # Upsert the document with the GridFS file reference
        mi2log_collection.update_one(
            {'filename': log_name},
            {
                '$set': {
                    'upload_time': datetime.now(),
                    'data_id': file_id  # Store reference to GridFS file
                }
            },
            upsert=True
        )

# @st.cache_data
def download_json(selected_json):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return json.dumps(selected_json, indent=4)

@st.cache_data
def download_mi2log(args):
    return download_bytes(args)

display_tab, upload_tab, manage_files_tab = st.tabs(['Display', 'Upload', 'Manage Files'])

if 'file_uploader_key' not in st.session_state:
    st.session_state['file_uploader_key'] = 0
if 'new_filename_text_input_key' not in st.session_state:
    st.session_state['new_filename_text_input_key'] = 0

with upload_tab:
    uploaded_log = st.file_uploader('Choose a file', key=f'file_uploader_key_{st.session_state["file_uploader_key"]}', accept_multiple_files=True)
    if len(uploaded_log) > 0:
        progress_text = 'Uploading mi2log file...'
        progress_bar = st.progress(0, text=progress_text)
        # with st.status('Uploading mi2log file...'):
        start_time = time.time()
        for e, log in enumerate(uploaded_log):
            upload_log(log)
            progress_bar.progress(int((e + 1) / len(uploaded_log) * 100), text=progress_text + f'({(e+1)}/{len(uploaded_log)})')
            st.info(f'Successfully uploaded {log.name}')
        time.sleep(1)
        progress_bar.empty()
        # st.success(f'Finish uploading with {time.time() - start_time} seconds', icon='✅')
        st.success(f'Finish uploading', icon='✅')
        time.sleep(2)
        st.session_state['file_uploader_key'] += 1
        st.rerun()

with manage_files_tab:
    files_df = pd.DataFrame(db['mi2log'].find({}, {'filename': 1, 'upload_time': 1, '_id': 0}).sort('upload_time', 1))
    files_df.reset_index(drop=True, inplace=True)
    if not files_df.empty:
        files_table = st.dataframe(files_df, on_select='rerun', selection_mode='multi-row')
        left, mid, right = st.columns(10)[:3]
        with left.popover('Rename'):
            if len(files_table['selection']['rows']) == 1:
                new_filename = st.text_input('New Filename', key=f'new_filename_text_input_key_{st.session_state["new_filename_text_input_key"]}')
                if files_table['selection']['rows'] and new_filename != '':
                    for row in files_table['selection']['rows']:
                        old_filename = files_df.iloc[row]['filename']
                        db['mi2log'].update_one(
                            {'filename': old_filename},  # Find the document with the old filename
                            {'$set': {'filename': new_filename}}  # Update the filename
                        )
                        db[old_filename].rename(new_filename)
                        st.session_state['new_filename_text_input_key'] += 1
                    st.rerun()
            else:
                st.error(f'You can only rename one file at a time')
        if mid.button('Delete'):
            if len(files_table['selection']['rows']) > 0:
                for row in files_table['selection']['rows']:
                    filename = files_df.iloc[row]['filename']
                    fs.delete(db['mi2log'].find_one({'filename': filename})['data_id'])
                    db['mi2log'].delete_one({'filename': filename})
                    db.drop_collection(filename)
                st.rerun()
            else:
                st.error(f'Please choose at least one file to delete')
        if right.button('Delete All'):
            client.drop_database('mobile_insight')
            st.rerun()
    else:
        st.write('No records in MongoDB')

with display_tab:
    filename_list = [doc['filename'] for doc in db['mi2log'].find({}, {'filename': 1, '_id': 0}).sort('upload_time', 1)]

    if filename_list:
        with st.popover(f"`{st.session_state['filename_selector'] if 'filename_selector' in st.session_state else filename_list[0]}`"):

            filename_selector = st.selectbox(
                'Filename',
                filename_list,
                key='filename_selector'
            )
            keys_df = load_data(filename_selector)

            type_id_selector = st.multiselect(
                'type_id',
                keys_df['type_id'].unique(),
                []
            )
            if type_id_selector:
                keys_df = keys_df[keys_df['type_id'].isin(type_id_selector)]

            hours = [f'{i:02d}' for i in range(24)]
            minutes = [f'{i:02d}' for i in range(60)]
            seconds = [f'{i:02d}' for i in range(60)]

            start_date_col, start_time_col = st.columns([0.5, 1])
            start_date_selector = start_date_col.date_input('Start Date', keys_df['timestamp'].min())
            start_hour_col, start_minute_col, start_second_col = start_time_col.columns(3)
            start_hour_selector = start_hour_col.selectbox('Start Hour', options=hours, index=keys_df['timestamp'].min().hour)
            start_minute_selector = start_minute_col.selectbox('Start Minute', options=minutes, index=keys_df['timestamp'].min().minute)
            start_second_selector = start_second_col.selectbox('Start Second', options=seconds, index=keys_df['timestamp'].min().second)

            end_date_col, end_time_col = st.columns([0.5, 1])
            end_date_selector = end_date_col.date_input('End Date', keys_df['timestamp'].max())
            end_hour_col, end_minute_col, end_second_col = end_time_col.columns(3)
            end_hour_selector = end_hour_col.selectbox('End Hour', options=hours, index=keys_df['timestamp'].max().hour)
            end_minute_selector = end_minute_col.selectbox('End Minute', options=minutes, index=keys_df['timestamp'].max().minute)
            end_second_selector = end_second_col.selectbox('End Second', options=seconds, index=keys_df['timestamp'].max().second+1)

            # Combine the date and time inputs for start and end time into a full datetime object
            start_date = pd.to_datetime(f'{start_date_selector} {start_hour_selector}:{start_minute_selector}:{start_second_selector}')
            end_date = pd.to_datetime(f'{end_date_selector} {end_hour_selector}:{end_minute_selector}:{end_second_selector}')

            if start_date > end_date:
                st.error('Start time cannot be later than end time.')

            keys_df = keys_df[(keys_df['timestamp'] >= start_date) & (keys_df['timestamp'] < end_date)]
            keys_df.reset_index(drop=True, inplace=True)

            keys_filtered_args = {
                'filename': filename_selector,
                'type_id': type_id_selector,
                'start_date': start_date,
                'end_date': end_date
            }

            left_right_ratio = st.slider('Ratio', min_value=1, max_value=99, value=50)
        left_column, right_column = st.columns([left_right_ratio, 100 - left_right_ratio])

        
        left_button, right_button = left_column.columns(2)
        left_button.download_button(
            label='Download Filtered mi2log File',
            data=download_mi2log(keys_filtered_args),
            file_name='filtered_log.mi2log',
            mime='application/octet-stream',
        )               

        filtered_json_args = {
            'type_id': {'$in': keys_filtered_args['type_id']},
            'timestamp': {'$gte': keys_filtered_args['start_date'], '$lt': keys_filtered_args['end_date']},
        }
        filtered_json = list(db[filename_selector].find(filtered_json_args, {'_id': 0}))
        for js in filtered_json:
            js['timestamp'] = js['timestamp'].isoformat()

        right_button.download_button(
            label='Download Filtered JSON',
            data=download_json(filtered_json),
            file_name='filtered_log.json',
            mime='application/json',
        )

        key_table = left_column.dataframe(keys_df[['type_id', 'timestamp', 'order']], on_select='rerun', selection_mode='single-row', width=screen_inner_width // 2, height=screen_inner_height - 360)

        if key_table['selection']['rows']:
            selected_json = db[filename_selector].find_one(keys_df.iloc[key_table['selection']['rows'][0]].to_dict(), {'_id': 0})
            selected_json['timestamp'] = selected_json['timestamp'].isoformat()

            right_column.download_button(
                label='Download Selected JSON',
                data=download_json(selected_json),
                file_name='selected_log.json',
                mime='application/json',
            )
            with right_column.container(height=screen_inner_height - 360):
                st.json(selected_json)

    else:
        st.write('No records in MongoDB')
