import streamlit as st
import pandas as pd
import numpy as np
import redis
import re
import json

st.set_page_config(layout="wide")
st.title('MobileInsight-Cloud')

r = redis.Redis(
    host='127.0.0.1',
    port=6379
)

@st.cache_data
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

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data)
    # Convert 'order' column to integer type for proper sorting
    df['order'] = df['order'].astype(int)

    # Sort the DataFrame by 'filename' and 'order'
    df_sorted = df.sort_values(by=['filename', 'order'])

    # Reset the index
    df_sorted.reset_index(drop=True, inplace=True)
    return df_sorted

def filter_df(keys_df, filename_selector, type_id_selector):
    if filename_selector:
        keys_df = keys_df[keys_df['filename'].isin(filename_selector)]
    if type_id_selector:
        keys_df = keys_df[keys_df['type_id'].isin(type_id_selector)]
    return keys_df

keys_df = load_data()

filename_selector = st.multiselect(
    "Filename",
    keys_df['filename'].unique(),
    []
)

type_id_selector = st.multiselect(
    "type_id",
    keys_df['type_id'].unique(),
    []
)

keys_filtered_df = filter_df(keys_df, filename_selector, type_id_selector)
key_table = st.dataframe(keys_filtered_df[['filename', 'type_id', 'timestamp', 'order']], on_select="rerun", selection_mode="single-row")

@st.cache_data
def download_json(selected_json):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return json.dumps(selected_json)

if key_table['selection']['rows']:
    selected_json = r.json().get(keys_df.iloc[key_table['selection']['rows'][0]]['original_key'])
    st.download_button(
        label="Download JSON",
        data=download_json(selected_json),
        file_name=f'selected.json',
        mime="application/json",
    )
    st.json(selected_json)