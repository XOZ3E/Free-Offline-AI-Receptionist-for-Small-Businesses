# Free-Offline-AI-Receptionist-for-Small-Businesses
# 🤖 Open-Source Voice Call Assistant

**A free, offline voice assistant for automatically handling phone calls using BlueZ, Ollama, and voice recognition.**

---
# Check out the newone folder and let me know if you guys need a executable 
# I have used base models as my system doesn't have good hardware replace them with high end if you want 
# switch to this [TTS](https://huggingface.co/spaces/Qwen/Qwen3-TTS) and use your own voice it was recently lauched by Qwen 
# Pls help this project reach every small business and i need someone to develop it for windows cause my pc has issues with network card 
## 🎯 Mission

This project was created to help small businesses and individuals who are being charged excessive fees by commercial AI voice assistant services. Why pay hundreds of dollars per month when you can run your own voice assistant completely free and offline?

I built this system to demonstrate that with a Linux PC, some open-source tools, and a bit of setup, anyone can have their own AI-powered call assistant without subscription fees or privacy concerns.

---
## Why am i doing this cause i know how it works with small business and they try all the ways to expand it and they loose it 
## What do i want in return : 
##Nothing i guess cause i don't have a bank account may be get me a job if you can.

**CHECK OUT THE YOUTUBE VIDEO**: [link](https://youtu.be/DtHNSL8JV_U)
## 🌟 How It Works

The system creates a complete voice call handling pipeline:

```
CALLER 
  ↓
📱 Phone (Auto-answers via Automate app)
  ↓
🔵 Bluetooth Connection
  ↓
💻 PC running BlueZ (acts as Bluetooth headset)
  ↓
🎤 PulseAudio Monitor of Sounds (captures audio)
  ↓
🗣️ Vosk (Speech-to-Text)
  ↓
🧠 Ollama AI Model (generates response)
  ↓
🔊 pyttsx3 (Text-to-Speech)
  ↓
🎧 Monitor of Sounds output
  ↓
💻 PC BlueZ
  ↓
🔵 Bluetooth Connection
  ↓
📱 Phone
  ↓
CALLER hears AI response
```

---

## ✨ Features

- **100% Free & Open Source** - No subscription fees, no API costs
- **Completely Offline** - Your conversations stay private
- **Automatic Call Answering** - Uses Automate app to pick up calls
- **Natural Conversations** - Powered by Ollama AI models
- **Customizable Responses** - Edit the system prompt to fit your needs
- **Low Resource Requirements** - Runs on basic hardware without GPU

---

## 📋 Prerequisites

### Hardware Requirements
- A PC with **Linux** (Ubuntu/Debian recommended) or **Windows 10/11**
- Bluetooth-enabled phone
- Bluetooth adapter on PC (built-in or USB)
- Microphone and speakers (or monitor of sounds routing)

### Software Requirements

#### Linux
- **Linux OS** (tested on Ubuntu 20.04+)
- **Python 3.8+**
- **BlueZ** (Bluetooth stack for Linux)
- **PulseAudio**
- **Ollama** (for running AI models)
- **Automate app** on Android phone (for auto-answering calls)

#### Windows
- **Windows 10/11**
- **Python 3.8+**
- **Ollama for Windows** (for running AI models)
- **Automate app** on Android phone (for auto-answering calls)
- **VB-Audio Virtual Cable** (optional, for advanced audio routing)

---

## 🚀 Installation Guide

---

## 🐧 Linux Installation

### Step 1: Install System Dependencies (Linux)

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install BlueZ and Bluetooth tools
sudo apt install pulseaudio

# Install Python and pip
sudo apt install python3 python3-pip python3-dev -y
```

### Step 2: Install Python Dependencies (Linux)

```bash
pip3 install pyttsx3 vosk sounddevice numpy
```

### Step 3: Install Ollama (Linux)

```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the AI model (phi3 is lightweight and fast)
ollama pull phi3:latest
```

### Step 4: Download Vosk Speech Recognition Model (Linux)

```bash
# Create directory for models
mkdir -p ~/vosk-models
cd ~/vosk-models

# Download English model (or choose your language)
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip

# Extract the model
unzip vosk-model-en-us-0.22.zip

# Note the path - you'll need it in the code
echo "Model path: $(pwd)/vosk-model-en-us-0.22"
```

---

## 🪟 Windows Installation

### Step 1: Install Python (Windows)

1. Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Open Command Prompt or PowerShell

### Step 2: Install Python Dependencies (Windows)

```powershell
pip install pyttsx3 vosk sounddevice numpy
```

### Step 3: Install Ollama (Windows)

1. Download Ollama for Windows from [ollama.com/download](https://ollama.com/download)
2. Run the installer
3. Open Command Prompt and pull the model:

```powershell
ollama pull phi3:latest
```

### Step 4: Download Vosk Speech Recognition Model (Windows)

1. Create a folder for models:
```powershell
mkdir %USERPROFILE%\vosk-models
```

2. Download the model from: https://alphacephei.com/vosk/models
   - Recommended: `vosk-model-en-us-0.22.zip`

3. Extract the ZIP to `C:\Users\<YourUsername>\vosk-models\`

4. The final path should be: `C:\Users\<YourUsername>\vosk-models\vosk-model-en-us-0.22`

**Alternative:** Set a custom path via environment variable:
```powershell
set VOSK_MODEL_PATH=D:\path\to\your\vosk-model
```

### Step 5: Bluetooth Setup (Windows)

Unlike Linux (which uses BlueZ), Windows uses its built-in Bluetooth stack:

1. **Pair your phone** via Windows Settings > Bluetooth & devices
2. **Enable "Hands-free Telephony"** in the Bluetooth device properties
3. When a call comes in, your phone's audio will route through the PC
4. The script will automatically list available audio devices - note the index of your Bluetooth device

**Optional: VB-Audio Virtual Cable**
For advanced audio routing (similar to PulseAudio on Linux):
1. Download from [vb-audio.com/Cable](https://vb-audio.com/Cable/)
2. Install and restart
3. Use it to route audio between applications

---

## 🐧 Linux-Specific Setup (continued)

### Step 5: Configure BlueZ as Bluetooth Headset (Linux only)

**Install BLUEZ from here ** [BLUEZ](https://www.bluez.org/)
Setup all required config and drivers ask me if it doensn't work 

### Step 6: Configure PulseAudio (Linux only)
Only the first time go to Recording and change what ever says monitor for both BLUEZ and voice agent 

### Step 7: Pair Your Phone (Linux)
**Make sure you turn on phone calling on the bluethooth on phone**

---

## 📱 Setup Automate App on Android (All Platforms)

1. Download **Automate** app from Google Play Store
2. Import the provided flow file: `Vfkl.flo` (link in repository)
3. Grant necessary permissions (Phone,logs)
4. Enable the flow
5. Test by calling your phone

The flow automatically:
- Detects incoming calls
- Connects to PC via Bluetooth
- Answers the call
- Routes audio to PC

---

## 🔧 Configuration

### Update the Voice Assistant Code

Edit the Python script and update these variables:

```python
# Change the Vosk model path to where you extracted it
VOSK_MODEL_PATH = "/home/yourusername/vosk-models/vosk-model-en-us-0.22"

# Customize the assistant's behavior
SYSTEM_PROMPT = """
You are an offline call assistant named "Aura" for [YOUR NAME/BUSINESS].
Your role is to answer calls because [REASON].
[ADD YOUR CUSTOM INSTRUCTIONS HERE]
"""

# You can also change the AI model
MODEL_NAME = "phi3:latest"  # or try "llama2", "mistral", etc.
```

### Adjust Voice Settings

```python
# In the speak() function, customize TTS
engine.setProperty('rate', 150)    # Speed (50-300)
engine.setProperty('volume', 0.9)  # Volume (0.0-1.0)

# You can also change the voice
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Try different indices
```

---

## 🎮 Usage

### Running the Voice Assistant

**Linux:**
```bash
# Navigate to your script directory
cd ~/voice-assistant

# Run the assistant
python3 voice_assistant.py
```

**Windows:**
```powershell
# Navigate to your script directory
cd C:\path\to\voice-assistant

# Run the assistant
python voice_assistant.py
```

The assistant will:
1. Start listening for audio input
2. Wait for a call to come in
3. Transcribe the caller's speech
4. Generate AI responses
5. Speak back to the caller
6. Continue the conversation until the call ends

### Stopping the Assistant

- Press `Ctrl+C` in the terminal

---

## 🐛 Troubleshooting

### 🐧 Linux Troubleshooting

#### No Audio from Phone (Linux)
```bash
# Check PulseAudio sources
pactl list sources short

# Restart PulseAudio
pulseaudio -k
pulseaudio --start
```

#### Bluetooth Connection Issues (Linux)
```bash
# Restart Bluetooth
sudo systemctl restart bluetooth

# Re-pair the device
bluetoothctl
remove XX:XX:XX:XX:XX:XX
# Then pair again
```

#### Ollama Not Responding (Linux)
```bash
# Stop background service
sudo systemctl stop ollama

# Run manually to see errors
ollama serve
```

---

### 🪟 Windows Troubleshooting

#### No Audio from Phone (Windows)
1. Check Windows Sound Settings > Recording devices
2. Ensure your Bluetooth device shows as "Hands-Free AG Audio"
3. Set it as default recording device
4. Run the script - it will list available audio devices with their index numbers

#### Bluetooth Connection Issues (Windows)
1. Open Settings > Bluetooth & devices
2. Remove the phone and re-pair
3. Ensure "Hands-free Telephony" is enabled in device properties
4. Restart Bluetooth: Settings > Bluetooth > Toggle Off/On

#### Ollama Not Responding (Windows)
```powershell
# Check if Ollama is running
tasklist | findstr ollama

# Kill and restart
taskkill /F /IM ollama.exe
ollama serve
```

#### Audio Device Selection (Windows)
If the wrong microphone is being used, edit `voice_assistant.py` and specify the device index:
```python
# Find this line and add device parameter:
with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=8000, 
                       dtype='int16', channels=1, callback=callback, device=1) as stream:
