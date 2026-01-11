import json
import requests
import sounddevice as sd
import numpy as np
import os
import sys
import queue
import threading
import time
from datetime import datetime
from faster_whisper import WhisperModel
import pyttsx3
import tkinter as tk
from booking_tools import check_availability, book_appointment, get_todays_appointments
from manager_alert import trigger_manager_alert
import torch
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

# --- CONFIGURATION ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

# --- Conversation History ---
conversation_history = []

# --- Load Knowledge Base ---
KB_PATH = "knowledge_base.json"

def load_knowledge_base():
    """Load knowledge base from JSON file"""
    try:
        with open(KB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[Error] Knowledge base not found at: {KB_PATH}")
        sys.exit(1)

kb = load_knowledge_base()

# Extract configuration from KB
ASSISTANT_NAME = kb["assistant_info"]["name"]
BUSINESS_NAME = kb["business_info"]["name"]
OWNER_NAME = kb["business_info"]["owner_name"]

# Build context for system prompt from KB
def build_kb_context():
    """Build context string from knowledge base for salon"""
    context = f"""
SALON INFO:
- Name: {kb['business_info']['name']}
- Owner: {kb['business_info']['owner_name']}
- Phone: {kb['business_info']['phone']}
- Address: {kb['business_info']['address']}

BUSINESS HOURS:
- Weekdays: {kb['business_hours']['monday_to_friday']}
- Saturday: {kb['business_hours']['saturday']}
- Sunday: {kb['business_hours']['sunday']}

SERVICES:
"""
    
    # Add services with pricing
    for category, services in kb["services"].items():
        context += f"\n{category.upper()}:\n"
        for service_name, details in services.items():
            context += f"  - {service_name.replace('_', ' ').title()}: ${details['price']} ({details['duration']} min)\n"
    
    # Add staff
    context += f"\nSTAFF:\n"
    for role, members in kb["staff"].items():
        context += f"  - {role.replace('_', ' ').title()}: {', '.join(members)}\n"
    
    # Add policies
    context += f"\nPOLICIES:\n"
    for policy_name, policy_text in kb["policies"].items():
        context += f"  - {policy_name.title()}: {policy_text}\n"
    
    return context

SYSTEM_PROMPT = f"""
You are {ASSISTANT_NAME}, the AI receptionist for {BUSINESS_NAME}.

{build_kb_context()}

=== BOOKING PROCESS (STRICT VALIDATION) ===

🚨 CRITICAL RULE: NEVER make up or assume customer information!
🚨 You are NOT the customer! Do NOT use your own name "Sophia" for bookings!

WHEN CUSTOMER WANTS TO BOOK:
1. Customer says "book", "appointment", "schedule"
2. YOU MUST ASK: "I'd be happy to help! What's your name?"
3. WAIT for customer to provide their name
4. YOU MUST ASK: "And your phone number?"
5. WAIT for customer to provide phone number
6. Only then ask about service, date, time

📋 INFORMATION CHECKLIST (Must collect in order):
[ ] NAME - customer must tell you their name
[ ] PHONE - customer must tell you their phone number
[ ] SERVICE - which service they want
[ ] DATE - which day they want
[ ] TIME - what time they want

⚡ IMMEDIATE EXECUTION RULE:
AS SOON AS you have all 5 items (name, phone, service, date, time):
→ IMMEDIATELY output: TOOL:BOOK:name|phone|YYYY-MM-DD|HH:MM AM/PM|service|price|duration
→ DO NOT say "details are noted" or "appointment confirmed" - EXECUTE THE TOOL!
→ DO NOT ask "is this confirmed?" - JUST EXECUTE THE TOOL!

❌ FORBIDDEN - DO NOT BOOK IF:
- Customer hasn't provided their name
- Customer hasn't provided their phone number
- You're using "Sophia" as name (that's YOU, not the customer!)
- You're making up phone numbers like 555-1234567

✅ CORRECT BEHAVIOR:
When customer says: "I want haircut on Monday at 10 AM"
And you already have: Name=Davis, Phone=555462125
Then IMMEDIATELY respond with: "TOOL:BOOK:Davis|555462125|2025-12-29|10:00 AM|Men's Haircut|25|30"
NOT: "Your details are noted" ← WRONG!

EXAMPLE CORRECT FLOW:
User: "I want a haircut on Monday"
You: "I'd be happy to help! What's your name?"
User: "Kevin"
You: "Thanks Kevin! What's your phone number?"
User: "555-8888"
You: "Perfect! What time on Monday?"
User: "10 AM"
You: "TOOL:BOOK:Kevin|555-8888|2025-12-29|10:00 AM|Men's Haircut|25|30"
← Notice: IMMEDIATELY executed tool, didn't say "confirmed" first!

EXAMPLE WRONG (DO NOT DO THIS):
User: "I want a haircut on Monday at 10 AM" (you already have name=Davis, phone=555462125)
You: "Your details are noted" ← WRONG! Should execute TOOL:BOOK instead!
CORRECT: "TOOL:BOOK:Davis|555462125|2025-12-29|10:00 AM|Men's Haircut|25|30"

=== OTHER TOOLS ===
- CHECK_SLOTS: "TOOL:CHECK_SLOTS:YYYY-MM-DD" - only when asking about availability
- CALL_MANAGER: "TOOL:CALL_MANAGER" - when customer needs to speak with manager/owner

WHEN TO CALL MANAGER:
- Customer asks to "speak with manager", "talk to owner", "escalate"
- Customer has special requests you cannot handle (group bookings, party events, complaints)
- Customer mentions "manager", "owner", "Maria" (owner's name)
- Use: "TOOL:CALL_MANAGER"

RULES:
1. Keep responses SHORT (1 sentence)
2. Don't use tools for general questions
3. ALWAYS get name and phone BEFORE booking
4. NEVER use your own name (Sophia) in bookings
5. Offer to connect with manager if customer seems unsatisfied or has special needs
"""

# --- Whisper Model Setup ---
WHISPER_MODEL_SIZE = "base"  # Options: tiny, base, small, medium, large-v3
# base = ~150MB, good balance | medium = ~1.5GB, best for accents

# --- Global state management (like LiveKit agents) ---
is_speaking = False  # Flag to indicate TTS is active
audio_stream = None  # Reference to the audio stream
stream_lock = threading.Lock()  # Thread-safe stream control
whisper_model = None  # Will be initialized in main

# --- TTS Engine Setup ---
def init_tts():
    """Initialize pyttsx3 TTS engine"""
    engine = pyttsx3.init()
    engine.setProperty('rate', 165)
    engine.setProperty('volume', 0.9)
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)  # Female voice if available
    return engine

