import streamlit as st
import requests
import base64
import tempfile

st.set_page_config(page_title="Speech → Deepseek → Speech", layout="centered")
st.title("🎤 Speech → Deepseek → Speech")

# -------------------------
# CONFIG: PUT YOUR KEYS HERE
# -------------------------
AZURE_SPEECH_KEY = "FS4yBV3YjzD9gw2g8Xzcz1k8OVpIXR8QaB0NuZt5ODQmappDVzirJQQJ99BKAC3pKaRXJ3w3AAAYACOGhPZt"
AZURE_SPEECH_REGION = "https://eastasia.api.cognitive.microsoft.com/"

DEEPSEEK_API_KEY = "sk-bdd3d505652b4b5499e5c0fea9dde95b"
DEEPSEEK_API_URL = "https://api.deepseek.com"  # e.g., https://api.deepseek.ai/llm

# -------------------------
# Session State Defaults
# -------------------------
if "audio_bytes" not in st.session_state:
    st.session_state["audio_bytes"] = None
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "llm_answer" not in st.session_state:
    st.session_state["llm_answer"] = ""
if "tts_audio" not in st.session_state:
    st.session_state["tts_audio"] = None

# -------------------------
# 1️⃣ Record audio in browser
# -------------------------
audio_bytes = st.audio_input("Click to speak")
if audio_bytes:
    st.session_state["audio_bytes"] = audio_bytes
    st.success("Audio recorded!")

# -------------------------
# Helper: Save audio temporarily
# -------------------------
def save_temp_audio(audio):
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_file.write(audio.read())
    tmp_file.flush()
    tmp_file.close()
    return tmp_file.name

# -------------------------
# 2️⃣ Speech-to-Text (Azure REST)
# -------------------------
def azure_speech_to_text(audio_path):
    url = f"https://{AZURE_SPEECH_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-US"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "audio/wav"
    }
    with open(audio_path, "rb") as f:
        data = f.read()
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("DisplayText", "")
    else:
        st.error(f"STT error: {response.text}")
        return ""

# -------------------------
# 3️⃣ Send text to Deepseek LLM
# -------------------------
def ask_deepseek(prompt_text):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"prompt": prompt_text}
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get("response", "")
    else:
        st.error(f"Deepseek error: {response.text}")
        return ""

# -------------------------
# 4️⃣ Text-to-Speech (Azure REST)
# -------------------------
def azure_text_to_speech(text):
    url = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm"
    }
    ssml = f"""
    <speak version='1.0' xml:lang='en-US'>
        <voice xml:lang='en-US' xml:gender='Female' name='en-US-JennyNeural'>
            {text}
        </voice>
    </speak>
    """
    response = requests.post(url, headers=headers, data=ssml.encode("utf-8"))
    if response.status_code == 200:
        return response.content
    else:
        st.error(f"TTS error: {response.text}")
        return None

# -------------------------
# BUTTONS
# -------------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Convert Speech → Text"):
        if st.session_state["audio_bytes"] is None:
            st.warning("Record audio first!")
        else:
            tmp_path = save_temp_audio(st.session_state["audio_bytes"])
            st.session_state["transcript"] = azure_speech_to_text(tmp_path)
            st.success("Transcription done!")

with col2:
    if st.button("Ask Deepseek LLM"):
        if st.session_state["transcript"].strip() == "":
            st.warning("Transcribe audio first!")
        else:
            st.session_state["llm_answer"] = ask_deepseek(st.session_state["transcript"])
            st.success("LLM responded!")

with col3:
    if st.button("Speak LLM Answer"):
        if st.session_state["llm_answer"].strip() == "":
            st.warning("Ask LLM first!")
        else:
            st.session_state["tts_audio"] = azure_text_to_speech(st.session_state["llm_answer"])
            st.success("Audio synthesized!")

# -------------------------
# DISPLAY
# -------------------------
st.subheader("Transcribed Text")
st.text_area("Transcript", st.session_state["transcript"], height=150)

st.subheader("LLM Answer")
st.text_area("LLM Answer", st.session_state["llm_answer"], height=150)

if st.session_state["tts_audio"]:
    st.audio(st.session_state["tts_audio"], format="audio/wav")
