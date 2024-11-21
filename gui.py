# Standard Library Imports
import time
from datetime import datetime
import json

# Third-Party Library Imports
import streamlit as st
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from gridfs import GridFS
import plotly.express as px
from streamlit_js_eval import streamlit_js_eval

# Local Imports
from my_analyzer import my_analysis, download_bytes
from config import PAGE_TOP_STYLE


# Streamlit App Setup
def initialize_app() -> tuple[str, str]:
    """
    Set up Streamlit application and global variables.
    """
    # st.set_page_config(layout='wide')
    st.title("MobileInsight-Cloud")
    st.markdown(PAGE_TOP_STYLE, unsafe_allow_html=True)

    # Screen Dimensions
    screen_width = streamlit_js_eval(
        js_expressions="parent.window.innerWidth", key="screen_width"
    )
    screen_height = streamlit_js_eval(
        js_expressions="parent.window.innerHeight", key="screen_height"
    )
    time.sleep(0.1)  # Small delay for accurate size capture

    return screen_width, screen_height


# Database Initialization
def initialize_database(
    host: str = "localhost", port: int = 27017, db_name: str = "mobile_insight"
):
    """
    Connect to MongoDB and initialize GridFS.
    """
    client = MongoClient(host, port)
    database = client[db_name]
    file_storage = GridFS(database)
    return client, database, file_storage


# Helper function for datetime transformation
def transform_datetime(
    date_string: str, date_format: str = "%Y-%m-%d %H:%M:%S.%f"
) -> datetime:
    """
    Converts a date string into a datetime object based on the given format.

    Args:
        date_string (str): The date string to transform.
        date_format (str): The format of the date string (default: '%Y-%m-%d %H:%M:%S.%f').

    Returns:
        datetime: The corresponding datetime object.
    """
    try:
        return datetime.strptime(date_string, date_format)
    except ValueError as e:
        st.error(f"Invalid date format: {e}")
        return None


@st.cache_data
def load_data(filename: str) -> pd.DataFrame:
    """
    Loads data from the MongoDB collection into a Pandas DataFrame.

    Args:
        filename (str): The name of the MongoDB collection.

    Returns:
        pd.DataFrame: A sorted DataFrame containing data from the collection.
    """
    try:
        data = db[filename].find(
            {}, {"type_id": 1, "timestamp": 1, "order": 1, "_id": 0}
        )
        df = pd.DataFrame(data)
        return df.sort_values(by="order").reset_index(drop=True)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def upload_log(uploaded_log) -> None:
    """
    Processes and uploads a log file into the database, with its content stored in MongoDB and GridFS.

    Args:
        uploaded_log: The file uploaded via Streamlit's file uploader.
    """
    bytes_log = uploaded_log.getvalue()
    log_name = uploaded_log.name
    stats = my_analysis(bytes_log)

    if not stats.field_list:
        st.warning("No valid fields found in the uploaded log.")
        return

    log_json = stats.field_list
    collection = db[log_name]

    # Clear existing collection if it already exists
    if log_name in db.list_collection_names():
        collection.delete_many({})
    collection.create_index([("type_id", 1), ("timestamp", 1), ("order", 1)])

    # Process and insert log data in batches
    batch_size = 1024
    processed_data = []
    for idx, entry in enumerate(log_json):
        entry["order"] = idx
        entry["timestamp"] = transform_datetime(entry["timestamp"])
        if "Subpackets" in entry and isinstance(entry["Subpackets"], list):
            for sub in entry["Subpackets"]:
                if "SRB Ciphering Keys" in sub:
                    sub["SRB Ciphering Keys"] = str(sub["SRB Ciphering Keys"])
                    sub["DRB Ciphering Keys"] = str(sub["DRB Ciphering Keys"])
        processed_data.append(entry)

    # Function to insert data in chunks
    def batch_insert(data, collection):
        for chunk in (
            data[i : i + batch_size] for i in range(0, len(data), batch_size)
        ):
            try:
                collection.insert_many(chunk)
            except BulkWriteError as e:
                st.error(f"Batch insert error: {e}")

    batch_insert(processed_data, collection)

    # Handle GridFS for storing the log file
    mi2log_collection = db["mi2log"]
    existing_file = mi2log_collection.find_one({"filename": log_name})
    if existing_file:
        fs.delete(existing_file["data_id"])

    file_id = fs.put(bytes_log, filename=log_name)
    mi2log_collection.update_one(
        {"filename": log_name},
        {"$set": {"upload_time": datetime.now(), "data_id": file_id}},
        upsert=True,
    )


