"""
RAAS API - Reminder as a Service REST API
Provides RESTful endpoints with automatic Swagger/OpenAPI documentation
"""

from fastapi import FastAPI, HTTPException, Query, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import database
import database_multi_user
import database_auth
import os

# Initialize FastAPI app with metadata for Swagger
app = FastAPI(
    title="⚡ RAAS API",
    description="""
    ## Reminder as a Service API
    
    **Never miss what matters** - Comprehensive REST API for managing reminders and tasks.
    
    ### Features
    * **Task Management**: Create, read, update, and delete reminders
    * **Smart Filtering**: Filter by category, priority, and completion status
    * **Recurring Tasks**: Support for daily, weekly, monthly, and yearly recurrence
    * **Priority Levels**: High, Medium, and Low priorities with color-coded indicators
    * **Customizable Reminders**: Set reminder intervals from 1 hour to 7 days before due date
    
    ### Endpoints
    * **GET /todos**: List all todos with optional filtering
    * **GET /todos/{id}**: Get a specific todo by ID
    * **POST /todos**: Create a new todo
    * **PUT /todos/{id}**: Update an existing todo
    * **DELETE /todos/{id}**: Delete a todo
    * **POST /todos/{id}/complete**: Mark a todo as complete
    * **POST /todos/{id}/uncomplete**: Mark a todo as incomplete
    * **GET /stats**: Get statistics about your todos
    """,
    version="1.0.0",
    contact={
        "name": "RAAS Support",
        "url": "https://github.com/yourusername/raas",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "todos",
            "description": "Operations with todos/reminders",
        },
        {
            "name": "statistics",
            "description": "Analytics and statistics",
        },
    ]
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
database.init_db()
database_auth.init_auth_db()

# --- Authentication Helpers ---

# API Key for securing the REST API (MANDATORY - prevents header spoofing)
API_AUTH_KEY = os.getenv("RAAS_API_KEY")

# Production security: Require API key for all authenticated endpoints
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "true").lower() == "true"

def verify_api_auth(request: Request, api_key: Optional[str] = Query(None, alias="api_key")) -> bool:
    """
    Verify API authentication key to prevent unauthorized access.
    
    MANDATORY AUTHENTICATION:
    - RAAS_API_KEY environment variable MUST be set in production
    - All API requests MUST include the key as a query parameter: ?api_key=YOUR_KEY
    - This prevents header spoofing and ensures secure multi-user isolation
    
    DEVELOPMENT MODE:
    - Set REQUIRE_API_KEY=false to disable (for local testing only)
    - NEVER disable in production - exposes critical security vulnerability
    
    Raises:
        HTTPException: If API key is invalid or missing
    """
    # In production mode (default), API key is REQUIRED
    if REQUIRE_API_KEY:
        if not API_AUTH_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API not configured: RAAS_API_KEY environment variable must be set. See documentation for setup instructions."
            )
        if not api_key or api_key != API_AUTH_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key. Include ?api_key=YOUR_KEY in the request URL."
            )
    return True

def get_current_user(request: Request, api_authenticated: bool = Depends(verify_api_auth)) -> str:
    """
    Extract and validate user from Replit Auth headers.
    
    SECURITY MODEL:
    - API Key Protection: Set RAAS_API_KEY environment variable to require API key
      authentication for all API requests. This prevents header spoofing attacks.
    
    - Header Validation: Reads X-Replit-User-Id and X-Replit-User-Name headers.
      Both headers must be present for consistency.
    
    - Database Verification: Ensures user exists in database (completed onboarding).
    
    PRODUCTION DEPLOYMENT:
    1. ALWAYS set RAAS_API_KEY to a secure random value
    2. Use HTTPS only (handled by Replit automatically)
    3. Consider adding rate limiting for additional security
    
    Returns:
        user_id: The authenticated user's internal RAAS ID (not auth_provider_id)
        
    Raises:
        HTTPException: If user is not authenticated
    """
    auth_provider_id = request.headers.get("X-Replit-User-Id")
    user_name = request.headers.get("X-Replit-User-Name")
    
    # Require both headers for consistency (prevents partial spoofing)
    if not auth_provider_id or not user_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Replit Auth headers.",
            headers={"WWW-Authenticate": "Replit-Auth"}
        )
    
    # Verify user exists in database (prevents access before onboarding)
    user = database_auth.get_user_by_auth_id(auth_provider_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found. Please complete onboarding in the Streamlit app first."
        )
    
    # CRITICAL: Return internal RAAS user ID, not auth_provider_id
    # Todos are stored with user['id'] (internal UUID), not auth_provider_id
    return user['id']

# Pydantic Models for request/response validation

