"""
Manager Alert System - Tkinter GUI
Shows "Manager Required" alert with 30-second countdown
Returns True when timeout completes so voice assistant can say "manager will call you back"
"""

import tkinter as tk
from tkinter import ttk
import threading
import time

class ManagerAlert:
    def __init__(self):
        self.alert_window = None
        self.countdown = 30
        self.is_active = False
        self.callback_triggered = False
    
    def show_alert(self, callback=None):
        """
        Show manager alert popup with countdown
        callback: Function to call after 30 seconds (for voice assistant to speak)
        """
        if self.is_active:
            return  # Don't show multiple alerts
        
        self.is_active = True
        self.countdown = 30
        self.callback_triggered = False
        
        # Create popup window
        self.alert_window = tk.Toplevel()
        self.alert_window.title("⚠️ Manager Required")
        self.alert_window.geometry("500x350")
        self.alert_window.configure(bg="#FF6B6B")
        self.alert_window.attributes("-topmost", True)  # Always on top
        
        # Prevent window close
        self.alert_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Center window
        self.alert_window.update_idletasks()
        width = self.alert_window.winfo_width()
        height = self.alert_window.winfo_height()
        x = (self.alert_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.alert_window.winfo_screenheight() // 2) - (height // 2)
        self.alert_window.geometry(f"+{x}+{y}")
        
        # Alert icon
        icon_label = tk.Label(
            self.alert_window,
            text="🔔",
            font=("Arial", 60),
            bg="#FF6B6B",
            fg="white"
        )
        icon_label.pack(pady=20)
        
        # Main message
        message_label = tk.Label(
            self.alert_window,
            text="MANAGER REQUIRED",
            font=("Arial", 24, "bold"),
            bg="#FF6B6B",
            fg="white"
        )
        message_label.pack(pady=10)
        
        # Subtext
        subtext_label = tk.Label(
            self.alert_window,
            text="Customer needs to speak with manager",
            font=("Arial", 14),
            bg="#FF6B6B",
            fg="white"
        )
        subtext_label.pack(pady=5)
        
        # Countdown label
        self.countdown_label = tk.Label(
            self.alert_window,
            text=f"Auto-close in: {self.countdown} seconds",
            font=("Arial", 16, "bold"),
            bg="#FF6B6B",
            fg="white"
        )
        self.countdown_label.pack(pady=20)
        
        # Progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("red.Horizontal.TProgressbar", 
                       troughcolor='#CC5555',
                       bordercolor='#FF6B6B',
                       background='white',
                       lightcolor='white',
                       darkcolor='white')
        
        self.progress = ttk.Progressbar(
            self.alert_window,
            style="red.Horizontal.TProgressbar",
            orient=tk.HORIZONTAL,
            length=400,
            mode='determinate',
            maximum=30,
            value=30
        )
        self.progress.pack(pady=10)
        
        # Dismiss button
        dismiss_btn = tk.Button(
            self.alert_window,
            text="✓ Manager Notified",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#FF6B6B",
            activebackground="#f0f0f0",
            relief=tk.RAISED,
            padx=20,
            pady=10,
            command=lambda: self.close_alert(callback)
        )
        dismiss_btn.pack(pady=15)
        
        # Start countdown in separate thread
        countdown_thread = threading.Thread(target=self._countdown_timer, args=(callback,), daemon=True)
        countdown_thread.start()
    
    def _countdown_timer(self, callback):
        """Run countdown timer"""
        while self.countdown > 0 and self.is_active:
            time.sleep(1)
            self.countdown -= 1
            
            # Update UI safely using after() method
            if self.alert_window and self.is_active:
                try:
                    self.alert_window.after(0, lambda: self._update_countdown_display())
                except:
                    break
        
        # Timeout reached
        if self.is_active and not self.callback_triggered:
            self.close_alert(callback)
    
    def _update_countdown_display(self):
        """Update countdown display (must be called from main thread)"""
        if self.alert_window and self.is_active:
            try:
                self.countdown_label.config(text=f"Auto-close in: {self.countdown} seconds")
                self.progress['value'] = self.countdown
            except:
                pass
    
    def close_alert(self, callback=None):
        """Close the alert and trigger callback"""
        self.is_active = False
        
        try:
            if self.alert_window:
                self.alert_window.destroy()
        except:
            pass
        
        # Trigger callback (voice assistant says "manager will call you back")
        if callback and not self.callback_triggered:
            self.callback_triggered = True
            callback()

# Global manager alert instance
manager_alert = ManagerAlert()

def trigger_manager_alert(callback=None):
    """
    Trigger manager alert from voice assistant
    Usage: trigger_manager_alert(lambda: speak("The manager will call you back shortly"))
    """
    manager_alert.show_alert(callback)

# Test/Demo
if __name__ == "__main__":
    def test_callback():
        print("✓ Callback triggered! Voice assistant would say: 'The manager will call you back shortly'")
    
    # Create hidden root window
    root = tk.Tk()
    root.withdraw()
    
    # Show alert
    print("Testing manager alert system...")
    trigger_manager_alert(test_callback)
    
    root.mainloop()
