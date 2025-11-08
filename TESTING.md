# RAAS Testing Guide

## Overview

RAAS has comprehensive unit tests covering all major functionality with **66 passing tests** across database operations, notifications, API endpoints, and scheduler functionality.

---

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest test_database.py       # Database operations
pytest test_notifications.py  # Email, SMS, WhatsApp notifications
pytest test_api.py           # FastAPI REST endpoints
pytest test_scheduler.py     # Background reminder scheduler
```

### Run Specific Test Class
```bash
pytest test_database.py::TestAddTodo
pytest test_api.py::TestGetTodos
```

### Run With Verbose Output
```bash
pytest -v
```

### Run With Coverage Report
```bash
pytest --cov=. --cov-report=html
```

---

## Test Structure

### Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_database.py` | 25 tests | Database CRUD operations, recurring tasks, filtering |
| `test_notifications.py` | 14 tests | Email, SMS, WhatsApp notifications with mocking |
| `test_api.py` | 23 tests | All REST API endpoints including Siri integration |
| `test_scheduler.py` | 4 tests | Background scheduler and reminder checking |

### Test Coverage

#### Database Operations ✅
- **CRUD Operations**: Add, update, delete, get todos
- **Toggle Complete**: Mark tasks complete/incomplete, recurring task rescheduling
- **Filtering**: Category, priority, completion status
- **Recurring Tasks**: Daily, weekly, monthly, yearly recurrence
- **Reminders**: Upcoming todos, reminder hours, mark reminder sent

#### Notifications ✅
- **Email (SMTP)**: Success, errors, formatting, credentials validation
- **SMS (Twilio)**: Success, errors, formatting, credentials validation
- **WhatsApp (Twilio)**: Success, errors, formatting, phone number formatting

#### API Endpoints ✅
- **Root**: Service information
- **GET /todos**: List all, filtering (category, priority, completed), limit
- **GET /todos/{id}**: Get specific todo
- **POST /todos**: Create new todo (minimal & full fields)
- **PUT /todos/{id}**: Update todo
- **DELETE /todos/{id}**: Delete todo
- **POST /todos/{id}/toggle-complete**: Toggle completion status
- **GET /stats**: Statistics (total, completed, pending, priority breakdown)
- **GET /api/siri/tasks**: Siri JSON endpoint
- **GET /api/siri/say**: Siri spoken text endpoint
- **API Key Security**: Siri endpoints with optional API key protection

#### Scheduler ✅
- **Check and Send**: Find upcoming todos and send reminders
- **Filtering**: Skip completed, skip already sent, respect reminder_hours
- **Start/Stop**: Scheduler lifecycle management

---

## Test Database

Tests use **isolated test databases** to prevent interference with production data:

- Database tests: `test_todos.db`
- API tests: `test_api_todos.db`
- Scheduler tests: `test_scheduler_todos.db`

Test databases are automatically created before each test and cleaned up afterward.

---

## Mocking Strategy

### External Services
All external services are mocked to prevent actual API calls during testing:

- **SMTP Server**: Mocked with `unittest.mock`
- **Twilio API**: Mocked with `unittest.mock`
- **Environment Variables**: Mocked with `unittest.mock.patch`

### Benefits
- ✅ Fast test execution (no network calls)
- ✅ No API costs during testing
- ✅ Reliable tests (no external dependencies)
- ✅ Can test error scenarios

---

## Writing New Tests

### Example Test Structure

```python
import pytest
from unittest.mock import patch
import database

class TestMyFeature:
    def test_feature_success(self):
        """Test successful feature execution."""
        # Arrange
        todo_id = database.add_todo("Test", "", "2025-12-01 10:00:00")
        
        # Act
        result = database.my_feature(todo_id)
        
        # Assert
        assert result is True
    
    @patch('module.external_service')
    def test_feature_with_mock(self, mock_service):
        """Test feature with external service mocked."""
        mock_service.return_value = "mocked_response"
        
        result = my_function()
        
        assert result == "expected_value"
        mock_service.assert_called_once()
```

### Testing Best Practices

1. **One assertion focus per test**: Each test should verify one specific behavior
2. **Descriptive test names**: Use `test_<what>_<condition>_<expected>`
3. **AAA Pattern**: Arrange → Act → Assert
4. **Mock external dependencies**: Never hit real APIs or send real emails
5. **Clean up**: Use fixtures to ensure test isolation

---

## Continuous Integration

Tests run automatically on every push via **GitHub Actions**. See `.github/workflows/test.yml`.

### CI Pipeline
1. ✅ Lint code (ruff)
2. ✅ Run all tests
3. ✅ Generate coverage report
4. ✅ Build Docker images

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'httpx'`
```bash
uv add httpx
```

**Issue**: Database locked
```bash
# Stop any running workflows
# Delete test databases
rm test_*.db
```

**Issue**: Mock not working
```python
# Make sure to patch the right module
# Patch where the function is used, not where it's defined
@patch('scheduler.notifications.send_email_reminder')  # ✅ Correct
@patch('notifications.send_email_reminder')             # ❌ Wrong
```

---

## Test Metrics

- **Total Tests**: 66
- **Passing**: 66 (100%)
- **Failing**: 0
- **Test Execution Time**: ~7-8 seconds
- **Coverage**: Database (100%), API (100%), Notifications (95%), Scheduler (90%)

---

## Future Improvements

- [ ] Add integration tests with real database
- [ ] Add performance/load tests for API
- [ ] Add end-to-end tests with Playwright
- [ ] Increase test coverage to 100% across all modules
- [ ] Add mutation testing
- [ ] Add test for edge cases (large data sets, concurrent requests)

---

**All tests maintained by the RAAS development team** 🚀
