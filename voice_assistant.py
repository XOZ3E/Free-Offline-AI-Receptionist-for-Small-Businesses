import subprocess
import sys
import os
import platform
import pyttsx3
import vosk
import sounddevice as sd
import numpy as np
import json
import queue

# --- PLATFORM DETECTION ---
CURRENT_OS = platform.system()  # 'Windows', 'Linux', or 'Darwin' (macOS)
IS_WINDOWS = CURRENT_OS == "Windows"
IS_LINUX = CURRENT_OS == "Linux"

print(f"[System] Detected OS: {CURRENT_OS}")

# --- CONFIGURATION ---
MODEL_NAME = "phi3:latest"

# --- Vosk Model Path (OS-specific) ---
if IS_WINDOWS:
    # Windows: Adjust this path to your Vosk model location
    VOSK_MODEL_PATH = os.path.join(os.path.expanduser("~"), "vosk-models", "vosk-model-en-us-0.22")
else:
    # Linux: Original path
    VOSK_MODEL_PATH = "/media/camin/New Volume/vosk-model-en-us-0.22"

# Allow override via environment variable
VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", VOSK_MODEL_PATH)

# --- Global variables ---
# We need this so the speak function can access and close the stream
current_stream = None
is_speaking = False  # Flag to prevent TTS echo from being recognized as input

# --- TTS Setup (pyttsx3) ---
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Select English voice (important for non-English Windows systems)
def select_english_voice():
    """Find and select an English TTS voice"""
    voices = engine.getProperty('voices')
    if not voices:
        return
    
    # Print available voices for debugging
    print("[TTS] Available voices:")
    for i, voice in enumerate(voices):
        print(f"  [{i}] {voice.name} - {voice.languages}")
    
    # Try to find an English voice
    english_keywords = ['english', 'en-us', 'en-gb', 'en_us', 'en_gb', 'david', 'zira', 'mark']
    
    for voice in voices:
        voice_name_lower = voice.name.lower()
        voice_id_lower = voice.id.lower()
        
        for keyword in english_keywords:
            if keyword in voice_name_lower or keyword in voice_id_lower:
                print(f"[TTS] Selected English voice: {voice.name}")
                engine.setProperty('voice', voice.id)
                return
    
    # Fallback: use first voice if no English found
    print(f"[TTS] Warning: No English voice found, using default: {voices[0].name}")
    engine.setProperty('voice', voices[0].id)

select_english_voice()

def speak(text):
    print(f"\n{ASSISTANT_NAME} speaking: {text}")
    
    global current_stream, is_speaking
    
    # Set speaking flag to ignore any STT input during TTS
    is_speaking = True
    
    if IS_LINUX and current_stream:
        # Linux: Stop stream to prevent feedback loop
        current_stream.stop()
        print("[Microphone muted during TTS playback]")
    
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error] {e}")
    
    if IS_LINUX and current_stream:
        # Linux: Restart stream after speaking
        current_stream.start()
        print("[Microphone resumed listening]")
    
    # Clear the audio queue to discard any TTS echo that was captured
    while not Q.empty():
        try:
            Q.get_nowait()
        except queue.Empty:
            break
    
    # Reset the recognizer to clear any partial results from TTS echo
    recognizer.Reset()
    
    # Small delay to let any remaining echo dissipate
    import time
    time.sleep(0.3)
    
    is_speaking = False
    print("[Microphone ready for next input]")


# --- System Prompt & LLM Logic (CLI method) ---
# ============================================
# CUSTOMIZE THIS SECTION FOR YOUR USE CASE
# ============================================
ASSISTANT_NAME = "Aura"  # Change to your preferred assistant name
OWNER_NAME = "the owner"  # Change to your name or business name
OWNER_INFO = "currently unavailable"  # Brief info about availability

