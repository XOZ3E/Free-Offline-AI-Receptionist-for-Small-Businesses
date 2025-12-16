import subprocess
import sys
import os
import pyttsx3
import vosk
import sounddevice as sd
import numpy as np
import json
import queue

# --- CONFIGURATION ---
MODEL_NAME = "phi3:latest"

# --- Global variable to manage the microphone stream instance ---
# We need this so the speak function can access and close the stream
current_stream = None

# --- TTS Setup (pyttsx3) ---
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

def speak(text):
    print(f"\nAura speaking: {text}")
    
    # *** CRITICAL FIX: Stop the input stream while speaking ***
    global current_stream
    if current_stream:
        current_stream.stop()
        print("[Microphone muted during TTS playback]")

    engine.say(text)
    engine.runAndWait()
    
    # *** CRITICAL FIX: Restart the input stream after speaking ***
    if current_stream:
        current_stream.start()
        print("[Microphone resumed listening]")


# --- System Prompt & LLM Logic (CLI method) ---
SYSTEM_PROMPT = """
You are an offline call assistant named "Aura" for a school kid named Kevin. Your role is to answer calls because Kevin is busy doing his projects and homeworks. You need to talk to callers politely and inform them that Kevin is busy, answering questions based on this information: Kevin is in 8th grade and he attends Soman Highschool.
NOTE: YOU NEED TO ANSWER FAST CALLER WON'T LONG
RULES:
1. Keep responses brief, polite and to the point.
2. Maintain the context of the call; do not generate unrelated information.
3. Format all responses as plain text. No Markdown formatting.
"""
def build_prompt(messages):
    prompt = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system": prompt += f"<|system|>\n{content}<|end|>\n"
        elif role == "user": prompt += f"<|user|>\n{content}<|end|>\n"
        elif role == "assistant": prompt += f"<|assistant|>\n{content}<|end|>\n"
    prompt += "<|assistant|>\n"
    return prompt

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

def get_chat_response_cli(user_input):
    print(f"\nUser said: {user_input}")
    messages.append({"role": "user", "content": user_input})
    full_prompt = build_prompt(messages)
    try:
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME, full_prompt],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0: return "Sorry, offline."
        output_lines = [line for line in result.stdout.strip().split('\n') 
                        if not line.startswith(('[', '>>>', 'Loading', '<|')) and line.strip()]
        assistant_response_content = ' '.join(output_lines).strip()
        if not assistant_response_content: return "Sorry, no response."
        messages.append({"role": "assistant", "content": assistant_response_content})
        return assistant_response_content
    except Exception as e:
        return f"Error: {e}"

# --- STT Setup (Vosk & Sounddevice) ---
VOSK_MODEL_PATH = "/media/camin/New Volume/vosk-model-en-us-0.22" 
SAMPLERATE = 16000
Q = queue.Queue()

if not os.path.exists(VOSK_MODEL_PATH):
    print(f"Vosk model not found at {VOSK_MODEL_PATH}. Exiting.")
    sys.exit(1)

model = vosk.Model(VOSK_MODEL_PATH)
recognizer = vosk.KaldiRecognizer(model, SAMPLERATE)

def callback(indata, frames, time, status):
    if status: print(status, file=sys.stderr)
    Q.put(bytes(indata))

# --- MAIN EXECUTION LOGIC ---
if __name__ == "__main__":
    try:
        subprocess.run(["sudo", "systemctl", "stop", "ollama"], check=True)
        print("Stopped background Ollama service.")
    except Exception:
        pass

    print(f"Starting assistant using {MODEL_NAME} via CLI.")
    print("Listening... Speak clearly into your microphone.")

    # Assign the stream instance to the global variable
    with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=8000, 
                           dtype='int16', channels=1, callback=callback) as stream:
        current_stream = stream # Set the global variable
        while True:
            data = Q.get()
            if recognizer.AcceptWaveform(data):
                result_json = recognizer.Result()
                user_spoken_text = json.loads(result_json).get('text', '').strip()
                
                if user_spoken_text and user_spoken_text != "the": # Filter out common noise word
                    if user_spoken_text.lower() == 'exit':
                        break
                    
                    assistant_response = get_chat_response_cli(user_spoken_text)

                    if not assistant_response.startswith(("Sorry,","Error:")):
                        # Speak function now handles muting/unmuting the stream
                        speak(assistant_response)
                    else:
                        print(f"System Message: {assistant_response}")
                    print("-" * 30)


