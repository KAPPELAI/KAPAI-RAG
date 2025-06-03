import streamlit as st
import requests
import uuid
from supabase import create_client, Client

# Supabase setup
SUPABASE_URL = "https://khizlursmpxlsrzsstdo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtoaXpsdXJzbXB4bHNyenNzdGRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg3MTYzNTIsImV4cCI6MjA2NDI5MjM1Mn0.khyl5QQJI4GmgCHeSCO6MQdZdFfiGbw7watnPa-tPM4"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Webhook URL (replace with your n8n webhook URL)
WEBHOOK_URL = "https://kappelaisolutions.app.n8n.cloud/webhook-test/using-supabase-agent"

def login(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return res
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return None

def generate_session_id():
    return str(uuid.uuid4())

def init_session_state():
    if "auth" not in st.session_state:
        st.session_state.auth = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

def display_chat():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_logout():
    st.session_state.auth = None
    st.session_state.session_id = None
    st.session_state.messages = []
    st.rerun()

def auth_ui():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        auth = login(email, password)
        if auth:
            st.session_state.auth = auth
            st.session_state.session_id = generate_session_id()
            st.rerun()

def main():
    st.title("KAPAI Chatbot")
    init_session_state()

    if st.session_state.auth is None:
        auth_ui()
    else:
        st.sidebar.success(f"Logged in as {st.session_state.auth.user.email}")
        st.sidebar.info(f"Session ID: {st.session_state.session_id}")

        if st.sidebar.button("Logout"):
            handle_logout()

        display_chat()

        if prompt := st.chat_input("What is your message?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Prepare the payload
            payload = {
                "chatInput": prompt,
                "sessionId": st.session_state.session_id
            }
            
            # Get the access token from the session
            access_token = st.session_state.auth.session.access_token
            
            # Send request to webhook
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            with st.spinner("AI is thinking..."):
                response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                ai_message = response.json().get("output", "Sorry, I couldn't generate a response.")
                st.session_state.messages.append({"role": "assistant", "content": ai_message})
                with st.chat_message("assistant"):
                    st.markdown(ai_message)
            else:
                st.error(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
