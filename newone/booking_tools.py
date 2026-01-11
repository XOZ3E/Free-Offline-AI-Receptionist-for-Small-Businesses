"""
Booking Tools for Salon Voice Assistant
Handles appointment scheduling, availability checking, and bookings management
"""

import json
from datetime import datetime, timedelta
import os

BOOKINGS_FILE = "bookings.json"

def load_bookings():
    """Load bookings from JSON file"""
    try:
        with open(BOOKINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"appointments": [], "next_appointment_id": 1}

def save_bookings(data):
    """Save bookings to JSON file"""
    with open(BOOKINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def parse_time(time_str):
    """Convert time string like '10:00 AM' to datetime object"""
    return datetime.strptime(time_str, "%I:%M %p")

def check_availability(date_str, requested_time=None):
    """
    Check available time slots for a given date
    Returns list of available slots
    """
    data = load_bookings()
    
    # Parse the requested date
    try:
        req_date = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
    
    # Check if it's Sunday (closed)
    if req_date.weekday() == 6:
        return {"error": "We're closed on Sundays"}
    
    # Get appropriate time slots
    is_saturday = req_date.weekday() == 5
    available_slots = data["time_slots"]["saturday" if is_saturday else "monday_to_friday"]
    
    # Filter out booked slots
    booked_times = [
        appt["time"] for appt in data["appointments"]
        if appt["date"] == date_str and appt["status"] == "confirmed"
    ]
    
    open_slots = [slot for slot in available_slots if slot not in booked_times]
    
    if requested_time:
        # Check specific time
        if requested_time in open_slots:
            return {"available": True, "time": requested_time, "date": date_str}
        else:
            return {"available": False, "message": f"{requested_time} is not available", "open_slots": open_slots[:5]}
    
    return {"available_slots": open_slots, "date": date_str, "total": len(open_slots)}

def book_appointment(customer_name, phone, date_str, time_str, service, staff="Any", duration=60, price=0):
    """
    Book a new appointment
    Returns confirmation details or error
    """
    data = load_bookings()
    
    # Check if slot is available
    availability = check_availability(date_str, time_str)
    if not availability.get("available", False):
        return {"success": False, "error": "Time slot not available", "suggestion": availability.get("open_slots", [])}
    
    # Create new appointment
    new_appointment = {
        "id": data["next_appointment_id"],
        "date": date_str,
        "time": time_str,
        "customer_name": customer_name,
        "phone": phone,
        "service": service,
        "staff": staff,
        "duration": duration,
        "price": price,
        "status": "confirmed"
    }
    
    data["appointments"].append(new_appointment)
    data["next_appointment_id"] += 1
    
    save_bookings(data)
    
    return {
        "success": True,
        "appointment": new_appointment,
        "message": f"Appointment confirmed for {customer_name} on {date_str} at {time_str}"
    }

def get_todays_appointments():
    """Get all appointments for today"""
    data = load_bookings()
    today = datetime.now().strftime("%Y-%m-%d")
    
    todays_appts = [
        appt for appt in data["appointments"]
        if appt["date"] == today and appt["status"] == "confirmed"
    ]
    
    # Sort by time
    todays_appts.sort(key=lambda x: parse_time(x["time"]))
    
    return todays_appts

def cancel_appointment(appointment_id):
    """Cancel an appointment by ID"""
    data = load_bookings()
    
    for appt in data["appointments"]:
        if appt["id"] == appointment_id:
            appt["status"] = "cancelled"
            save_bookings(data)
            return {"success": True, "message": f"Appointment #{appointment_id} has been cancelled"}
    
    return {"success": False, "error": "Appointment not found"}

# Test functions
if __name__ == "__main__":
    print("Testing booking tools...")
    
    # Test 1: Check availability for today
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n1. Checking availability for {today}:")
    result = check_availability(today)
    print(f"   Available slots: {result.get('total', 0)}")
    
    # Test 2: Get today's appointments
    print(f"\n2. Today's appointments:")
    appts = get_todays_appointments()
    for appt in appts:
        print(f"   {appt['time']} - {appt['customer_name']} ({appt['service']})")
    
    print("\n✓ Booking tools ready!")