SYSTEM_PROMPT = f"""
You are an offline call assistant named "{ASSISTANT_NAME}". Your role is to answer calls because {OWNER_NAME} is {OWNER_INFO}.

RULES:
1. Keep responses brief, polite and to the point (1-2 sentences max).
2. Do not invent information you don't have.
3. Format all responses as plain text. No Markdown.
4. If asked something you don't know, say you'll pass the message along.
5. Be helpful but concise - callers won't wait long.
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
        # Use encoding='utf-8' and errors='replace' to handle Windows encoding issues
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME, full_prompt],
            capture_output=True, 
            text=True, 
            timeout=120,
            encoding='utf-8',
            errors='replace'  # Replace undecodable characters instead of crashing
        )
        if result.returncode != 0: return "Sorry, offline."
        
        # Filter out model artifacts and hallucinations
        raw_output = result.stdout.strip()
        
        # Stop at common hallucination markers
        stop_markers = ['---', '**', '```', 'NOTE:', 'RULES:', 'Constraints:', 
                        'You are an', 'You are a', '<|', '>>>', 'Loading']
        
        # Take only the first part before any stop marker
        clean_output = raw_output
        for marker in stop_markers:
            if marker in clean_output:
                clean_output = clean_output.split(marker)[0]
        
        # Filter lines
        output_lines = [line for line in clean_output.split('\n') 
                        if line.strip() and not line.startswith(('[', '>>>'))]
        
        assistant_response_content = ' '.join(output_lines).strip()
        
        # Limit response length (prevent runaway responses)
        if len(assistant_response_content) > 500:
            # Cut at last complete sentence within limit
            truncated = assistant_response_content[:500]
            last_period = truncated.rfind('.')
            if last_period > 100:
                assistant_response_content = truncated[:last_period + 1]
        
        if not assistant_response_content: return "Sorry, no response."
        messages.append({"role": "assistant", "content": assistant_response_content})
        return assistant_response_content
    except Exception as e:
        return f"Error: {e}"

# --- STT Setup (Vosk & Sounddevice) ---
SAMPLERATE = 16000
Q = queue.Queue()

if not os.path.exists(VOSK_MODEL_PATH):
    print(f"[Error] Vosk model not found at: {VOSK_MODEL_PATH}")
    print(f"[Info] Download a model from: https://alphacephei.com/vosk/models")
    if IS_WINDOWS:
        print(f"[Info] Extract to: {os.path.join(os.path.expanduser('~'), 'vosk-models')}")
        print(f"[Info] Or set VOSK_MODEL_PATH environment variable")
    sys.exit(1)

print(f"[System] Loading Vosk model from: {VOSK_MODEL_PATH}")
model = vosk.Model(VOSK_MODEL_PATH)
recognizer = vosk.KaldiRecognizer(model, SAMPLERATE)

def callback(indata, frames, time, status):
    if status: print(status, file=sys.stderr)
    Q.put(bytes(indata))

# --- Helper Functions ---
def stop_ollama_service():
    """Stop Ollama background service (OS-specific)"""
    if IS_LINUX:
        try:
            subprocess.run(["sudo", "systemctl", "stop", "ollama"], check=True, 
                         capture_output=True, timeout=10)
            print("[System] Stopped background Ollama service (Linux).")
        except Exception:
            pass  # Service might not be running
    elif IS_WINDOWS:
        try:
            # On Windows, try to stop Ollama if running as a process
            subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], 
                         capture_output=True, timeout=10)
            print("[System] Stopped Ollama process (Windows).")
        except Exception:
            pass  # Process might not be running

def list_audio_devices():
    """List available audio input devices for user reference"""
    print("\n[Audio Devices] Available input devices:")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"  [{i}] {dev['name']}")
    print()

# --- MAIN EXECUTION LOGIC ---
if __name__ == "__main__":
    stop_ollama_service()
    
    # Show available audio devices (helpful for Windows Bluetooth setup)
    if IS_WINDOWS:
        list_audio_devices()
        print("[Info] On Windows, ensure your Bluetooth audio device is paired and set as input.")
        print("[Info] You may need to select the correct device index in the code.\n")

    print(f"[System] Starting assistant using {MODEL_NAME} via CLI.")
    print("[System] Listening... Speak clearly into your microphone.")

    # Assign the stream instance to the global variable
    # On Windows, you might need to specify device=<index> from the list above
    # Example: sd.RawInputStream(..., device=1, ...)
    try:
        with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=8000, 
                               dtype='int16', channels=1, callback=callback) as stream:
            current_stream = stream  # Set the global variable
            print("[System] Audio stream started successfully.")
            
            while True:
                data = Q.get()
                
                # Skip processing if we're currently speaking (prevents TTS echo)
                if is_speaking:
                    continue
                
                if recognizer.AcceptWaveform(data):
                    result_json = recognizer.Result()
                    user_spoken_text = json.loads(result_json).get('text', '').strip()
                    
                    # Filter out common noise words and short utterances
                    if user_spoken_text and len(user_spoken_text) > 2 and user_spoken_text not in ["the", "a", "uh", "um"]:
                        if user_spoken_text.lower() == 'exit':
                            print("[System] Exit command received. Shutting down...")
                            break
                        
                        assistant_response = get_chat_response_cli(user_spoken_text)

                        if not assistant_response.startswith(("Sorry,", "Error:")):
                            # Speak function now handles muting/unmuting the stream
                            speak(assistant_response)
                        else:
                            print(f"[System] {assistant_response}")
                        print("-" * 30)
    except sd.PortAudioError as e:
        print(f"[Error] Audio device error: {e}")
        if IS_WINDOWS:
            print("[Info] Try specifying a device index. Edit the code and add device=<index> to RawInputStream")
            list_audio_devices()
        sys.exit(1)