def create_datetime_selector() -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Create start date and end data selector.

    Returns:
        start_date (str): The date string to transform.
        end_date (str): The format of the date string (default: '%Y-%m-%d %H:%M:%S.%f').
    """
    hours = [f"{i:02d}" for i in range(24)]
    minutes = [f"{i:02d}" for i in range(60)]
    seconds = [f"{i:02d}" for i in range(60)]

    start_date_col, start_time_col = st.columns([0.5, 1])
    start_date_selector = start_date_col.date_input(
        "Start Date", keys_df["timestamp"].min()
    )
    start_hour_col, start_minute_col, start_second_col = start_time_col.columns(3)
    start_hour_selector = start_hour_col.selectbox(
        "Start Hour", options=hours, index=keys_df["timestamp"].min().hour
    )
    start_minute_selector = start_minute_col.selectbox(
        "Start Minute", options=minutes, index=keys_df["timestamp"].min().minute
    )
    start_second_selector = start_second_col.selectbox(
        "Start Second", options=seconds, index=keys_df["timestamp"].min().second
    )

    end_date_col, end_time_col = st.columns([0.5, 1])
    end_date_selector = end_date_col.date_input("End Date", keys_df["timestamp"].max())
    end_hour_col, end_minute_col, end_second_col = end_time_col.columns(3)
    end_hour_selector = end_hour_col.selectbox(
        "End Hour", options=hours, index=keys_df["timestamp"].max().hour
    )
    end_minute_selector = end_minute_col.selectbox(
        "End Minute", options=minutes, index=keys_df["timestamp"].max().minute
    )
    end_second_selector = end_second_col.selectbox(
        "End Second", options=seconds, index=keys_df["timestamp"].max().second + 1
    )

    # Combine the date and time inputs for start and end time into a full datetime object
    start_date = pd.to_datetime(
        f"{start_date_selector} {start_hour_selector}:{start_minute_selector}:{start_second_selector}"
    )
    end_date = pd.to_datetime(
        f"{end_date_selector} {end_hour_selector}:{end_minute_selector}:{end_second_selector}"
    )

    return start_date, end_date


@st.cache_data
def download_json(filter_args: dict) -> str:
    """
    Retrieves and converts filtered MongoDB data to a JSON string.

    Args:
        filter_args (dict): Query parameters for filtering the data.

    Returns:
        str: JSON-formatted string of the filtered data.
    """
    try:
        filtered_data = list(db[filename_selector].find(filter_args, {"_id": 0}))
        for entry in filtered_data:
            entry["timestamp"] = entry["timestamp"].isoformat()
        if len(filtered_data) == 1:
            return json.dumps(filtered_data[0], indent=4)
        return json.dumps(filtered_data, indent=4)
    except Exception as e:
        st.error(f"Error downloading JSON: {e}")
        return "{}"


@st.cache_data
def download_mi2log(args: dict) -> bytes:
    """
    Returns bytes for downloading mi2log data using an external utility function.

    Args:
        args (dict): Arguments for filtering and processing mi2log data.

    Returns:
        bytes: Processed mi2log file content.
    """
    try:
        return download_bytes(args)
    except Exception as e:
        st.error(f"Error downloading mi2log: {e}")
        return b""


# Initialize App
screen_inner_width, screen_inner_height = initialize_app()
INNER_HEIGHT_DELTA = 360

# Initialize Database
mongo_client, db, fs = initialize_database()

# Tabs for different functionalities
display_tab, upload_tab, manage_files_tab = st.tabs(
    ["Display", "Upload", "Manage Files"]
)

# Initialize session state keys if not already present
st.session_state.setdefault("file_uploader_key", 0)
st.session_state.setdefault("new_filename_text_input_key", 0)

# --- Upload Tab ---
with upload_tab:
    uploaded_logs = st.file_uploader(
        "Choose a file",
        key=f'file_uploader_key_{st.session_state["file_uploader_key"]}',
        accept_multiple_files=True,
    )

    if uploaded_logs:
        progress_text = "Uploading mi2log files..."
        progress_bar = st.progress(0, text=progress_text)
        start_time = time.time()

        for idx, log in enumerate(uploaded_logs):
            upload_log(log)
            progress_percent = int((idx + 1) / len(uploaded_logs) * 100)
            progress_bar.progress(
                progress_percent,
                text=f"{progress_text} ({idx + 1}/{len(uploaded_logs)})",
            )
            st.info(f"Successfully uploaded {log.name}")

        st.success(
            f"Finished uploading in {time.time() - start_time:.2f} seconds", icon="✅"
        )
        st.session_state["file_uploader_key"] += 1
        time.sleep(1)  # For display success message
        st.rerun()

# --- Manage Files Tab ---
with manage_files_tab:
    files_df = pd.DataFrame(
        db["mi2log"]
        .find({}, {"filename": 1, "upload_time": 1, "_id": 0})
        .sort("upload_time", 1)
    ).reset_index(drop=True)

    if not files_df.empty:
        files_table = st.dataframe(
            files_df, on_select="rerun", selection_mode="multi-row"
        )

        left, mid, right = st.columns(10)[:3]
        with left.popover("Rename"):
            if len(files_table["selection"]["rows"]) == 1:
                selected_row = files_table["selection"]["rows"][0]
                old_filename = files_df.iloc[selected_row]["filename"]
                new_filename = st.text_input(
                    "New Filename",
                    key=f'new_filename_text_input_key_{st.session_state["new_filename_text_input_key"]}',
                )

                if new_filename:
                    db["mi2log"].update_one(
                        {"filename": old_filename}, {"$set": {"filename": new_filename}}
                    )
                    db[old_filename].rename(new_filename)
                    st.session_state["new_filename_text_input_key"] += 1
                    st.rerun()
            else:
                st.error("You can only rename one file at a time.")

        with mid:
            if st.button("Delete Selected"):
                if files_table["selection"]["rows"]:
                    for row_idx in files_table["selection"]["rows"]:
                        filename = files_df.iloc[row_idx]["filename"]
                        file_id = db["mi2log"].find_one({"filename": filename})[
                            "data_id"
                        ]
                        fs.delete(file_id)
                        db["mi2log"].delete_one({"filename": filename})
                        db.drop_collection(filename)
                    st.rerun()
                else:
                    st.error("Please select at least one file to delete.")

        with right:
            if st.button("Delete All Files"):
                mongo_client.drop_database("mobile_insight")
                st.rerun()
    else:
        st.info("No records found in MongoDB.")

# --- Display Tab ---
with display_tab:
    filename_list = [
        doc["filename"]
        for doc in db["mi2log"]
        .find({}, {"filename": 1, "_id": 0})
        .sort("upload_time", 1)
    ]

    if filename_list:
        with st.popover(
            f"`{st.session_state['filename_selector'] if 'filename_selector' in st.session_state else filename_list[0]}`",
            help="Click here for filtering and display adjustment",
        ):
            filename_selector = st.selectbox(
                "Filename", filename_list, key="filename_selector"
            )
            keys_df = load_data(filename_selector)

            # Filtering options
            type_id_selector = st.multiselect(
                "type_id", keys_df["type_id"].unique(), []
            )
            if type_id_selector:
                keys_df = keys_df[keys_df["type_id"].isin(type_id_selector)]

            # Datetime Filtering
            start_date, end_date = create_datetime_selector()

            if start_date > end_date:
                st.error("Start time cannot be later than end time.")

            keys_df = keys_df[
                (keys_df["timestamp"] >= start_date) & (keys_df["timestamp"] < end_date)
            ].reset_index(drop=True)

            keys_filtered_args = {
                "filename": filename_selector,
                "type_id": type_id_selector,
                "start_date": start_date,
                "end_date": end_date,
            }

            left_right_ratio = st.slider(
                "Ratio",
                min_value=1,
                max_value=99,
                value=50,
                help="Adjust the ratio of dataframe and selected json data",
            )
            timestamp_scale = st.slider(
                "Timestamp Scale (s)",
                min_value=1,
                max_value=60,
                value=5,
                help="Adjust the timestamp scale in the bar chart",
            )
        left_column, right_column = st.columns(
            [left_right_ratio, 100 - left_right_ratio]
        )

        left_button, right_button = left_column.columns(2)
        left_button.download_button(
            label="Download Filtered mi2log File",
            data=download_mi2log(keys_filtered_args),
            file_name="filtered_log.mi2log",
            mime="application/octet-stream",
        )

        filtered_json_args = {
            "type_id": {"$in": keys_filtered_args["type_id"]},
            "timestamp": {
                "$gte": keys_filtered_args["start_date"],
                "$lt": keys_filtered_args["end_date"],
            },
        }

        right_button.download_button(
            label="Download Filtered JSON",
            data=download_json(filtered_json_args),
            file_name="filtered_log.json",
            mime="application/json",
        )

        # Create a DataFrame for visualization
        keys_df["timestamp_aggregate"] = keys_df["timestamp"].dt.floor(
            f"{timestamp_scale}s"
        )
        timestamp_counts = keys_df["timestamp_aggregate"].value_counts().sort_index()
        count_df = timestamp_counts.reset_index()
        count_df.columns = ["timestamp", "count"]
        fig = px.bar(count_df, x="timestamp", y="count")

        num_records_col, records_chart_col = st.columns([0.1, 0.9])
        timestamp_selector = records_chart_col.plotly_chart(fig, on_select="rerun")
        st.info(
            'Select the bars to filter the dataframe. Click "Pan" for single selection and "Box Select" or "Lasso Select" for multiple selection. Double click the selected bars to unselect'
        )
        if timestamp_selector["selection"]["points"]:
            keys_df = keys_df[
                keys_df["timestamp_aggregate"].isin(
                    [d["x"] for d in timestamp_selector.selection["points"]]
                )
            ].reset_index(drop=True)

        key_table = left_column.dataframe(
            keys_df[["type_id", "timestamp", "order"]],
            on_select="rerun",
            selection_mode="single-row",
            width=screen_inner_width // 2,
            height=screen_inner_height - INNER_HEIGHT_DELTA,
        )
        num_records_col.metric("Number of Records", len(keys_df))

        if key_table["selection"]["rows"]:
            selected_json_args = keys_df.iloc[key_table["selection"]["rows"][0]][
                ["type_id", "timestamp", "order"]
            ].to_dict()

            right_column.download_button(
                label="Download Selected JSON",
                data=download_json(selected_json_args),
                file_name="selected_log.json",
                mime="application/json",
            )
            with right_column.container(
                height=screen_inner_height - INNER_HEIGHT_DELTA
            ):
                st.json(download_json(selected_json_args))

    else:
        st.info("No records in MongoDB")
