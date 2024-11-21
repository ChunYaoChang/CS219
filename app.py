import streamlit as st
from pymongo import MongoClient
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# --- Streamlit Page Setup ---
st.set_page_config(layout="wide")

# --- MongoDB Client ---
client = MongoClient("localhost", 27017)
db = client["credentials"]

# --- Load Configuration ---
CONFIG_FILE = "credential.yml"

try:
    with open(CONFIG_FILE) as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error(f"Configuration file '{CONFIG_FILE}' not found.")
    st.stop()
except yaml.YAMLError as e:
    st.error(f"Error loading configuration file: {e}")
    st.stop()

# --- Authentication Setup ---
authenticator = stauth.Authenticate(
    credentials=CONFIG_FILE,
    cookie_name=config["cookie"]["name"],
    cookie_key=config["cookie"]["key"],
    cookie_expiry_days=config["cookie"]["expiry_days"],
)


def default():
    st.title("MobileInsight-Cloud")


# --- Helper Functions ---
def show_login_status():
    """
    Display appropriate sidebar messages based on authentication status.
    """
    authenticator.login("sidebar")
    if st.session_state.get("authentication_status") is True:
        st.sidebar.success(f"Logged in as {st.session_state['username']}")
        st.sidebar.title(f'Welcome, {st.session_state["username"]}')
        authenticator.logout(location="sidebar")
    else:
        if st.session_state.get("authentication_status") is False:
            st.sidebar.error("Invalid username or password")
        else:
            st.sidebar.warning("Please enter your credentials")
        try:
            email, username, name = authenticator.register_user("sidebar")
            if email:
                st.sidebar.success("User registered successfully!")
        except Exception as e:
            st.sidebar.error(f"Registration failed: {e}")


def register_new_user():
    """
    Allow users to register new accounts from the sidebar.
    """
    try:
        email, username, name = authenticator.register_user("sidebar")
        if email:
            st.sidebar.success("User registered successfully!")
    except Exception as e:
        st.sidebar.error(f"Registration failed: {e}")


gui = st.Page("gui.py", title="Mobile Insight", icon=":material/dashboard:")
default_page = st.Page(default, title="Login", icon=":material/login:")

show_login_status()

if st.session_state["authentication_status"]:
    pg = st.navigation({"Reports": [gui]})
elif st.session_state["authentication_status"] is False:
    pg = st.navigation({"Reports": [default_page]})
elif st.session_state["authentication_status"] is None:
    pg = st.navigation({"Reports": [default_page]})

pg.run()
