import os
import openai
import streamlit as st
from constants import characters, open_ai_key, uri, database_name

def user_page(room_code, user_name, openai_api_key="") :
    st.title("💬 Chatbot")
    if "messages" not in st.session_state:
        st.session_state["messages"] = fetch_user_messages(database_name, room_code, user_name)[0]["messages"]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()

        openai.api_key = openai_api_key
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
        msg = response.choices[0].message
        st.session_state.messages.append(msg)
        store_message_history(database_name, room_code, st.session_state.messages, user_name)
        st.chat_message("assistant").write(msg.content)
        
def user_view_page(user_name, messages) :
    st.title(user_name)
    for msg in messages:
        st.chat_message(msg["role"]).write(msg["content"])

import streamlit as st
import pymongo
import certifi
import random

def admin_page(room_code, users):
    # Sample data for 5 users

    button_states = []

    st.header("Room Code: " + room_code)

    # Create three columns using st.beta_columns()
    col1, col2, col3 = st.columns(3)

    # Column 1: Names
    with col1:
        st.subheader("Names")
        for user in users:
            st.write(user["user"])
            st.write("######")

    # Column 2: View Chat Buttons
    with col2:
        st.subheader("View Chat")
        button_states = []
        for user in users:
            button_states.append(st.button("View Chat", key=user["user"] + "view"))

    # Column 3: Remove User Buttons
    with col3:
        st.subheader("Remove User")
        for user in users:
            if st.button("Remove", key=user["user"] + "remove"):
                remove_user(database_name, room_code, user["user"])
                st.experimental_rerun()

    for ind, state in enumerate(button_states):
        if state:
            user_view_page(users[ind]["user"], users[ind]["messages"])

ca = certifi.where()
# Connect to MongoDB

def random_code(characters):
    code = ""
    for i in range(6):
        code += characters[random.randint(0, len(characters) - 1)]
    return code

def does_collection_exist(database_name, collection_name):
    
    client = pymongo.MongoClient(uri, tlsCAFile=ca)
    # Create or access the specified database
    db = client[database_name]
    
    # Check if the collection exists in the database
    collection_names = db.list_collection_names()
    collection_exists = collection_name in collection_names

    # Close the MongoDB connection
    client.close()

    return collection_exists

def generate_room_key(characters):
    collection_exists = True
    while collection_exists: 
        collection_code = random_code(characters)
        collection_exists = does_collection_exist(client, database_name, collection_code)
    return collection_code

def remove_user(database_name, collection_code, user_name):
    client = pymongo.MongoClient(uri, tlsCAFile=ca)
    db = client[database_name]
    collection = db[collection_code]

    # Define the filter to find the user by name
    filter_query = {"user": user_name}

    # Delete the user from the collection
    result = collection.delete_one(filter_query)

    client.close()
    # Return True if the user was deleted, False otherwise
    return result.deleted_count > 0

def fetch_all_documents(database_name, collection_code):
    # Connect to MongoDB
    client = pymongo.MongoClient(uri, tlsCAFile=ca)
    db = client[database_name]
    collection = db[collection_code]

    # Fetch all the documents from the collection
    documents = list(collection.find())

    # Close the MongoDB connection
    client.close()

    return documents

def fetch_user_messages(database_name, collection_code, user_name):
    client = pymongo.MongoClient(uri, tlsCAFile=ca)
    db = client[database_name]
    collection = db[collection_code]
    
    query_filter = {"user": user_name}

    # Fetch messages from the collection for the specific user
    messages = list(collection.find(query_filter, {"_id": 0, "messages": 1}))

    # Close the MongoDB connection
    client.close()

    return messages

def store_message_history(database_name, collection_code, message_history, user_name):

    client = pymongo.MongoClient(uri, tlsCAFile=ca)
    # Create or access the specified database
    db = client[database_name]

    # Create a collection with the provided code as its name
    collection = db[collection_code]

    # Insert each user's message history as documents in the collection
    filter_query = {"user": user_name}
    update_query = {
        "$set": {"messages": message_history},
        "$setOnInsert": {"user": user_name}  # Only set this field if it's a new document
    }
    collection.update_one(filter_query, update_query, upsert=True)
    client.close()


def home_page():
    st.title('Welcome to the Home Page')
    # Add content specific to the Home page here
    st.write("Large Language models like chat gpt are being used more and more by students all over the world. The intentions while accessing these amazing resources are not always innocent especially when used for school work. Why not provide our students with a safe, relevant, and non-malicious way to use these very powerful tools within the classroom ")

def main1(user_name):
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'
    with st.sidebar:
        st.title('LLM Powered TA')
        if st.button('Home'):
            st.session_state['page'] = 'home'
            
        openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
        
        # Create buttons for switching pages
        collection_code = st.text_input("Join Room Code", key="join_room_code")
        
        if st.button('Join Room'):
            if not collection_code:
                st.info("Please enter a valid room code to continue.")
            else:
                st.session_state['page'] = 'user'

        if st.button('Create Room'):
            st.session_state['page'] = 'admin'
    

    # Use conditional statements to display the content based on the current page
    if st.session_state['page'] == 'user':
        if collection_code:
            user_page(collection_code, user_name, openai_api_key)
        else:
            home_page()
    elif st.session_state['page'] == 'admin':
        collection_code = "FDY3WT"
        users = fetch_all_documents(database_name, collection_code)
        admin_page(collection_code, users)
    elif st.session_state['page'] == "home":
        home_page()

if __name__ == "__main__":
    main1("minglun")