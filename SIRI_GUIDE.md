# 📱 Siri Integration Guide for RAAS

## Overview

Your RAAS app now supports **Siri voice commands**! Ask Siri about your reminders and get spoken responses.

---

## ✅ What's Working

Two new API endpoints have been added to your FastAPI backend:

### 1. **GET /api/siri/tasks** (JSON format)
Returns your tasks in a simple JSON structure:

```json
{
  "pending": ["Task 1", "Task 2", "Task 3"],
  "done": ["Completed Task"],
  "total_pending": 3,
  "total_done": 1
}
```

### 2. **GET /api/siri/say** (Plain text for Siri)
Returns a spoken sentence that Siri can read aloud:

- **No tasks**: "You have no pending tasks."
- **1 task**: "You have one task: Buy groceries."
- **2-5 tasks**: "You have 3 tasks: Task 1; Task 2; Task 3."
- **More than 5**: "You have 10 tasks: Task 1; Task 2; Task 3; Task 4; Task 5. And 5 more."

---

## 🧪 Test the Endpoints

### Your Replit URLs:

Replace `YOUR-REPL-URL` with your actual Replit app URL (e.g., `your-username-raas.replit.app`)

**Test JSON endpoint:**
```bash
curl 'https://YOUR-REPL-URL:8000/api/siri/tasks'
```

**Test spoken summary:**
```bash
curl 'https://YOUR-REPL-URL:8000/api/siri/say'
```

**Current test (localhost):**
```bash
# JSON
curl 'http://localhost:8000/api/siri/tasks'

# Spoken
curl 'http://localhost:8000/api/siri/say'
```

---

## 🔒 Optional: Add Security (Recommended)

To prevent unauthorized access to your reminders:

### 1. Generate a secure API key
```bash
# Use a random string, like:
raas_siri_d8f2b3c4e5a6f7g8h9i0
```

### 2. Add to Replit Secrets
- Click the **🔒 Secrets** icon in Replit's left sidebar
- Add a new secret:
  - **Key**: `SIRI_API_KEY`
  - **Value**: Your random string (e.g., `raas_siri_d8f2b3c4e5a6f7g8h9i0`)
- Click "Save"

### 3. Restart the API
The API will automatically require the key on all Siri endpoints.

### 4. Use with the key
```bash
# With key parameter
curl 'https://YOUR-REPL-URL:8000/api/siri/say?key=raas_siri_d8f2b3c4e5a6f7g8h9i0'
```

**Without the key**: Returns `401 Unauthorized`

---

## 📱 Set Up Siri Shortcut (iPhone/iPad)

### Step-by-Step Instructions:

#### 1. Open Shortcuts App
- Find the **Shortcuts** app on your iPhone
- Tap the **+** button to create a new shortcut

#### 2. Add "Get Contents of URL" Action
- Search for **"Get Contents of URL"**
- Add the action
- Configure:
  - **URL**: `https://YOUR-REPL-URL:8000/api/siri/say`
  - If using API key: `https://YOUR-REPL-URL:8000/api/siri/say?key=YOUR_API_KEY`
  - **Method**: GET
  - Leave other settings as default

#### 3. Add "Speak Text" Action
- Search for **"Speak Text"**
- Add the action below the URL action
- The input should automatically be the output from the previous action
- Configure:
  - **Text**: (automatically uses "Contents of URL")
  - **Rate**: Normal (or adjust to your preference)
  - **Language**: English (or your preference)

#### 4. Name Your Shortcut
- Tap the shortcut name at the top
- Rename to: **"Check RAAS"** or **"Check Reminders"**

#### 5. Add to Siri
- Tap the settings icon (⚙️) in the shortcut
- Tap **"Add to Siri"**
- Record your voice command, for example:
  - "Check my reminders"
  - "What are my tasks"
  - "RAAS status"
- Tap **"Done"**

---

## 🎤 Using Siri

Once set up, just say:

> **"Hey Siri, check my reminders"**

Siri will:
1. Fetch your pending tasks from RAAS
2. Read them aloud to you
3. Tell you how many more you have if there are more than 5

---

## 🛠️ Troubleshooting

### Siri says "There was a problem with the app"
- **Check your URL**: Make sure you're using the correct Replit URL
- **Check the API**: Open the URL in a browser to verify it works
- **Check the key**: If you set `SIRI_API_KEY`, make sure the key in the URL matches

### Siri reads JSON instead of a sentence
- You're probably using `/api/siri/tasks` instead of `/api/siri/say`
- Change the URL in your shortcut to `/api/siri/say`

### Getting 401 Unauthorized
- You set `SIRI_API_KEY` but forgot to add `?key=YOUR_KEY` to the URL
- Or the key in the URL doesn't match the secret

### No tasks are returned
- Make sure you have pending (not completed) tasks in RAAS
- Check the app to verify tasks exist

---

## 📚 API Documentation

Visit your API documentation to see all endpoints:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Look for the **"siri"** tag to see the Siri endpoints with full documentation and examples.

---

## 🌟 Advanced: Multiple Shortcuts

You can create different shortcuts for different purposes:

### "What's urgent?"
Filter by high priority tasks (requires custom endpoint modification)

### "What's due today?"
Filter by tasks due today (requires custom endpoint modification)

### "Mark as done"
Use Siri to complete tasks (would need a POST endpoint)

---

## 🚀 Example Workflow

1. Wake up in the morning
2. Say: **"Hey Siri, check my reminders"**
3. Siri responds: "You have 5 tasks: Finish project report; Call dentist; Buy groceries; Team meeting at 2 PM; Email client proposal."
4. You plan your day accordingly!

---

## 📝 Notes

- The Siri endpoints are **read-only** - they don't modify your tasks
- Endpoints return **pending tasks only** (not completed ones)
- The API respects your existing filters and categories
- Works with any voice assistant that can make HTTP GET requests

---

**Your RAAS app is now voice-enabled!** 🎉

Never miss what matters - even when you're hands-free! 🚀