#                                                                    ^^^^^^^^
# Replace 1 with your Bluetooth device index from the list shown at startup
```

---

### General Troubleshooting (All Platforms)

#### Poor Speech Recognition
- Speak clearly and at moderate pace
- Reduce background noise
- Try a different Vosk model (larger = more accurate)
- Adjust microphone input levels in your OS sound settings

---

## 🔮 Future Plans

- ~~**Windows Support**: Working on a Windows version using alternative Bluetooth solutions~~ ✅ Done!
- **Better Models**: Optimizing for GPUs to use larger, more capable AI models
- **Web Interface**: Adding a web dashboard to monitor calls and responses
- **Multi-language Support**: Adding support for multiple languages
- **Call Recording**: Optional feature to save call transcripts
- **SMS Integration**: Ability to send follow-up text messages

---

## 🤝 Contributing

This project is open source and welcomes contributions! Whether you:
- Found a bug
- Have a feature suggestion
- Want to improve documentation
- Can help with Windows compatibility
- Want to optimize performance

**All contributions are appreciated!**

---

## 📜 License

This project is released under the MIT License - feel free to use, modify, and distribute as you wish.

---

## ⚠️ Disclaimer

This software is provided as-is for educational and personal use. Please ensure compliance with local laws regarding call recording and automation. Always inform callers if they're speaking with an AI assistant.

---

## 💬 Contact & Support

**Creator**: Kevin (8th Grade Student at Soman Highschool)

**Why I Built This**: I was frustrated seeing small businesses getting charged $200-500/month for basic AI call assistants. This technology should be accessible to everyone, not just those who can afford expensive subscriptions.

**Need Help?**
- 💬 GitHub Issues: [XOZ3E](https://github.com/XOZ3E)
- 💬 Telegram: [XCZGITHUB](https://t.me/XCZGITHUB)
- 💬 Discord: [ENDXCZ](https://discord.gg/tYj5vw2BNM)

---

## 🌟 Support the Project

If this project helped you or your business save money, consider:
- ⭐ Starring the repository
- 🔄 Sharing it with others who might benefit
- 📝 Contributing improvements
- ☕ Buying me a coffee (link if you want donations)

**Together, we can make AI technology accessible to everyone!**

---

**Made with ❤️ to help small businesses thrive without breaking the bank.**

