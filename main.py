# imports
import os
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import certifi
import random
import pymongo
# for pdf
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
# for chatbot
import openai
from langchain import PromptTemplate, OpenAI, LLMChain
from langchain.schema import HumanMessage, AIMessage
from constants import characters, open_ai_key, uri, database_name

company_name = "Classroom Companion"
lesson_title = "Indigenous Colonization"
global file_path

# functions are for streamlit's ability to run multiple pages    

def semantic_search(path, query, openai_api_key):
    loader = PyPDFLoader(path)
    pages = loader.load_and_split()

    faiss_index = FAISS.from_documents(pages, OpenAIEmbeddings(openai_api_key=openai_api_key))
    docs = faiss_index.similarity_search(query, k=2)
    results = []
    for doc in docs:
        results.append(f'Page {doc.metadata["page"]}: {doc.page_content[:300]}...')
    return '\n'.join(results)

def chatbot(user_input="", openai_api_key="", room_code="", user_name=""):
    llm = OpenAI(openai_api_key=openai_api_key,temperature=0)

    template1 = """\
    You are a teaching assistant for a high school teacher's class, and your primary objective is to assist the student in understanding the lesson better. Your responses should be in the second person, addressing the student directly.

    If the student asks you a question or seeks help related to the lesson, provide relevant and informative responses from the lesson PDF. However, if the student types random keys or seems off-task, gently guide them back to the lesson and encourage them to focus on the material.

    Remember, your role is to support the student's learning journey. Try to relate your responses as much as possible to the content covered in the lesson PDF. If the student hasn't asked a question or is not discussing the lesson, you can politely remind them to stay on track and ask questions related to the material.

    Now, the student has said: {question}
    """

    template0 = """\
    You are a teaching assistant for a high school teacher's class. You are helping a student with a lesson. Talk to the student in second person.
    If the user does not ask a question including a ?, remind them they should be asking questions to understand the lesson. Try to relate the conversation to the lesson pdf as much as possible. 
    The student asks you: {question}
    """

    llm_chain = LLMChain(
        llm=llm, 
        prompt=PromptTemplate.from_template(template1)
    )
    st.chat_message("user").write(user_input)

    user_message = HumanMessage(content=user_input)
    user_message_dict = {"role": "user", "content": user_message.content}
    st.session_state.messages.append(user_message_dict)

    semantic_info = semantic_search(path="uploaded_documents/61687944.pdf", query="What is some relevant information in the lesson text that is relevant to: " + user_input, openai_api_key=openai_api_key)

    ai_message = AIMessage(content=llm_chain("use relevant information from the lesson pdf to answer " + user_input + "\n relevant information: " + semantic_info)["text"])
    # msg should really becalled ai_message
    msg = { 'role': 'assistant', 'content': ai_message.content }
    st.chat_message("assistant").write(msg["content"])
    st.session_state.messages.append(msg)

    store_message_history(database_name, room_code, st.session_state.messages, user_name)

# user page
def user_page(room_code, user_name, openai_api_key) : # why is openai api key here?
    st.title("💬 Chatbot")
    st.write("Your teacher's chosen topic is " + lesson_title)
    if "messages" not in st.session_state:
        try: 
            st.session_state["messages"] = fetch_user_messages(database_name, room_code, user_name)[0]["messages"]
        except(Exception):
            st.session_state["messages"] = [{"role": "assistant", "content": "Hello, how can I help you today?"}]
    store_message_history(database_name, room_code, st.session_state["messages"], user_name)
        
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input():
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()
        # this is the actual chat bot
        chatbot(user_input=user_input, openai_api_key=openai_api_key, room_code=room_code, user_name=user_name)
        
def user_view_page(user_name, messages) :
    st.title(user_name)
    for msg in messages:
        st.chat_message(msg["role"]).write(msg["content"])

def admin_page(room_code, users):
    st_autorefresh(interval=5000, limit=100, key="userFinder")
    # Sample data for 5 users

    button_states = []

    st.header("Room Code: " + room_code)
    if st.button("Delete Room", key="delete"):
        delete_collection(database_name, room_code)
        return "home"

    # Create three columns using st.beta_columns()
    col1, col2, col3 = st.columns(3)

    lesson_title = st.text_input("Main Focus of Lesson", key="lesson_title")
    # Create a file uploader using streamlit components & run my function to upload the file
    uploaded_file = st.file_uploader('Upload your lesson material as a .pdf file', type="pdf")
    if uploaded_file is not None:
        print("upload successful")

    if len(users) > 0:
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
    client = pymongo.MongoClient(uri, tlsCAFile=ca)
    
    collection_exists = True
    while collection_exists: 
        collection_code = random_code(characters)
        collection_exists = does_collection_exist(database_name, collection_code)
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

def delete_collection(database_name, collection_code):
    client = pymongo.MongoClient(uri, tlsCAFile=ca)
    db = client[database_name]
    collection = db[collection_code]

    # Delete the collection
    collection.drop()

    # Close the MongoDB connection
    client.close()

company_name = "LLM-TA"
def home_page():
    st.title('Welcome to ' + company_name + '!')
    # Add content specific to the Home page here
    st.write("Students worldwide rely on large language models like ChatGPT for various purposes. However, their usage is not always innocent, particularly when employed for school work.")
    st.write(company_name + " is revolutionizing learning through AI-driven Breakout Rooms. Engage students with curriculum PDFs and foster collaborative discussions in a educational, non-malicious, and secure environment.")
    st.write("####")
    st.write("What is your name?")
    if 'name' not in st.session_state:
        st.session_state['name'] = ''
    st.session_state['name'] = st.text_input("Username", key="username")

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
            if st.session_state['name'] == '':
                st.info("Please enter a valid username to continue.")
            elif not collection_code or not does_collection_exist(database_name, collection_code):
                st.info("Please enter a valid room code to continue.")
            else:
                st.session_state['page'] = 'user'

        if st.button('Create Room'):
            st.session_state['page'] = 'admin'
    

    # Use conditional statements to display the content based on the current page
    if st.session_state['page'] == 'user':
        if collection_code:
            user_page(collection_code, st.session_state['name'], openai_api_key)
        else:
            home_page()
    elif st.session_state['page'] == 'admin':
        if 'key' not in st.session_state:
            st.session_state['key'] = generate_room_key(characters)
        client = pymongo.MongoClient(uri, tlsCAFile=ca)
        # Create or access the specified database
        db = client[database_name]
        collection = db[st.session_state['key'] ]
        collection.insert_one({})
        query_filter = {"user": {"$exists": True}}

        # Fetch documents from the collection with the "user" property
        users = list(collection.find(query_filter))
        client.close()
        admin_page(st.session_state['key'], users)
    elif st.session_state['page'] == "home":
        home_page()

if __name__ == "__main__":
    main1("minglun")