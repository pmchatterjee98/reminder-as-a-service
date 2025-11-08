import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import database
import api

TEST_DB = "test_api_todos.db"

@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database before each test."""
    original_db = database.DB_NAME
    database.DB_NAME = TEST_DB
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    database.init_db()
    
    yield
    
    database.DB_NAME = original_db
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(api.app)

class TestRootEndpoint:
    def test_root_returns_service_info(self, client):
        """Test root endpoint returns service information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "⚡ RAAS API"
        assert "tagline" in data
        assert "documentation" in data

class TestGetTodos:
    def test_get_todos_empty(self, client):
        """Test getting todos from empty database."""
        response = client.get("/todos")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_todos_multiple(self, client):
        """Test getting multiple todos."""
        database.add_todo("Task 1", "", "2025-12-01 10:00:00")
        database.add_todo("Task 2", "", "2025-12-02 10:00:00")
        database.add_todo("Task 3", "", "2025-12-03 10:00:00")
        
        response = client.get("/todos")
        assert response.status_code == 200
        
        todos = response.json()
        assert len(todos) == 3
        assert todos[0]['title'] == "Task 1"
    
    def test_get_todos_filter_by_category(self, client):
        """Test filtering todos by category."""
        database.add_todo("Work Task", "", "2025-12-01 10:00:00", category="Work")
        database.add_todo("Personal Task", "", "2025-12-02 10:00:00", category="Personal")
        
        response = client.get("/todos?category=Work")
        assert response.status_code == 200
        
        todos = response.json()
        assert len(todos) == 1
        assert todos[0]['category'] == "Work"
    
    def test_get_todos_filter_by_priority(self, client):
        """Test filtering todos by priority."""
        database.add_todo("High Priority", "", "2025-12-01 10:00:00", priority="High")
        database.add_todo("Low Priority", "", "2025-12-02 10:00:00", priority="Low")
        
        response = client.get("/todos?priority=High")
        assert response.status_code == 200
        
        todos = response.json()
        assert len(todos) == 1
        assert todos[0]['priority'] == "High"
    
    def test_get_todos_filter_by_completed(self, client):
        """Test filtering todos by completion status."""
        todo_id = database.add_todo("Task 1", "", "2025-12-01 10:00:00")
        database.add_todo("Task 2", "", "2025-12-02 10:00:00")
        database.toggle_complete(todo_id)
        
        response = client.get("/todos?completed=true")
        assert response.status_code == 200
        
        todos = response.json()
        assert len(todos) == 1
        assert todos[0]['completed'] == 1
    
    def test_get_todos_with_limit(self, client):
        """Test limiting number of todos returned."""
        for i in range(10):
            database.add_todo(f"Task {i}", "", "2025-12-01 10:00:00")
        
        response = client.get("/todos?limit=5")
        assert response.status_code == 200
        
        todos = response.json()
        assert len(todos) == 5

class TestGetTodoById:
    def test_get_todo_by_id_exists(self, client):
        """Test getting a specific todo by ID."""
        todo_id = database.add_todo("Test Task", "Description", "2025-12-01 10:00:00")
        
        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        
        todo = response.json()
        assert todo['id'] == todo_id
        assert todo['title'] == "Test Task"
    
    def test_get_todo_by_id_not_found(self, client):
        """Test getting a non-existent todo returns 404."""
        response = client.get("/todos/99999")
        assert response.status_code == 404
        assert "not found" in response.json()['detail'].lower()

class TestCreateTodo:
    def test_create_todo_minimal(self, client):
        """Test creating a todo with minimal fields."""
        todo_data = {
            "title": "New Task",
            "due_date": "2025-12-01 10:00:00"
        }
        
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 201
        
        todo = response.json()
        assert todo['title'] == "New Task"
        assert todo['id'] > 0
    
    def test_create_todo_full(self, client):
        """Test creating a todo with all fields."""
        todo_data = {
            "title": "Complete Task",
            "description": "Full description",
            "due_date": "2025-12-01 10:00:00",
            "email": "test@example.com",
            "phone": "+1234567890",
            "whatsapp_phone": "+1234567890",
            "reminder_hours": 48,
            "category": "Work",
            "priority": "High",
            "is_recurring": True,
            "recurrence_frequency": "weeks",
            "recurrence_interval": 2
        }
        
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 201
        
        todo = response.json()
        assert todo['title'] == "Complete Task"
        assert todo['priority'] == "High"
        assert todo['is_recurring'] is True
    
    def test_create_todo_invalid_data(self, client):
        """Test creating a todo with invalid data."""
        todo_data = {
            "title": "",
            "due_date": "invalid-date"
        }
        
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 422