def speak(text):
    """
    Professional TTS management with Piper:
    1. Stop audio input stream
    2. Clear any queued audio
    3. Synthesize and speak with Piper
    4. Wait for audio to clear
    5. Restart input stream
    """
    global is_speaking, audio_stream, piper_voice
    
    print(f"\n{ASSISTANT_NAME} speaking: {text}")
    if not text or len(text) == 0:
        print("[Warning] Empty text, skipping TTS")
        return
    
    with stream_lock:
        try:
            # Step 1: Stop microphone input
            is_speaking = True
            if audio_stream:
                audio_stream.stop()
                print("[Microphone] MUTED during TTS")
            
            # Step 2: Clear any audio data captured before muting
            while not Q.empty():
                try:
                    Q.get_nowait()
                except queue.Empty:
                    break
            
            # Step 3: Initialize fresh engine and speak
            engine = init_tts()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
            
            print("[TTS] Finished speaking")
            
            # Step 4: Wait for audio to physically clear
            time.sleep(0.3)
            
        except Exception as e:
            print(f"[TTS Error] {e}")
        
        finally:
            # Step 5: Resume listening
            if audio_stream:
                audio_stream.start()
                print("[Microphone] UNMUTED - Ready to listen\n" + "-"*30)
            is_speaking = False


