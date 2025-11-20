import streamlit as st
import requests
import tempfile

# -------------------------
# CONFIG: Put your keys here
# -------------------------
AZURE_SPEECH_KEY = "FS4yBV3YjzD9gw2g8Xzcz1k8OVpIXR8QaB0NuZt5ODQmappDVzirJQQJ99BKAC3pKaRXJ3w3AAAYACOGhPZt"
AZURE_SPEECH_REGION = "eastasia"  # just the region

OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "tngtech/deepseek-r1t2-chimera:free"

# -------------------------
# Streamlit page config
# -------------------------
st.set_page_config(page_title="Speech → OpenRouter → Speech", layout="centered")
st.title("🎤 Speech → OpenRouter → Speech")

# -------------------------
# Session state defaults
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
    try:
        response = requests.post(url, headers=headers, data=data, timeout=15)
        if response.status_code == 200:
            return response.json().get("DisplayText", "")
        else:
            st.error(f"STT error: {response.status_code} {response.text}")
            return ""
    except requests.exceptions.RequestException as e:
        st.error(f"STT request failed: {str(e)}")
        return ""

# -------------------------
# 3️⃣ Send text to OpenRouter LLM
# -------------------------
def ask_openrouter(prompt_text):
    url = "https://openrouter.ai/api/v1/chat/completions/"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "tngtech/deepseek-r1t2-chimera:free",
        "messages": [{"role": "user", "content": prompt_text}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)

        # Debug print (optional)
        # st.write("RAW:", response.text)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]

        elif response.status_code == 401:
            st.error("❌ Invalid API key (401 Unauthorized)")
            return ""

        elif response.status_code == 404:
            st.error("❌ Model not found (404 Not Found)")
            return ""

        else:
            st.error(f"LLM error {response.status_code}: {response.text}")
            return ""

    except requests.exceptions.RequestException as e:
        st.error(f"LLM request failed: {str(e)}")
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
    try:
        response = requests.post(url, headers=headers, data=ssml.encode("utf-8"), timeout=15)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"TTS error: {response.status_code} {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"TTS request failed: {str(e)}")
        return None

# -------------------------
# SINGLE BUTTON: Record → LLM → Speak
# -------------------------
if st.button("Record → Ask → Speak"):
    if st.session_state["audio_bytes"] is None:
        st.warning("Record audio first!")
    else:
        tmp_path = save_temp_audio(st.session_state["audio_bytes"])
        # 1️⃣ STT
        st.session_state["transcript"] = azure_speech_to_text(tmp_path)
        if st.session_state["transcript"].strip() == "":
            st.error("No transcription available.")
        else:
            # 2️⃣ LLM
            st.session_state["llm_answer"] = ask_openrouter(st.session_state["transcript"])
            # 3️⃣ TTS
            if st.session_state["llm_answer"].strip() != "":
                st.session_state["tts_audio"] = azure_text_to_speech(st.session_state["llm_answer"])

# -------------------------
# DISPLAY
# -------------------------
st.subheader("Transcribed Text")
st.text_area("Transcript", st.session_state["transcript"], height=150)

st.subheader("LLM Answer")
st.text_area("LLM Answer", st.session_state["llm_answer"], height=150)

if st.session_state["tts_audio"]:
    st.audio(st.session_state["tts_audio"], format="audio/wav")
