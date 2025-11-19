import streamlit as st
import tempfile
import azure.cognitiveservices.speech as speechsdk
import requests

st.set_page_config(page_title="Speech → Deepseek → Speech", layout="centered")
st.title("🎤 Speech → Deepseek → Speech (SDK Version)")

# -------------------------
# CONFIG: Put your keys here
# -------------------------
AZURE_SPEECH_KEY = "FS4yBV3YjzD9gw2g8Xzcz1k8OVpIXR8QaB0NuZt5ODQmappDVzirJQQJ99BKAC3pKaRXJ3w3AAAYACOGhPZt"
AZURE_SPEECH_REGION = "eastasia"  # just the region, no URL

DEEPSEEK_API_KEY = "sk-bdd3d505652b4b5499e5c0fea9dde95b"
DEEPSEEK_API_URL = "https://api.deepseek.com"

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
# 2️⃣ Speech-to-Text (Azure SDK)
# -------------------------
def azure_speech_to_text(audio_path):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    audio_config = speechsdk.AudioConfig(filename=audio_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        st.error(f"STT failed: {result.reason}")
        return ""

# -------------------------
# 3️⃣ Deepseek LLM call (keep requests)
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
# 4️⃣ Text-to-Speech (Azure SDK)
# -------------------------
def azure_text_to_speech(text):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    # Pick voice
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    audio_config = speechsdk.audio.AudioOutputConfig(filename=tmp_file)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return tmp_file
    else:
        st.error(f"TTS failed: {result.reason}")
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
            tts_path = azure_text_to_speech(st.session_state["llm_answer"])
            st.session_state["tts_audio"] = tts_path
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
