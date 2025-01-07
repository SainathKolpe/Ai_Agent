import streamlit as st
import requests
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
import os
from dotenv import load_dotenv
from pydub import AudioSegment
import io

# Load environment variables from .env file (optional, for local development)
load_dotenv()

# Constants for API keys and Agent ID (loaded from environment variables)
API_KEY = os.getenv("API_KEY")
AGENT_ID = os.getenv("AGENT_ID")

# Ensure API_KEY and AGENT_ID are present
if not API_KEY or not AGENT_ID:
    raise ValueError("API_KEY and AGENT_ID must be set as environment variables.")

client = ElevenLabs(api_key=API_KEY)

# Global variable for the conversation
conversation = None

def start_conversation():
    global conversation
    conversation = Conversation(
        client,
        AGENT_ID,
        requires_auth=bool(API_KEY),
        audio_interface=DefaultAudioInterface(),
        callback_agent_response=lambda response: st.write(f"**Agent:** {response}"),
        callback_agent_response_correction=lambda original, corrected: st.write(f"**Agent:** {original} -> {corrected}"),
        callback_user_transcript=handle_user_transcript,
    )
    conversation.start_session()
    st.session_state.agent_running = True

def stop_conversation():
    global conversation
    if conversation:
        conversation.stop_session()
        st.session_state.agent_running = False
        st.write("**Agent has been stopped**")

def handle_user_transcript(transcript):
    st.write(f"**User:** {transcript}")
    if transcript.strip().lower() == "stop":
        stop_conversation()

# Function to fetch all conversations
def get_conversations():
    url = "https://api.elevenlabs.io/v1/convai/conversations"
    querystring = {"agent_id": AGENT_ID}
    headers = {"xi-api-key": API_KEY}

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict) and "conversations" in data:
            conversation_ids = [conversation["conversation_id"] for conversation in data["conversations"]]
            return conversation_ids
        else:
            return []
    else:
        return []

# Function to fetch and return conversation audio file
def get_audio(conversation_id):
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}/audio"
    headers = {"xi-api-key": API_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        audio_data = response.content
        
        # Using pydub to process audio
        audio = AudioSegment.from_mp3(io.BytesIO(audio_data))  # Read the audio from memory
        
        # Optionally process the audio (e.g., convert to WAV)
        audio_file_path = f"{conversation_id}_audio.wav"
        audio.export(audio_file_path, format="wav")

        return audio_file_path
    else:
        return None

# Function to delete a conversation
def delete_conversation(conversation_id):
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"xi-api-key": API_KEY}

    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        return "Conversation deleted successfully."
    else:
        return "Failed to delete the conversation."

def get_messages(conversation_id):
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"xi-api-key": API_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "transcript" in data:
            return [message["message"] for message in data["transcript"]]
        else:
            return ["No messages found in this conversation."]
    else:
        return ["Failed to fetch messages."]

# Streamlit UI
def main():
    st.set_page_config(page_title="Agensense - Your Comsense AI Agent", page_icon="🤖", layout="centered")
    st.markdown("""<div style="text-align: center;"><span style="font-size: 5em;">🤖</span><br><br></div>""", unsafe_allow_html=True)

    st.markdown("""<h1 style="text-align: center; font-size: 3em;">🌟 Welcome to Agensense 🌟</h1>""", unsafe_allow_html=True)

    st.markdown("""<p style="text-align: center; font-size: 1.2em;">Agensense is here to help you explore Comsense Technologies with ease and efficiency.</p>""", unsafe_allow_html=True)

    # Initialize session state for agent status
    if "agent_running" not in st.session_state:
        st.session_state.agent_running = False

    # Dropdown for selecting services
    services = [
        "Select a service", 
        "Start the Agensense", 
        "Get Conversations History", 
        "Get Conversation Audio", 
        "Delete Conversation", 
        "Twillo Configuration", 
        "Send Email", 
        "Schedule Meeting", 
        "Translation"
    ]
    selected_service = st.selectbox("Choose a Service:", services)

    if selected_service == "Start the Agensense":
        if not st.session_state.agent_running:
            if st.button("Start Agensense"):
                start_conversation()
                st.write("**Agent has been started**")
        else:
            st.write("**Agent is already running**")
            if st.button("Stop Agensense"):
                stop_conversation()

    elif selected_service == "Get Conversations History":
        if st.session_state.agent_running:
            stop_conversation()
        conversation_ids = get_conversations()

        if conversation_ids:
            selected_conversation_id = st.selectbox("Select a Conversation ID:", conversation_ids)

            if selected_conversation_id:
                messages = get_messages(selected_conversation_id)
                st.markdown(f"### Messages for Conversation ID: {selected_conversation_id}")
                for message in messages:
                    st.write(f"- {message}")
        else:
            st.write("No conversations found!")

    elif selected_service == "Get Conversation Audio":
        if st.session_state.agent_running:
            stop_conversation()
        conversation_ids = get_conversations()

        if conversation_ids:
            selected_conversation_id = st.selectbox("Select a Conversation ID for Audio:", conversation_ids)

            if selected_conversation_id:
                audio_file_path = get_audio(selected_conversation_id)

                if audio_file_path:
                    st.audio(audio_file_path, format="audio/wav")
                else:
                    st.error("Failed to retrieve audio. Please try again.")
        else:
            st.write("No conversations found!")

    elif selected_service == "Delete Conversation":
        if st.session_state.agent_running:
            stop_conversation()
        conversation_ids = get_conversations()

        if conversation_ids:
            selected_conversation_id = st.selectbox("Select a Conversation ID to Delete:", conversation_ids)

            if st.button("Delete Conversation"):
                if selected_conversation_id:
                    result = delete_conversation(selected_conversation_id)
                    st.success(result)
                else:
                    st.error("No Conversation ID selected.")
        else:
            st.write("No conversations found!")

    elif selected_service == "Twillo Configuration":
        st.write("Coming Soon...")

    elif selected_service == "Send Email":
        st.write("Coming Soon...")

    elif selected_service == "Schedule Meeting":
        st.write("Coming Soon...")

    elif selected_service == "Translation":
        st.write("Coming Soon...")

if __name__ == "__main__":
    main()
