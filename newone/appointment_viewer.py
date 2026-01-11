"""
Salon Appointment Viewer - Tkinter GUI
Shows all scheduled appointments in real-time
Auto-refreshes every 5 seconds
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os

BOOKINGS_FILE = "bookings.json"

class AppointmentViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("📅 All Appointments - Glamour Salon")
        self.root.geometry("1050x600")
        self.root.configure(bg="#f5f5f5")
        
        # Header
        header_frame = tk.Frame(root, bg="#4A90E2", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="📅 All Appointments",
            font=("Arial", 24, "bold"),
            bg="#4A90E2",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        self.date_label = tk.Label(
            header_frame,
            text="Manager View",
            font=("Arial", 14),
            bg="#4A90E2",
            fg="white"
        )
        self.date_label.pack(side=tk.RIGHT, padx=20)
        
        # Stats Frame
        stats_frame = tk.Frame(root, bg="#f5f5f5", height=60)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.total_label = tk.Label(
            stats_frame,
            text="Total: 0",
            font=("Arial", 12, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        self.total_label.pack(side=tk.LEFT, padx=10)
        
        self.next_label = tk.Label(
            stats_frame,
            text="Next: --:--",
            font=("Arial", 12, "bold"),
            bg="#f5f5f5",
            fg="#4A90E2"
        )
        self.next_label.pack(side=tk.LEFT, padx=20)
        
        # Main content frame with scrollbar
        content_frame = tk.Frame(root, bg="#f5f5f5")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Canvas for scrolling
        canvas = tk.Canvas(content_frame, bg="white")
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="white")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = canvas
        self.next_label.pack(side=tk.LEFT, padx=20)
        
        # Main content frame with scrollbar
        self.status_label = tk.Label(
            root,
            text="🔄 Auto-refresh: ON",
            font=("Arial", 10),
            bg="#f5f5f5",
            fg="#666",
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, padx=20, pady=5)
        
        # Load initial data
        self.refresh_appointments()
        
        # Auto-refresh every 5 seconds
        self.auto_refresh()
    
    def load_bookings(self):
        """Load ALL appointments from JSON file"""
        try:
            with open(BOOKINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Get all confirmed appointments
                all_appts = [
                    appt for appt in data["appointments"]
                    if appt["status"] == "confirmed"
                ]
                
                # Sort by date, then time
                all_appts.sort(key=lambda x: (
                    x["date"],
                    datetime.strptime(x["time"], "%I:%M %p")
                ))
                return all_appts
        except:
            return []
    
    def delete_appointment(self, appt_id):
        """Delete appointment from bookings.json"""
        try:
            with open(BOOKINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Remove appointment with matching ID
            data["appointments"] = [
                appt for appt in data["appointments"]
                if appt["id"] != appt_id
            ]
            
            # Save back to file
            with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            
            # Refresh display
            self.refresh_appointments()
            messagebox.showinfo("✅ Done", "Appointment completed and removed!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete appointment: {e}")
    
    def refresh_appointments(self):
        """Refresh the appointments display"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.appointment_widgets = []
        
        # Load appointments
        appointments = self.load_bookings()
        
        # Update stats
        self.total_label.config(text=f"Total Appointments: {len(appointments)}")
        
        # Find next appointment
        now = datetime.now()
        next_appt = None
        next_appt_date = None
        for appt in appointments:
            appt_datetime = datetime.strptime(f"{appt['date']} {appt['time']}", "%Y-%m-%d %I:%M %p")
            if appt_datetime > now:
                next_appt = appt["time"]
                next_appt_date = appt["date"]
                break
        
        if next_appt and next_appt_date:
            # Format date nicely
            appt_date = datetime.strptime(next_appt_date, "%Y-%m-%d")
            if appt_date.date() == now.date():
                self.next_label.config(text=f"Next: Today {next_appt}")
            else:
                day_name = appt_date.strftime("%a")
                date_str = appt_date.strftime("%m/%d")
                self.next_label.config(text=f"Next: {day_name} {date_str} {next_appt}")
        else:
            self.next_label.config(text="Next: None scheduled")
        
        # Create appointment cards
        for idx, appt in enumerate(appointments):
            self.create_appointment_card(appt, idx)
        
        # Update status
        current_time = datetime.now().strftime("%I:%M:%S %p")
        self.status_label.config(text=f"🔄 Last updated: {current_time}")
    
    def create_appointment_card(self, appt, idx):
        """Create a card for each appointment with Done button"""
        # Card frame
        card = tk.Frame(
            self.scrollable_frame,
            bg="white",
            relief=tk.RAISED,
            borderwidth=1
        )
        card.pack(fill=tk.X, padx=10, pady=5)
        
        # Content frame (left side)
        content = tk.Frame(card, bg="white")
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Format date
        appt_date = datetime.strptime(appt["date"], "%Y-%m-%d")
        day_name = appt_date.strftime("%a")
        date_display = f"{day_name} {appt_date.strftime('%m/%d/%Y')}"
        
        # Row 1: Date and Time
        row1 = tk.Frame(content, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(
            row1,
            text=f"📅 {date_display}  ⏰ {appt['time']}",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#4A90E2"
        ).pack(side=tk.LEFT)
        
        # Row 2: Customer and Phone
        row2 = tk.Frame(content, bg="white")
        row2.pack(fill=tk.X, pady=2)
        tk.Label(
            row2,
            text=f"👤 {appt['customer_name']}",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(
            row2,
            text=f"📞 {appt['phone']}",
            font=("Arial", 10),
            bg="white",
            fg="#666"
        ).pack(side=tk.LEFT)
        
        # Row 3: Service, Staff, Duration, Price
        row3 = tk.Frame(content, bg="white")
        row3.pack(fill=tk.X, pady=2)
        tk.Label(
            row3,
            text=f"✂️ {appt['service']}",
            font=("Arial", 10),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(
            row3,
            text=f"👨‍🔧 {appt['staff']}",
            font=("Arial", 10),
            bg="white",
            fg="#666"
        ).pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(
            row3,
            text=f"⏱️ {appt['duration']} min",
            font=("Arial", 10),
            bg="white",
            fg="#666"
        ).pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(
            row3,
            text=f"💵 ${appt['price']}",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#2ECC71"
        ).pack(side=tk.LEFT)
        
        # Done button (right side)
        done_btn = tk.Button(
            card,
            text="✅ Done",
            font=("Arial", 11, "bold"),
            bg="#2ECC71",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=lambda: self.delete_appointment(appt["id"])
        )
        done_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Hover effect
        def on_enter(e):
            done_btn.config(bg="#27AE60")
        def on_leave(e):
            done_btn.config(bg="#2ECC71")
        
        done_btn.bind("<Enter>", on_enter)
        done_btn.bind("<Leave>", on_leave)
    
    def auto_refresh(self):
        """Auto-refresh every 5 seconds"""
        self.refresh_appointments()
        self.root.after(5000, self.auto_refresh)  # 5000ms = 5 seconds

def main():
    root = tk.Tk()
    app = AppointmentViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