# --- LLM Setup (Ollama API with Streaming) ---
def get_current_context():
    """Get current time and day context for intelligent responses"""
    now = datetime.now()
    day_name = now.strftime("%A")
    current_time = now.strftime("%I:%M %p")
    hour = now.hour
    
    # Determine what Kevin should be doing based on schedule from KB
    activity = "unknown"
    
    # Map day to schedule key
    if day_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        schedule_key = "monday_to_friday"
    elif day_name == "Saturday":
        schedule_key = "saturday"
    elif day_name == "Sunday":
        schedule_key = "sunday"
    else:
        schedule_key = None
    
    # Find current activity from KB schedule
    if schedule_key and "daily_schedule" in kb and schedule_key in kb["daily_schedule"]:
        schedule = kb["daily_schedule"][schedule_key]
        # Find the most recent time slot that has passed
        for time_key, activity_desc in schedule.items():
            # Extract hour from time_key (e.g., "7:30_AM" -> 7, "3:30_PM" -> 15)
            try:
                time_parts = time_key.split("_")
                time_str = time_parts[0]
                period = time_parts[1] if len(time_parts) > 1 else "AM"
                
                hour_min = time_str.split(":")
                schedule_hour = int(hour_min[0])
                
                # Convert to 24-hour format
                if period == "PM" and schedule_hour != 12:
                    schedule_hour += 12
                elif period == "AM" and schedule_hour == 12:
                    schedule_hour = 0
                
                # Check if current time is past this schedule time
                if hour >= schedule_hour:
                    activity = activity_desc
            except:
                continue
    
    return f"""
CURRENT TIME CONTEXT:
- Current Day: {day_name}
- Current Time: {current_time}
- Kevin is likely: {activity}
"""

def get_ollama_response_stream(user_input):
    """Get LLM response and process any tool commands"""
    global conversation_history
    
    print(f"\nUser said: {user_input}")
    
    # Add current time context
    now = datetime.now()
    time_context = f"Current date/time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"
    
    # Add user message to history
    conversation_history.append({"role": "user", "content": user_input})
    
    # Build conversation context (last 10 messages to keep context manageable)
    recent_history = conversation_history[-10:]
    conversation_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
        for msg in recent_history
    ])
    
    # Combine time context and conversation
    enhanced_prompt = f"{time_context}\n\nConversation history:\n{conversation_text}"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": enhanced_prompt,
        "system": SYSTEM_PROMPT,
        "stream": True
    }
    
    full_response = ""
    try:
        with requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=180) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line.decode('utf-8'))
                        chunk = json_response.get('response', '')
                        full_response += chunk
                        
                        if json_response.get('done'):
                            break
                    except json.JSONDecodeError:
                        continue
    except requests.exceptions.RequestException as e:
        print(f"[Error] Ollama API: {e}")
        return "Sorry, the assistant is offline."
    
    # Process any tool commands
    response = full_response.strip()
    
    # Check for tool commands
    if "TOOL:CHECK_SLOTS:" in response:
        date_str = response.split("TOOL:CHECK_SLOTS:")[1].split()[0].strip()
        print(f"[Tool] Checking availability for {date_str}...")
        result = check_availability(date_str)
        
        if "error" in result:
            return result["error"]
        else:
            slots_count = result.get("total", 0)
            if slots_count > 0:
                # Show first 5 slots
                slots_preview = ", ".join(result["available_slots"][:5])
                return f"We have {slots_count} openings on that day. Available times include {slots_preview}. Would you like to book one?"
            else:
                return "That day is fully booked. Would you like to try a different day?"
    
    elif "TOOL:BOOK:" in response:
        # Parse booking details: name|phone|date|time|service|price|duration
        try:
            # Extract only the TOOL:BOOK line, ignore any text after it
            tool_line = response.split("TOOL:BOOK:")[1].split("\n")[0].strip()
            parts = tool_line.split("|")
            
            # Validate we have all 7 required fields
            if len(parts) < 7:
                print(f"[Tool Error] Missing booking information. Got {len(parts)} fields, need 7")
                missing = []
                if len(parts) < 1: missing.append("name")
                if len(parts) < 2: missing.append("phone")
                if len(parts) < 3: missing.append("date")
                if len(parts) < 4: missing.append("time")
                if len(parts) < 5: missing.append("service")
                if len(parts) < 6: missing.append("price")
                if len(parts) < 7: missing.append("duration")
                return f"I need more information to book. Please provide: {', '.join(missing)}"
            
            name, phone, date, time_slot, service, price_str, duration_str = parts[:7]
            
            # 🚨 CHECKSUM VALIDATION: Must have name and phone
            name = name.strip()
            phone = phone.strip()
            
            # Reject if using assistant's own name
            if name.lower() in ["sophia", "assistant", "ai", "bot"]:
                print(f"[Tool Error] ❌ CHECKSUM FAILED: Cannot use assistant name '{name}' as customer")
                return "I need the CUSTOMER's name, not mine! What is YOUR name?"
            
            if not name or len(name) < 2:
                print(f"[Tool Error] ❌ CHECKSUM FAILED: Invalid name '{name}'")
                return "I need your full name to complete the booking. What's your name?"
            
            # Reject fake/placeholder phone numbers
            if not phone or len(phone) < 7 or phone.startswith("555-123") or phone.startswith("555-000"):
                print(f"[Tool Error] ❌ CHECKSUM FAILED: Invalid phone '{phone}'")
                return "I need a valid phone number to complete the booking. What's your phone number?"
            
            # Clean up all fields - remove extra characters, newlines, asterisks
            date = date.strip()
            time_slot = time_slot.strip()
            service = service.strip()
            
            # Clean up price (remove $, spaces, commas, extra chars)
            price_str = price_str.strip().replace('$', '').replace(',', '').replace('*', '')
            # Extract just the number from price_str
            price_str = ''.join(c for c in price_str if c.isdigit())
            
            # Clean up duration (remove min, spaces, asterisks, newlines, extra text)
            duration_str = duration_str.strip().replace('min', '').replace('*', '').split()[0]
            # Extract just the number from duration_str
            duration_str = ''.join(c for c in duration_str if c.isdigit())
            
            print(f"[Tool] ✓ CHECKSUM PASSED - Name: {name}, Phone: {phone}")
            print(f"[Tool] Booking appointment for {name}...")
            print(f"[Tool] Details: {phone}, {date}, {time_slot}, {service}, ${price_str}, {duration_str}min")
            
            result = book_appointment(
                customer_name=name,
                phone=phone,
                date_str=date,
                time_str=time_slot,
                service=service,
                price=int(price_str),
                duration=int(duration_str)
            )
            
            if result["success"]:
                print(f"[Tool] ✓ Appointment #{result['appointment']['id']} created successfully!")
                return f"Perfect! Your appointment is confirmed for {date} at {time_slot}. See you then, {name}!"
            else:
                return f"Sorry, that time isn't available. {result.get('error', '')}"
        except Exception as e:
            print(f"[Tool Error] Booking failed: {e}")
            import traceback
            traceback.print_exc()
            return "I had trouble with that booking. Can you confirm your name, phone number, date, time, and service?"
    
    elif "TOOL:CALL_MANAGER" in response:
        print("[Tool] Calling manager...")
        # Trigger manager alert (runs in main thread to avoid tkinter issues)
        try:
            trigger_manager_alert(lambda: speak("The manager will call you back shortly."))
        except Exception as e:
            print(f"[Tool Error] Manager alert failed: {e}")
        return "One moment please, I'm getting the manager for you."
    
    # Clean up regular response
    response = response.replace('**', '').replace('```', '').replace('###', '')
    
    # Remove any remaining tool commands from response
    for tool_marker in ["TOOL:CHECK_SLOTS:", "TOOL:BOOK:", "TOOL:CALL_MANAGER"]:
        if tool_marker in response:
            response = response.split(tool_marker)[0].strip()
    
    # Stop at common markers
    stop_markers = ['---', 'Example:', 'Transcript:', 'Caller:', 'NOTE:', 'RULES:', 'TOOL:']
    for marker in stop_markers:
        if marker in response:
            response = response.split(marker)[0].strip()
    
    # Limit to first 2-3 sentences max
    sentences = response.split('. ')
    if len(sentences) > 2:
        response = '. '.join(sentences[:2]) + '.'
    
    # Hard limit on length
    if len(response) > 300:
        response = response[:300].rsplit(' ', 1)[0] + '.'
    
    # Add assistant response to history
    conversation_history.append({"role": "assistant", "content": response.strip()})
    
    return response.strip()

