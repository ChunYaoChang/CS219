import streamlit as st
import time
from pymongo import MongoClient
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from config import PAGE_TOP_STYLE

with open('credential.yml') as file:
    config = yaml.load(file, Loader=SafeLoader)
st.set_page_config(layout='wide')
# st.title('MobileInsight-Cloud')
# st.markdown(PAGE_TOP_STYLE, unsafe_allow_html=True)

# Pre-hashing all plain text passwords once
# stauth.Hasher.hash_passwords(config['credentials'])

authenticator = stauth.Authenticate(
    'credential.yml',
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)
client = MongoClient('localhost', 27017)
db = client['credentials']

def default():
    st.title('MobileInsight-Cloud')

gui = st.Page("gui.py", title="GUI", icon=":material/dashboard:")
default_page = st.Page(default, title="Login", icon=':material/login:')

try:
    authenticator.login('sidebar')
    if st.session_state['authentication_status']:
        st.sidebar.success('Login successfully')
    elif st.session_state['authentication_status'] is False:
        st.sidebar.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] is None:
        st.sidebar.warning('Please enter your username and password')
except Exception as e:
    st.error(e)

if st.session_state['authentication_status']:
    try:
        st.sidebar.title(f'Welcome, {st.session_state["username"]}')
        authenticator.logout(location='sidebar')
    except Exception as e:
        st.error(e)
else:
    try:
        email_of_registered_user, \
        username_of_registered_user, \
        name_of_registered_user = authenticator.register_user('sidebar')
        # st.write(email_of_registered_user, username_of_registered_user, name_of_registered_user)
        if email_of_registered_user:
            st.sidebar.success('User registered successfully')
    except Exception as e:
        st.error(e)

if st.session_state['authentication_status']:
    pg = st.navigation(
        {
            "Reports": [gui]
        }
    )
elif st.session_state['authentication_status'] is False:
    pg = st.navigation(
        {
            "Reports": [default_page]
        }
    )
elif st.session_state['authentication_status'] is None:
    pg = st.navigation(
        {
            "Reports": [default_page]
        }
    )
# st.write(st.session_state)
pg.run()