class TodoBase(BaseModel):
    """Base todo model with common fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Title of the todo", example="Team Meeting")
    description: Optional[str] = Field(None, max_length=1000, description="Detailed description", example="Discuss Q1 goals and project timeline")
    due_date: str = Field(..., description="Due date in ISO format (YYYY-MM-DD HH:MM:SS)", example="2025-11-15 14:30:00")
    email: Optional[str] = Field(None, description="Email for notifications", example="user@example.com")
    phone: Optional[str] = Field(None, description="Phone number for SMS notifications", example="+1234567890")
    whatsapp_phone: Optional[str] = Field(None, description="WhatsApp phone number for notifications", example="+1234567890")
    reminder_hours: int = Field(24, ge=1, le=168, description="Hours before due date to send reminder (1-168)", example=24)
    category: Optional[str] = Field(None, max_length=50, description="Category for organization", example="Work")
    priority: str = Field("Medium", description="Priority level: High, Medium, or Low", example="High")
    is_recurring: bool = Field(False, description="Whether this is a recurring task")
    recurrence_frequency: Optional[str] = Field(None, description="Recurrence frequency: days, weeks, months, years", example="weeks")
    recurrence_interval: Optional[int] = Field(None, ge=1, description="Interval for recurrence", example=2)

class TodoCreate(TodoBase):
    """Model for creating a new todo"""
    pass

class TodoUpdate(BaseModel):
    """Model for updating a todo (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    due_date: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    reminder_hours: Optional[int] = Field(None, ge=1, le=168)
    category: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_frequency: Optional[str] = None
    recurrence_interval: Optional[int] = Field(None, ge=1)
    completed: Optional[bool] = None

class Todo(TodoBase):
    """Complete todo model with all fields"""
    id: int = Field(..., description="Unique identifier")
    completed: bool = Field(False, description="Completion status")
    reminder_sent: bool = Field(False, description="Whether reminder was sent")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True

class TodoStats(BaseModel):
    """Statistics about todos"""
    total: int
    completed: int
    pending: int
    overdue: int
    high_priority: int
    medium_priority: int
    low_priority: int
    categories: dict

class Message(BaseModel):
    """Generic message response"""
    message: str

# API Endpoints

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - API information (public endpoint, no auth required)
    """
    # Security status check
    if REQUIRE_API_KEY and not API_AUTH_KEY:
        security_status = "🔒 SETUP REQUIRED: Set RAAS_API_KEY environment variable"
    elif REQUIRE_API_KEY and API_AUTH_KEY:
        security_status = "🔒 Protected with API key (secure multi-user mode)"
    else:
        security_status = "⚠️  WARNING: Development mode - API key not required (UNSAFE for production)"
    
    return {
        "service": "⚡ RAAS API",
        "tagline": "Reminder as a Service — Never miss what matters",
        "version": "1.0.0",
        "security": security_status,
        "auth_required": REQUIRE_API_KEY,
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "todos": "/todos",
            "stats": "/stats"
        }
    }

@app.get("/todos", response_model=List[Todo], tags=["todos"])
async def get_todos(
    user_id: str = Depends(get_current_user),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority (High/Medium/Low)"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
):
    """
    Get all todos for the authenticated user with optional filtering
    
    - **category**: Filter by category name
    - **priority**: Filter by priority level (High, Medium, Low)
    - **completed**: Filter by completion status (true/false)
    - **limit**: Maximum number of results to return
    """
    todos = database_multi_user.get_todos_for_user(user_id)
    
    # Apply filters
    if category:
        todos = [t for t in todos if t.get('category') == category]
    if priority:
        todos = [t for t in todos if t.get('priority') == priority]
    if completed is not None:
        todos = [t for t in todos if bool(t.get('completed')) == completed]
    if limit:
        todos = todos[:limit]
    
    return todos

@app.get("/todos/{todo_id}", response_model=Todo, tags=["todos"])
async def get_todo(todo_id: int, user_id: str = Depends(get_current_user)):
    """
    Get a specific todo by ID (must belong to authenticated user)
    
    - **todo_id**: The ID of the todo to retrieve
    """
    todo = database_multi_user.get_todo_by_id_for_user(todo_id, user_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found or access denied")
    return todo

@app.post("/todos", response_model=Todo, status_code=201, tags=["todos"])
async def create_todo(todo: TodoCreate, user_id: str = Depends(get_current_user)):
    """
    Create a new todo for the authenticated user
    
    Provide all required fields to create a new reminder. The system will automatically
    send notifications based on the reminder_hours setting.
    """
    try:
        todo_id = database_multi_user.add_todo_for_user(
            user_id=user_id,
            title=todo.title,
            description=todo.description or "",
            due_date=todo.due_date,
            email=todo.email or "",
            phone=todo.phone or "",
            whatsapp_phone=todo.whatsapp_phone or "",
            reminder_hours=todo.reminder_hours,
            is_recurring=todo.is_recurring,
            recurrence_frequency=todo.recurrence_frequency,
            recurrence_interval=todo.recurrence_interval,
            category=todo.category,
            priority=todo.priority
        )
        created_todo = database_multi_user.get_todo_by_id_for_user(todo_id, user_id)
        return created_todo
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/todos/{todo_id}", response_model=Todo, tags=["todos"])
async def update_todo(todo_id: int, todo_update: TodoUpdate, user_id: str = Depends(get_current_user)):
    """
    Update an existing todo (must belong to authenticated user)
    
    - **todo_id**: The ID of the todo to update
    
    Only provide the fields you want to update. All fields are optional.
    """
    existing_todo = database_multi_user.get_todo_by_id_for_user(todo_id, user_id)
    if not existing_todo:
        raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found or access denied")
    
    # Prepare update data
    update_data = todo_update.model_dump(exclude_unset=True)
    
    # Merge with existing data
    merged_data = {**existing_todo, **update_data}
    
    try:
        database_multi_user.update_todo_for_user(
            user_id=user_id,
            todo_id=todo_id,
            title=merged_data['title'],
            description=merged_data['description'] or "",
            due_date=merged_data['due_date'],
            email=merged_data['email'] or "",
            phone=merged_data['phone'] or "",
            whatsapp_phone=merged_data.get('whatsapp_phone') or "",
            reminder_hours=merged_data['reminder_hours'],
            is_recurring=bool(merged_data['is_recurring']),
            recurrence_frequency=merged_data.get('recurrence_frequency'),
            recurrence_interval=merged_data.get('recurrence_interval'),
            category=merged_data.get('category'),
            priority=merged_data['priority']
        )
        
        # Update completion status if provided
        if 'completed' in update_data:
            # Toggle to match desired state
            current_completed = bool(existing_todo['completed'])
            desired_completed = bool(update_data['completed'])
            if current_completed != desired_completed:
                database_multi_user.toggle_complete_for_user(todo_id, user_id)
        
        updated_todo = database_multi_user.get_todo_by_id_for_user(todo_id, user_id)
        return updated_todo
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/todos/{todo_id}", response_model=Message, tags=["todos"])
async def delete_todo(todo_id: int, user_id: str = Depends(get_current_user)):
    """
    Delete a todo (must belong to authenticated user)
    
    - **todo_id**: The ID of the todo to delete
    
    This action is permanent and cannot be undone.
    """
    existing_todo = database_multi_user.get_todo_by_id_for_user(todo_id, user_id)
    if not existing_todo:
        raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found or access denied")
    
    database_multi_user.delete_todo_for_user(todo_id, user_id)
    return {"message": f"Todo {todo_id} deleted successfully"}

@app.post("/todos/{todo_id}/toggle-complete", response_model=Todo, tags=["todos"])
async def toggle_todo_complete(todo_id: int, user_id: str = Depends(get_current_user)):
    """
    Toggle the completion status of a todo (must belong to authenticated user)
    
    - **todo_id**: The ID of the todo to toggle
    
    If the todo is complete, it will be marked as incomplete.
    If the todo is incomplete, it will be marked as complete.
    """
    existing_todo = database_multi_user.get_todo_by_id_for_user(todo_id, user_id)
    if not existing_todo:
        raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found or access denied")
    
    database_multi_user.toggle_complete_for_user(todo_id, user_id)
    updated_todo = database_multi_user.get_todo_by_id_for_user(todo_id, user_id)
    return updated_todo

@app.get("/stats", response_model=TodoStats, tags=["statistics"])
async def get_stats(user_id: str = Depends(get_current_user)):
    """
    Get statistics about the authenticated user's todos
    
    Returns counts for total, completed, pending, overdue, and priority breakdowns.
    """
    stats = database_multi_user.get_user_statistics(user_id)
    
    return {
        "total": stats['total'],
        "completed": stats['completed'],
        "pending": stats['pending'],
        "overdue": stats['overdue'],
        "high_priority": stats['high_priority'],
        "medium_priority": stats['medium_priority'],
        "low_priority": stats['low_priority'],
        "categories": stats['categories']
    }

# --- Siri / Voice Assistant Integration ---

# Optional API key for securing Siri endpoints
API_KEY = os.getenv("SIRI_API_KEY")

def verify_api_key(key: Optional[str] = Query(None, description="API key for authentication")):
    """
    Verify API key if SIRI_API_KEY environment variable is set.
    If not set, endpoints are publicly accessible.
    """
    if API_KEY and key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return True

class SiriTasksResponse(BaseModel):
    """Response model for Siri tasks endpoint"""
    pending: List[str] = Field(..., description="List of pending task titles")
    done: List[str] = Field(..., description="List of completed task titles")
    total_pending: int = Field(..., description="Total number of pending tasks")
    total_done: int = Field(..., description="Total number of completed tasks")

@app.get("/api/siri/tasks", response_model=SiriTasksResponse, tags=["siri"])
async def siri_get_tasks(
    user_id: str = Depends(get_current_user),
    authorized: bool = Depends(verify_api_key)
):
    """
    Get tasks for Siri/voice assistants in simplified JSON format
    
    Returns pending and completed tasks for the authenticated user as simple string lists,
    perfect for voice assistant integrations.
    
    **Security**: 
    - Requires Replit Auth headers (X-Replit-User-Id)
    - If SIRI_API_KEY environment variable is set, you must also provide
      the key as a query parameter: `?key=YOUR_KEY`
    
    **Example**:
    ```
    curl -H "X-Replit-User-Id: YOUR_USER_ID" \
         'https://your-app.replit.app/api/siri/tasks?key=YOUR_KEY'
    ```
    """
    todos = database_multi_user.get_todos_for_user(user_id)
    
    pending = [t['title'] for t in todos if not t.get('completed')]
    done = [t['title'] for t in todos if t.get('completed')]
    
    return {
        "pending": pending,
        "done": done,
        "total_pending": len(pending),
        "total_done": len(done)
    }

@app.get("/api/siri/say", response_class=PlainTextResponse, tags=["siri"])
async def siri_say_tasks(
    user_id: str = Depends(get_current_user),
    authorized: bool = Depends(verify_api_key)
):
    """
    Get a spoken summary of pending tasks for Siri/voice assistants
    
    Returns a human-readable plain text sentence that Siri can speak aloud for the authenticated user.
    
    **Rules**:
    - No pending tasks → "You have no pending tasks."
    - 1 task → "You have one task: Task Name."
    - 2-5 tasks → "You have N tasks: task1; task2; task3."
    - More than 5 tasks → Lists first 5, then "And M more."
    
    **Security**: 
    - Requires Replit Auth headers (X-Replit-User-Id)
    - If SIRI_API_KEY environment variable is set, you must also provide
      the key as a query parameter: `?key=YOUR_KEY`
    
    **Example**:
    ```
    curl -H "X-Replit-User-Id: YOUR_USER_ID" \
         'https://your-app.replit.app/api/siri/say?key=YOUR_KEY'
    ```
    
    **Siri Shortcut Setup**:
    1. Open Shortcuts app → Create new shortcut
    2. Add "Get Contents of URL" action with this endpoint
    3. Add custom headers: X-Replit-User-Id with your user ID
    4. Add "Speak Text" action using the response
    5. Add to Siri with phrase "Check my reminders"
    """
    todos = database_multi_user.get_todos_for_user(user_id)
    pending = [t['title'] for t in todos if not t.get('completed')]
    
    if not pending:
        return "You have no pending tasks."
    elif len(pending) == 1:
        return f"You have one task: {pending[0]}."
    else:
        # Show first 5 tasks
        first_five = pending[:5]
        remainder = len(pending) - len(first_five)
        
        task_list = "; ".join(first_five)
        response = f"You have {len(pending)} tasks: {task_list}."
        
        if remainder > 0:
            response += f" And {remainder} more."
        
        return response

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("⚡ RAAS API - Siri Integration Enabled")
    print("="*50)
    print("\n📱 Siri Endpoints:")
    print("  JSON: GET /api/siri/tasks")
    print("  SAY:  GET /api/siri/say")
    
    if API_KEY:
        print(f"\n🔒 Security: API Key required (add ?key=YOUR_KEY)")
        print(f"   Set via SIRI_API_KEY environment variable")
    else:
        print("\n🌐 Security: Public access (no API key required)")
        print("   Set SIRI_API_KEY environment variable to enable authentication")
    
    print("\n🧪 Test with curl:")
    if API_KEY:
        print("  curl 'http://localhost:8000/api/siri/tasks?key=YOUR_KEY'")
        print("  curl 'http://localhost:8000/api/siri/say?key=YOUR_KEY'")
    else:
        print("  curl 'http://localhost:8000/api/siri/tasks'")
        print("  curl 'http://localhost:8000/api/siri/say'")
    
    print("\n📚 Documentation: http://localhost:8000/docs")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
