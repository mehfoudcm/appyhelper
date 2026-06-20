def check_password():
    """Returns True if the user had the correct password."""
    # Ensure the password secret exists
    if "APP_PASSWORD" not in st.secrets:
        st.error("Security configuration error: 'APP_PASSWORD' is not set in secrets.")
        return False

    # Initialize password state if it doesn't exist
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # If already authenticated, bypass login
    if st.session_state["password_correct"]:
        return True

    # Show login form
    st.title("🔒 Password Protected Application")
    password_input = st.text_input("Enter Password to access the tool:", type="password")
    
    if st.button("Log In"):
        if password_input == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()  # Refresh the page to show the full app immediately
        else:
            st.error("❌ Incorrect password. Please try again.")
            
    return False
