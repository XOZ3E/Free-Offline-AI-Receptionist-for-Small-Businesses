# Voice Assistant - Knowledge Base Configuration

## Quick Start

To customize the assistant for your business, simply edit `knowledge_base.json`. **No coding required!**

## Configuration Guide

### 1. Assistant Info
```json
"assistant_info": {
  "name": "Aura",              // Name of your assistant
  "role": "call assistant",     // What the assistant does
  "voice_gender": "female"      // Voice preference
}
```

### 2. Business/Owner Info
```json
"business_info": {
  "owner_name": "Kevin",                    // Your name or business owner
  "business_type": "personal assistant",    // Type of business
  "status": "busy with homework"            // Current availability status
}
```

### 3. Student/Employee Info (Optional)
```json
"student_info": {
  "name": "Kevin",
  "grade": "8th grade",
  "school": "Soman High School",
  "current_activities": "working on projects"
}
```

### 4. Response Templates
Use placeholders that get filled automatically:
- `{assistant_name}` - Assistant's name
- `{owner_name}` - Owner's name
- `{status}` - Current status
- `{grade}` - Student grade
- `{school}` - School name

```json
"responses": {
  "greeting": "Hello! This is {assistant_name}. {owner_name} is {status}.",
  "unavailable": "{owner_name} is {status} right now."
}
```

### 5. Business Hours
```json
"business_hours": {
  "weekday_available": "after 4 PM",
  "weekend_available": "most of the day",
  "note": "Additional availability notes"
}
```

### 6. FAQ (Frequently Asked Questions)
```json
"faq": {
  "school_name": "Kevin attends Soman High School.",
  "availability": "Usually available after 4 PM on weekdays."
}
```

## Example: Small Business

```json
{
  "assistant_info": {
    "name": "Sarah",
    "role": "receptionist",
    "voice_gender": "female"
  },
  "business_info": {
    "owner_name": "Mike's Auto Shop",
    "business_type": "auto repair shop",
    "status": "with a customer"
  },
  "business_hours": {
    "weekday_available": "9 AM - 6 PM",
    "weekend_available": "Closed on Sundays",
    "note": "Saturday hours: 9 AM - 2 PM"
  },
  "faq": {
    "services": "We offer oil changes, brake repair, and general maintenance.",
    "location": "We're located at 123 Main Street.",
    "pricing": "Please call back for a quote based on your specific needs."
  }
}
```

## Example: Freelancer

```json
{
  "assistant_info": {
    "name": "Alex",
    "role": "assistant",
    "voice_gender": "female"
  },
  "business_info": {
    "owner_name": "Jessica",
    "business_type": "freelance designer",
    "status": "in a client meeting"
  },
  "responses": {
    "greeting": "Hi! This is {assistant_name}. {owner_name} is {status}. Can I take a message?",
    "portfolio": "{owner_name} specializes in logo design and branding. Would you like to schedule a consultation?"
  }
}
```

## How It Works

1. The assistant loads `knowledge_base.json` on startup
2. All information is used to answer questions intelligently
3. The LLM (Ollama) uses this knowledge to respond accurately
4. **Change the JSON, restart the assistant - that's it!**

## Tips

- Keep responses natural and conversational
- Add all common questions to the FAQ section
- Update status regularly (busy, in meeting, on vacation, etc.)
- Use clear, simple language
- Test responses after making changes

## Restart After Changes

After editing `knowledge_base.json`, restart the voice assistant:
```
python voice_assistant.py
```

The assistant will automatically load your new configuration!
