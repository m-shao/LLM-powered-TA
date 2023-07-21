import streamlit as st

def home_page():
    st.title('Welcome to the Home Page')
    # Add content specific to the Home page here

def about_page():
    st.title('About Us')
    # Add content specific to the About page here

def main():
    st.title('Multi-Page Streamlit App')
    
    # Initialize a state variable to keep track of the current page
    current_page = 'Home'

    # Create buttons for switching pages
    if st.button('Home'):
        current_page = 'Home'

    if st.button('About'):
        current_page = 'About'

    # Use conditional statements to display the content based on the current page
    if current_page == 'Home':
        home_page()
    elif current_page == 'About':
        about_page()

if __name__ == '__main__':
    main()