# --- STT Setup (Whisper with Silero VAD) ---
SAMPLERATE = 16000
Q = queue.Queue()

# Initialize Silero VAD model
print("[System] Loading Silero VAD model...")
silero_model = load_silero_vad()
print("[System] Silero VAD loaded!")

def detect_speech_silero(audio_data):
    """Use Silero VAD to detect if audio contains speech"""
    # Convert bytes to torch tensor
    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    audio_tensor = torch.from_numpy(audio_np)
    
    # Get speech timestamps
    speech_timestamps = get_speech_timestamps(audio_tensor, silero_model, sampling_rate=SAMPLERATE)
    
    return len(speech_timestamps) > 0

def transcribe_audio(audio_data):
    """Transcribe audio using Whisper"""
    global whisper_model
    
    try:
        # Convert to float32
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Transcribe with Whisper
        segments, info = whisper_model.transcribe(
            audio_np,
            language="en",
            vad_filter=True,
            beam_size=5
        )
        
        text = " ".join([segment.text for segment in segments]).strip()
        return text
        
    except Exception as e:
        print(f"[Whisper Error] {e}")
        return ""

def callback(indata, frames, time, status):
    """Audio callback - queues audio for Whisper processing"""
    if status:
        print(status, file=sys.stderr)
    
    # Critical: Do not capture audio during TTS playback
    if not is_speaking:
        Q.put(bytes(indata))