class TestUpdateTodo:
    def test_update_todo_success(self, client):
        """Test updating a todo."""
        todo_id = database.add_todo("Original", "Desc", "2025-12-01 10:00:00")
        
        update_data = {
            "title": "Updated",
            "priority": "High"
        }
        
        response = client.put(f"/todos/{todo_id}", json=update_data)
        assert response.status_code == 200
        
        todo = response.json()
        assert todo['title'] == "Updated"
        assert todo['priority'] == "High"
    
    def test_update_todo_not_found(self, client):
        """Test updating a non-existent todo."""
        update_data = {
            "title": "Updated"
        }
        
        response = client.put("/todos/99999", json=update_data)
        assert response.status_code == 404
    
    def test_update_todo_completion_status(self, client):
        """Test updating completion status via PUT."""
        todo_id = database.add_todo("Task", "", "2025-12-01 10:00:00")
        
        update_data = {
            "completed": True
        }
        
        response = client.put(f"/todos/{todo_id}", json=update_data)
        assert response.status_code == 200
        
        todo = response.json()
        assert todo['completed'] is True

class TestDeleteTodo:
    def test_delete_todo_success(self, client):
        """Test deleting a todo."""
        todo_id = database.add_todo("Task to Delete", "", "2025-12-01 10:00:00")
        
        response = client.delete(f"/todos/{todo_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()['message']
        
        todo = database.get_todo_by_id(todo_id)
        assert todo is None
    
    def test_delete_todo_not_found(self, client):
        """Test deleting a non-existent todo."""
        response = client.delete("/todos/99999")
        assert response.status_code == 404

class TestToggleTodoComplete:
    def test_toggle_complete(self, client):
        """Test toggling todo completion status."""
        todo_id = database.add_todo("Task", "", "2025-12-01 10:00:00")
        
        response = client.post(f"/todos/{todo_id}/toggle-complete")
        assert response.status_code == 200
        
        todo = response.json()
        assert todo['completed'] is True
        
        response = client.post(f"/todos/{todo_id}/toggle-complete")
        todo = response.json()
        assert todo['completed'] is False
    
    def test_toggle_complete_not_found(self, client):
        """Test toggling completion for non-existent todo."""
        response = client.post("/todos/99999/toggle-complete")
        assert response.status_code == 404

class TestGetStats:
    def test_get_stats_empty(self, client):
        """Test stats with empty database."""
        response = client.get("/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert stats['total'] == 0
        assert stats['completed'] == 0
        assert stats['pending'] == 0
    
    def test_get_stats_with_todos(self, client):
        """Test stats with multiple todos."""
        database.add_todo("High Task", "", "2025-12-01 10:00:00", priority="High", category="Work")
        todo_id = database.add_todo("Med Task", "", "2025-12-02 10:00:00", priority="Medium")
        database.add_todo("Low Task", "", "2025-12-03 10:00:00", priority="Low", category="Personal")
        
        database.toggle_complete(todo_id)
        
        response = client.get("/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert stats['total'] == 3
        assert stats['completed'] == 1
        assert stats['pending'] == 2
        assert stats['high_priority'] == 1
        assert stats['medium_priority'] == 1
        assert stats['low_priority'] == 1
        assert stats['categories']['Work'] == 1
        assert stats['categories']['Personal'] == 1

class TestSiriEndpoints:
    def test_siri_tasks_endpoint(self, client):
        """Test Siri tasks JSON endpoint."""
        database.add_todo("Pending Task 1", "", "2025-12-01 10:00:00")
        database.add_todo("Pending Task 2", "", "2025-12-02 10:00:00")
        todo_id = database.add_todo("Done Task", "", "2025-12-03 10:00:00")
        database.toggle_complete(todo_id)
        
        response = client.get("/api/siri/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert data['total_pending'] == 2
        assert data['total_done'] == 1
        assert "Pending Task 1" in data['pending']
        assert "Done Task" in data['done']
    
    def test_siri_say_endpoint_no_tasks(self, client):
        """Test Siri say endpoint with no tasks."""
        response = client.get("/api/siri/say")
        assert response.status_code == 200
        assert "no pending tasks" in response.text.lower()
    
    def test_siri_say_endpoint_one_task(self, client):
        """Test Siri say endpoint with one task."""
        database.add_todo("Single Task", "", "2025-12-01 10:00:00")
        
        response = client.get("/api/siri/say")
        assert response.status_code == 200
        assert "one task" in response.text.lower()
        assert "Single Task" in response.text
    
    def test_siri_say_endpoint_multiple_tasks(self, client):
        """Test Siri say endpoint with multiple tasks."""
        for i in range(7):
            database.add_todo(f"Task {i+1}", "", "2025-12-01 10:00:00")
        
        response = client.get("/api/siri/say")
        assert response.status_code == 200
        assert "7 tasks" in response.text
        assert "And 2 more" in response.text
    
    @patch.dict(os.environ, {'SIRI_API_KEY': 'test_key_123'})
    def test_siri_endpoint_with_api_key_required(self, client):
        """Test Siri endpoint requires API key when set."""
        response = client.get("/api/siri/tasks")
        assert response.status_code == 401
        
        response = client.get("/api/siri/tasks?key=test_key_123")
        assert response.status_code == 200
    
    @patch.dict(os.environ, {'SIRI_API_KEY': 'test_key_123'})
    def test_siri_endpoint_with_wrong_api_key(self, client):
        """Test Siri endpoint rejects wrong API key."""
        response = client.get("/api/siri/say?key=wrong_key")
        assert response.status_code == 401
