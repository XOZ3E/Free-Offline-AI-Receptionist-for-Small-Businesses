import json
import requests
import pyttsx3
import vosk
import sounddevice as sd
import numpy as np
import os

# --- CONFIGURATION ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b" # Or qwen2.5:3b, phi3:latest
KNOWLEDGE_BASE_PATH = "knowledge_base.json"

# --- 1. TTS Setup (pyttsx3) ---
engine = pyttsx3.init()
engine.setProperty('rate', 150) # Speed of speech
engine.setProperty('volume', 0.9) # Volume

def speak(text):
    print(f"Aura speaking: {text}")
    engine.say(text)
    engine.runAndWait()

# --- 2. LLM Setup (Ollama API Call) ---
def get_ollama_response(user_input, knowledge_base_data):
    # Load knowledge base content dynamically into the prompt template
    system_prompt = f"""
    You are an offline call assistant named "Aura". Your role is to help the user manage their phone calls by providing concise, relevant information based on the user's spoken input during an active phone call.

    **CONTEXT AND KNOWLEDGE BASE:**
    Below is specific information provided in a JSON format. Use this data ONLY if it is relevant to the user's current question or the flow of the conversation. Do not mention the knowledge base unless explicitly asked.

    --- START KNOWLEDGE BASE ---
    {json.dumps(knowledge_base_data, indent=2)}
    --- END KNOWLEDGE BASE ---

    **RULES:**
    1. Keep responses brief, polite, and to the point.
    2. Maintain the context of the call; do not generate unrelated information.
    3. If the answer is not in the Knowledge Base and you don't know it, respond naturally: "I'm sorry, I don't have that information."
    4. Format all responses as plain text for the TTS engine. No Markdown formatting.

    Respond only with the text that should be spoken aloud to the user.
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": user_input,
        "system": system_prompt,
        "stream": False # Set to False for single, complete response
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['response'].strip()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
        return "Sorry, the assistant is offline."


# --- 3. STT Setup (Vosk) ---
# You need to download a Vosk model (e.g., small English model) and specify the path
# Example model path: "vosk-model-small-en-us-0.22"
VOSK_MODEL_PATH = "" 

if not os.path.exists(VOSK_MODEL_PATH):
    print(f"Vosk model not found at {VOSK_MODEL_PATH}. Please download one.")
    # Add logic here to download a model if needed

model = vosk.Model(VOSK_MODEL_PATH)
samplerate = 16000 # Standard sample rate for speech models
device = 0 # Default audio input device

def listen_and_transcribe():
    print("Listening for user input...")
    with sd.RawInputStream(samplerate=samplerate, blocksize = 8000, device=device, dtype='int16', channels=1, callback=callback):
        # Implement continuous listening loop here (e.g., using queues or similar logic)
        pass

# You need a callback function to handle audio chunks
# ... (Example implementation involves queue management which is more complex) ...


# --- MAIN EXECUTION LOGIC (Conceptual) ---
if __name__ == "__main__":
    # 1. Load the knowledge base data
    try:
        with open(KNOWLEDGE_BASE_PATH, 'r') as f:
            knowledge_data = json.load(f)
    except FileNotFoundError:
        print(f"Knowledge base file not found at {KNOWLEDGE_BASE_PATH}")
        knowledge_data = {}

    # 2. Main loop for interaction
    while True:
        # In a real app, this waits for the user to speak via Vosk
        user_spoken_text = input("User (type input): ") # Replace with Vosk output

        if user_spoken_text.lower() == 'exit':
            break

        # 3. Get LLM Response
        assistant_response = get_ollama_response(user_spoken_text, knowledge_data)

        # 4. Speak response
        speak(assistant_response)