# --- Helper Functions ---
def list_audio_devices():
    """List available audio input devices"""
    print("\n[Audio Devices] Available input devices:")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"  [{i}] {dev['name']}")
    print()

# --- MAIN EXECUTION LOGIC ---
if __name__ == "__main__":
    list_audio_devices()

    print(f"[System] Starting assistant using {MODEL_NAME} via API.")
    
    print(f"[System] Loading Whisper {WHISPER_MODEL_SIZE} model...")
    
    # Initialize Whisper model
    whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    print("[System] Whisper model loaded successfully!")
    
    print("[System] Listening... Speak clearly into your microphone.")
    print("[Info] Using Silero VAD: Records until you stop speaking")
    
    # Silero VAD state
    audio_buffer = []
    is_recording = False
    silence_chunks = 0
    MAX_SILENCE_CHUNKS = 8  # ~0.5 seconds of silence (8 * 0.06s per chunk)
    MIN_RECORDING_CHUNKS = 8  # Minimum ~0.5 seconds of speech

    try:
        with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=8000, 
                               dtype='int16', channels=1, callback=callback) as stream:
            
            audio_stream = stream
            print("[System] Audio stream started successfully.")
            
            # Introduction greeting
            greeting = f"Hello! I'm {ASSISTANT_NAME}, your AI receptionist at {BUSINESS_NAME}. How can I help you today?"
            print(f"[Greeting] {greeting}")
            speak(greeting)
            
            print("[Ready] 🎤 Listening for speech...\n")
            
            while True:
                data = Q.get()
                
                if is_speaking:
                    continue
                
                # Use Silero VAD to detect speech
                has_speech = detect_speech_silero(data)
                
                if has_speech:
                    # Speech detected
                    if not is_recording:
                        print("[🔴 Recording] Speech detected...")
                        is_recording = True
                        audio_buffer = []
                    
                    silence_chunks = 0  # Reset silence counter
                    audio_buffer.append(data)
                    
                else:
                    # No speech detected
                    if is_recording:
                        silence_chunks += 1
                        audio_buffer.append(data)  # Keep buffering during silence
                        
                        # Check if silence threshold reached
                        if silence_chunks >= MAX_SILENCE_CHUNKS:
                            # Check minimum duration
                            if len(audio_buffer) >= MIN_RECORDING_CHUNKS:
                                print(f"[⏹️  Stopped] Processing speech ({len(audio_buffer) * 0.06:.1f}s)...")
                                
                                # Transcribe
                                combined_audio = b''.join(audio_buffer)
                                user_spoken_text = transcribe_audio(combined_audio)
                                
                                # Reset state
                                is_recording = False
                                silence_chunks = 0
                                audio_buffer = []
                                
                                # Process transcription
                                ignore_words = ['the', 'a', 'an', 'uh', 'um', 'huh', 'oh', 'ah', 'er', 'mm']
                                
                                if user_spoken_text and len(user_spoken_text) > 4 and user_spoken_text.lower() not in ignore_words:
                                    print(f"[Detected] '{user_spoken_text}'")
                                    
                                    if user_spoken_text.lower() == 'exit':
                                        print("[System] Exit command received. Shutting down...")
                                        break
                                    
                                    print("[System] Sending request to Ollama...")
                                    assistant_response = get_ollama_response_stream(user_spoken_text)
                                    print(f"[Response] '{assistant_response}'")

                                    if assistant_response:
                                        speak(assistant_response)
                                    
                                    print("\n[Ready] 🎤 Listening for speech...\n")
                                else:
                                    if user_spoken_text:
                                        print(f"[Ignored] '{user_spoken_text}' (too short or noise)")
                                    print("[Ready] 🎤 Listening for speech...\n")
                            else:
                                # Too short, ignore
                                is_recording = False
                                silence_chunks = 0
                                audio_buffer = []
                            
    except sd.PortAudioError as e:
        print(f"[Error] Audio device error: {e}")
        list_audio_devices()
        sys.exit(1)
