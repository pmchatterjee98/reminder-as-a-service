"""
AI Intelligence Module for RAAS
Provides natural language task creation, auto-categorization, smart scheduling, and productivity insights
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from openai import OpenAI

# Initialize OpenAI client
# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def parse_natural_language_task(user_input: str, current_categories: List[str] = None) -> Dict:
    """
    Parse natural language input into a structured task.
    
    Args:
        user_input: Natural language description of the task
        current_categories: List of existing categories for context
        
    Returns:
        Dictionary with task details (title, description, due_date, category, priority)
    """
    try:
        categories_context = ""
        if current_categories:
            categories_context = f"\nExisting categories: {', '.join(current_categories)}"
        
        prompt = f"""You are a smart task management assistant. Parse the following natural language input into a structured task.

User input: "{user_input}"{categories_context}

Extract and infer the following information:
1. Title: A clear, concise task title (max 50 characters)
2. Description: Additional details if provided, otherwise leave empty
3. Due date: Parse any time references (e.g., "tomorrow", "next week", "in 3 days", "Friday at 2pm")
   - Today is {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}
   - If no time specified, use 5:00 PM
   - If date mentioned without time, use that date at 5:00 PM
   - Return in format: YYYY-MM-DD HH:MM:SS
4. Category: Infer from context (Work, Personal, Shopping, Health, Finance, etc.)
   - Prefer existing categories if they match
   - If unclear, use "Personal" as default
5. Priority: Infer from urgency cues (High, Medium, Low)
   - Words like "urgent", "ASAP", "critical" → High
   - Words like "important", "soon" → Medium
   - Default → Low
6. Reminder hours: How many hours before due date to send reminder (default: 24)
   - For urgent tasks → 2-4 hours
   - For normal tasks → 24 hours
   - For long-term tasks → 48-72 hours

Respond ONLY with valid JSON in this exact format:
{{
  "title": "Task title here",
  "description": "Optional description",
  "due_date": "YYYY-MM-DD HH:MM:SS",
  "category": "Category name",
  "priority": "High|Medium|Low",
  "reminder_hours": 24
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a smart task parsing assistant. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=500
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        # Fallback: Create a simple task with the input as title
        return {
            "title": user_input[:100],
            "description": "",
            "due_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            "category": "Personal",
            "priority": "Medium",
            "reminder_hours": 24
        }


def auto_categorize_task(title: str, description: str, existing_categories: List[str]) -> str:
    """
    Automatically categorize a task based on its content.
    
    Args:
        title: Task title
        description: Task description
        existing_categories: List of existing categories in the system
        
    Returns:
        Category name (from existing categories or a new one)
    """
    try:
        categories_list = ', '.join(existing_categories) if existing_categories else "Work, Personal, Shopping, Health, Finance"
        
        prompt = f"""Categorize this task based on its content.

Task Title: {title}
Task Description: {description}

Existing categories: {categories_list}

Choose the most appropriate category from the existing ones, or suggest a new category if none fit well.
Respond with ONLY the category name in JSON format.

Example response: {{"category": "Work"}}"""

        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a task categorization expert. Respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=100
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('category', 'Personal')
        
    except Exception as e:
        return 'Personal'


def suggest_smart_schedule(title: str, description: str, priority: str) -> Tuple[str, int]:
    """
    Suggest optimal due date and reminder time based on task content.
    
    Args:
        title: Task title
        description: Task description
        priority: Task priority
        
    Returns:
        Tuple of (due_date string, reminder_hours)
    """
    try:
        prompt = f"""You are a smart scheduling assistant. Suggest an optimal due date and reminder time for this task.

Task Title: {title}
Task Description: {description}
Priority: {priority}

Current date/time: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}

Consider:
1. Task urgency and priority
2. Typical time needed for such tasks
3. Business hours (9 AM - 6 PM on weekdays preferred)
4. Reasonable deadlines based on task type

Respond with JSON:
{{
  "due_date": "YYYY-MM-DD HH:MM:SS",
  "reminder_hours": 24,
  "reasoning": "Brief explanation of why this schedule makes sense"
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a smart scheduling expert. Respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=300
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('due_date'), result.get('reminder_hours', 24)
        
    except Exception as e:
        # Default: tomorrow at 5 PM, 24 hour reminder
        due_date = (datetime.now() + timedelta(days=1)).replace(hour=17, minute=0, second=0)
        return due_date.strftime('%Y-%m-%d %H:%M:%S'), 24


def generate_productivity_insights(tasks: List[Dict]) -> Dict:
    """
    Analyze tasks and generate productivity insights.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        Dictionary with insights and recommendations
    """
    try:
        if not tasks:
            return {
                "summary": "No tasks to analyze yet. Start adding tasks to get personalized insights!",
                "recommendations": [],
                "patterns": []
            }
        
        # Prepare task summary for AI
        task_summary = []
        for task in tasks[:20]:  # Limit to 20 most recent tasks
            task_summary.append({
                "title": task.get('title', ''),
                "category": task.get('category', ''),
                "priority": task.get('priority', ''),
                "completed": task.get('completed', False),
                "due_date": task.get('due_date', '')
            })
        
        prompt = f"""You are a productivity coach analyzing a user's task management patterns.

Here are their recent tasks:
{json.dumps(task_summary, indent=2)}

Analyze and provide:
1. A brief summary of their task management patterns
2. 3-5 actionable recommendations to improve productivity
3. Any patterns you notice (procrastination, category clustering, priority distribution, etc.)

Respond with JSON:
{{
  "summary": "Brief overview of their task patterns",
  "recommendations": ["Recommendation 1", "Recommendation 2", ...],
  "patterns": ["Pattern 1", "Pattern 2", ...]
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a helpful productivity coach. Respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=800
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        return {
            "summary": "Unable to generate insights at this time.",
            "recommendations": ["Keep adding tasks to track your productivity"],
            "patterns": []
        }


def chat_with_assistant(user_message: str, tasks_context: List[Dict] = None) -> str:
    """
    Chat with AI assistant about tasks and productivity.
    
    Args:
        user_message: User's question or request
        tasks_context: Optional list of tasks for context
        
    Returns:
        AI assistant's response
    """
    try:
        context = ""
        if tasks_context:
            # Summarize tasks for context
            pending = len([t for t in tasks_context if not t.get('completed')])
            completed = len([t for t in tasks_context if t.get('completed')])
            categories = list(set([t.get('category', '') for t in tasks_context if t.get('category')]))
            
            context = f"\n\nCurrent task overview:\n- Pending tasks: {pending}\n- Completed tasks: {completed}\n- Categories: {', '.join(categories)}"
        
        prompt = f"""You are RAAS AI, a helpful task management and productivity assistant. You help users manage their tasks, stay organized, and be more productive.

User question: {user_message}{context}

Provide a helpful, friendly, and concise response. Be encouraging and practical."""

        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are RAAS AI, a friendly and helpful task management assistant."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return "I'm having trouble connecting right now. Please try again in a moment."
