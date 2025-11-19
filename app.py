import streamlit as st
import requests
import base64

# ------------------------------
# CONFIG / API KEYS
# ------------------------------

STT_API_KEY = "YOUR_SPEECH_TO_TEXT_KEY"
STT_API_URL = "YOUR_STT_ENDPOINT"  # e.g. Azure, AssemblyAI, etc.

TTS_API_KEY = "YOUR_TTS_KEY"
TTS_API_URL = "YOUR_TTS_ENDPOINT"  # e.g. Azure, Google, etc.

LLM_API_KEY = "YOUR_LLM_KEY"
LLM_URL = "YOUR_LLM_URL"  # e.g. https://api.groq.com/openai/v1/chat/completions

# ------------------------------
# STREAMLIT APP UI
# ------------------------------

st.title("🎤 Speech → LLM → Speech App")

st.write("Speak in any language → Convert to Text → Ask LLM → Hear the Answer")

# ----------------------------------------
# 1️⃣ RECORD AUDIO (Streamlit built-in)
# ----------------------------------------

audio_bytes = st.audio_input("Click to Speak")

if audio_bytes:
    st.success("Audio recorded!")
else:
    st.info("Please record your voice.")

# ----------------------------------------
# 2️⃣ SPEECH TO TEXT
# ----------------------------------------

def speech_to_text(audio):
    headers = {
        "Authorization": STT_API_KEY,
        "Content-Type": "audio/wav"
    }
    response = requests.post(STT_API_URL, headers=headers, data=audio)

    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        st.error(f"STT Error: {response.text}")
        return ""

if audio_bytes:
    if st.button("Convert Speech to Text"):
        stt_text = speech_to_text(audio_bytes)
        st.text_area("Recognized Text", stt_text, height=150)
    else:
        stt_text = ""

# ----------------------------------------
# 3️⃣ SEND TEXT TO LLM
# ----------------------------------------

def ask_llm(prompt):
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b",   # Change based on provider
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(LLM_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"LLM Error: {response.text}")
        return ""

if audio_bytes and stt_text:
    if st.button("Ask LLM"):
        llm_answer = ask_llm(stt_text)
        st.text_area("LLM Answer", llm_answer, height=150)
    else:
        llm_answer = ""

# ----------------------------------------
# 4️⃣ TEXT TO SPEECH
# ----------------------------------------

def text_to_speech(text):
    headers = {
        "Authorization": TTS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "voice": "default",
        "language": "auto"
    }

    response = requests.post(TTS_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        audio_data = base64.b64decode(response.json()["audio"])
        return audio_data
    else:
        st.error(f"TTS Error: {response.text}")
        return None

if llm_answer:
    if st.button("Speak Answer"):
        audio_output = text_to_speech(llm_answer)
        if audio_output:
            st.audio(audio_output, format="audio/wav")
