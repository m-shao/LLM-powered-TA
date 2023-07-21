import os
import openai
import streamlit as st
from constants import characters, open_ai_key, uri, database_name

def user_page(room_code, user_name) :
    with st.sidebar:
        openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

    st.title("💬 Chatbot")
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

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
        for user in users:
            if st.button("View Chat", key=user["user"] + "view"):
                print(user["user"], user["messages"])


    # Column 3: Remove User Buttons
    with col3:
        st.subheader("Remove User")
        for user in users:
            if st.button("Remove", key=user["user"] + "remove"):
                # Logic to remove the user from the list or database goes here
                # In this example, we simply remove the user from the list for demonstration purposes
                users.remove(user)


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


room_role = ""

def home_page():
    st.title('Welcome to the Home Page')
    # Add content specific to the Home page here

def about_page():
    st.title('About Us')
    # Add content specific to the About page here

def main1(user_name):
    room_role = "user"
    st.title('Multi-Page Streamlit App')

    # Create buttons for switching pages
    if st.button('user'):
        room_role = 'user'

    if st.button('admin'):
        room_role = 'admin'

    # Use conditional statements to display the content based on the current page
    if room_role == 'user':
        collection_code = "FDY3WT"
        user_page(collection_code, user_name)
    elif room_role == 'admin':
        collection_code = "FDY3WT"
        users = fetch_all_documents(database_name, collection_code)
        admin_page(collection_code, users)

if __name__ == "__main__":
    main1("minglun")
    
    
    # room = input("would you like to create a room?: ")
    # if room == "yes":
    #     collection_code = generate_room_key(characters)
    #     room_role = "admin"
    #     # admin_page(collection_code, users)
    # else:
    #     room_role = "user"
    #     collection_code = input("please enter the room code: ")
        
    
    # # Sample dictionary representing user message history
    # message_history = [
    #         {"role": "sender", "content": "Hello, how is your mom?"},
    #         {"role": "receiver", "content": "I'm fine, thank you!"},
    # ]
    user_name = "minglun"

    
    # # Call the function to store the message history in MongoDB
    # store_message_history(client, database_name, "FDY3WT", message_history, user_name)
    # print(remove_user(client, database_name, "FDY3WT", user_name))