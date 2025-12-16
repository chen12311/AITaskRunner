# Quick Start Guide

[English](QUICK_START_EN.md) | [中文](QUICK_START.md)

## 5-Minute Quick Start

### Step 1: Install Dependencies

**Backend dependencies:**
```bash
pip install -r backend/requirements.txt
```

**Frontend dependencies:**
```bash
cd frontend
npm install
cd ..
```

### Step 2: Start Services

**Start backend:**
```bash
python start_web.py
```

**Start frontend (new terminal):**
```bash
cd frontend
npm run dev
```

### Step 3: Access the System

Open your browser and navigate to: `http://localhost:3500`

## Create Your First Task

### Method 1: Using Web Interface

1. Go to **Settings** page, configure:
   - CLI Type (Claude Code / Codex / Gemini)
   - Terminal Type (iTerm2 / Kitty / Windows Terminal)
   - Max Concurrent Sessions

2. Go to **Projects** page, create a new project:
   - Enter project name
   - Select project directory path
   - Use **Launch Terminal** to quickly open the project directory

3. Go to **Tasks** page, create a task:
   - Enter task title
   - Select associated project
   - Specify Markdown document path
   - Click **Save** then click **Start**

### Method 2: Using API

```python
import requests

# Create task
response = requests.post('http://localhost:8086/api/tasks', json={
    "title": "My First Task",
    "project_directory": "/path/to/my_project",
    "markdown_document_path": "/path/to/my_project/tasks/task.md"
})
task = response.json()

# Start task
requests.post(f'http://localhost:8086/api/tasks/{task["id"]}/start')
```

## Markdown Document Format

Task documents use Markdown format. The system automatically recognizes checkboxes and tracks progress:

```markdown
# Project Title

## Project Overview
Brief description of the project goals and background

## Tech Stack
- **Language**: Python
- **Framework**: FastAPI
- **Database**: PostgreSQL

## Task List

### 1. Project Initialization
- [ ] Create project directory structure
- [ ] Configure development environment
- [ ] Initialize Git repository

### 2. Core Feature Development
- [ ] Implement user authentication
- [ ] Develop API endpoints
- [ ] Database design

### 3. Testing and Deployment
- [ ] Write unit tests
- [ ] Configure CI/CD
- [ ] Deploy to production

## Implementation Notes
Detailed implementation requirements and considerations...
```

**Note:** Use `- [ ]` checkbox format for automatic task completion detection.

## Common Operations

### Batch Operations

The Tasks page supports batch operations:
- **Batch Start**: Start all pending tasks with one click
- **Batch Delete**: Delete multiple selected tasks
- **Batch Status Update**: Update status for multiple tasks

### Project Terminal

On the Projects page you can:
- **Launch Terminal**: Open a terminal in the project directory
- **Launch CLI**: Directly start the AI CLI tool
- **Dangerous Mode**: Start CLI with auto-confirm parameters

### View Logs

All logs during task execution can be viewed in:
- Task detail page
- Logs page for all task logs

## Core Features

### Session Watchdog

Automatically detects and recovers unexpectedly terminated sessions:
- Auto-restart when terminal window is accidentally closed
- Kitty terminal supports CLI idle detection
- Can be enabled/disabled in Settings page

### Cross-Review

Use a different AI CLI for cross-review:
- Automatically switches to review CLI after task completion
- Supports both task-level and global-level toggle
- Configure review CLI type in Settings page

### Context Management

When CLI context reaches threshold:
- Automatically restarts session to continue execution
- Uses `resume_task` template to restore progress
- No manual intervention required

## Troubleshooting

### Q1: Backend fails to start?

Check if port is occupied:
```bash
lsof -i :8086
```

Ensure Python 3.10+ is installed:
```bash
python --version
```

### Q2: Frontend cannot connect to backend?

Ensure backend service is running, check `API_BASE_URL` configuration in `.env` file.

### Q3: CLI session won't start?

1. Confirm the selected CLI tool is installed (claude / codex / gemini)
2. Confirm terminal emulator is installed (iTerm2 / Kitty)
3. Check task logs for detailed error messages

### Q4: Task progress not updating?

1. Ensure Markdown document uses correct checkbox format `- [ ]`
2. Check if callback URL is correctly configured
3. Run `curl http://127.0.0.1:8086/health` to test connection

### Q5: How to view more logs?

Backend logs are output directly to the terminal where `start_web.py` was started.

## API Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/init` | GET | Get initialization data |
| `/api/tasks` | GET/POST | List/Create tasks |
| `/api/tasks/{id}/start` | POST | Start task |
| `/api/tasks/batch/start` | POST | Batch start |
| `/api/sessions` | GET | Get session list |
| `/api/projects` | GET/POST | List/Create projects |
| `/api/projects/{id}/launch` | POST | Launch project terminal |
| `/api/settings` | GET | Get settings |
| `/ws/monitor` | WebSocket | Real-time status updates |

## More Resources

- [Full Documentation](README.md)
- [API Documentation](http://localhost:8086/docs) - Access after starting backend

---

**Tip**: We recommend starting with a small test project to familiarize yourself with the system before using it for actual development tasks.
