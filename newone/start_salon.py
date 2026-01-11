"""
Salon Voice Assistant Launcher
Starts all components: Voice Assistant + Appointment Viewer
"""

import subprocess
import sys
import time

print("=" * 60)
print("🎙️  GLAMOUR SALON VOICE ASSISTANT")
print("=" * 60)
print()
print("Starting system components...")
print()

# Start appointment viewer in separate process
print("📅 Launching Appointment Viewer...")
viewer_process = subprocess.Popen([sys.executable, "appointment_viewer.py"])
time.sleep(1)  # Give it time to start

# Start voice assistant
print("🎙️  Starting Voice Assistant...")
print()
print("=" * 60)
print("SYSTEM READY")
print("=" * 60)
print()
print("Features:")
print("  ✓ Check appointment availability")
print("  ✓ Book new appointments")
print("  ✓ Call manager for special requests")
print("  ✓ Real-time appointment viewer")
print()
print("Say 'exit' to quit")
print("=" * 60)
print()

try:
    # Run voice assistant (blocking)
    subprocess.run([sys.executable, "voice_assistant.py"])
except KeyboardInterrupt:
    print("\n\n[System] Shutting down...")
finally:
    # Clean up
    viewer_process.terminate()
    print("[System] Goodbye!")
