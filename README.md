# AITaskRunner

A web-based automation platform for orchestrating and monitoring AI coding assistants (Claude Code, Codex CLI, Gemini CLI).

[English](README.md) | [中文](README_CN.md)

## Features

- **Task Management**: Create, edit, and track tasks with markdown support
- **Multi-CLI Support**: Works with Claude Code, OpenAI Codex CLI, and Google Gemini CLI
- **Multi-Project Parallel Execution**: Run multiple tasks simultaneously with configurable concurrency limits
- **Batch Operations**: Batch delete, status update, and start all pending tasks
- **Real-time Monitoring**: WebSocket-based live status updates
- **Session Watchdog**: Automatic session recovery when CLI unexpectedly terminates
- **Context Management**: Automatic session restart when context threshold is reached
- **Template System**: Reusable task templates with variable substitution and i18n support
- **Cross-Review**: Automatic code review using a different AI CLI after task completion
- **Project Organization**: Organize tasks by projects with one-click terminal launch
- **Terminal Integration**: Native support for iTerm2, Kitty, and Windows Terminal
- **Internationalization**: Full i18n support (English/Chinese)
- **Dark Mode**: Built-in dark/light theme support
- **Cross-Platform**: Works on macOS, Linux, and Windows

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI 0.109+
- SQLite (async with aiosqlite)
- WebSocket
- Pydantic 2.5+

**Frontend:**
- React 19
- TypeScript 5.9
- Vite 7
- Tailwind CSS 4
- Radix UI
- Zustand 5
- i18next

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- One of the supported AI CLI tools:
  - [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
  - [Codex CLI](https://github.com/openai/codex)
  - [Gemini CLI](https://github.com/google-gemini/gemini-cli)

### Installation

1. Clone the repository

```bash
git clone https://github.com/yourusername/AITaskRunner.git
cd AITaskRunner
```

2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### Running

**Development mode:**

```bash
# Terminal 1 - Backend
python start_web.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Then open http://localhost:3500 in your browser.

### 5-Minute Tutorial

Follow these steps to run your first automated task:

**Step 1: Configure Settings**

1. Open http://localhost:3500 and go to **Settings** page
2. Select your preferred **CLI Type** (e.g., Claude Code)
3. Select your **Terminal** (e.g., iTerm2 on macOS, Kitty on Linux)
4. Set **Max Concurrent Sessions** (default: 3)
5. Optionally enable **Cross-Review** for automatic code review

**Step 2: Create a Project**

1. Go to **Projects** page
2. Click **New Project**
3. Enter project name and select the project directory path
4. Use **Launch Terminal** button to quickly open a terminal in your project

**Step 3: Create a Task Document**

Create a markdown file in your project directory (e.g., `tasks/feature-login.md`):

```markdown
# Implement User Login Feature

## Tasks

- [ ] Create login form component with email and password fields
- [ ] Add form validation (email format, password length)
- [ ] Implement login API call
- [ ] Handle login success/failure states
- [ ] Add "Remember me" checkbox functionality
```

**Step 4: Create and Start a Task**

1. Go to **Tasks** page
2. Click **New Task**
3. Fill in:
   - **Title**: Implement User Login
   - **Project**: Select your project
   - **Document Path**: Path to your markdown file
4. Click **Save**, then click **Start**

**Step 5: Monitor Progress**

- The system opens a terminal window with the AI CLI
- Watch real-time progress in the **Sessions** page
- Check task logs for detailed execution history
- The AI will automatically check off completed items in your markdown file

**Pro Tips:**

- Use checkbox format (`- [ ]`) in markdown for trackable sub-tasks
- The system auto-restarts sessions when context limit is reached
- Enable **Cross-Review** to have a different AI review the completed work
- Use **Batch Start** to start all pending tasks at once
- The **Session Watchdog** automatically recovers terminated sessions

## Project Structure

```
AITaskRunner/
├── backend/                    # FastAPI backend
│   ├── app.py                 # Main application & API routes
│   ├── database/              # Database models (SQLite)
│   │   ├── models.py          # SQLAlchemy models
│   │   └── shared.py          # Shared database connection pool
│   ├── models/                # Pydantic schemas
│   │   └── schemas.py         # Request/Response models
│   ├── services/              # Business logic
│   │   ├── codex_service.py   # CLI session management
│   │   ├── task_service_db.py # Task CRUD operations
│   │   ├── template_service.py# Template management
│   │   ├── settings_service.py# Settings management
│   │   └── project_service.py # Project management
│   ├── utils/                 # Utility functions
│   │   └── markdown_checker.py# Task progress detection
│   └── tests/                 # Backend unit tests
├── frontend/                   # React frontend
│   └── src/
│       ├── pages/             # Page components
│       │   ├── Tasks.tsx      # Task management
│       │   ├── Sessions.tsx   # Session monitoring
│       │   ├── Projects.tsx   # Project management
│       │   ├── Templates.tsx  # Template editor
│       │   ├── Settings.tsx   # System settings
│       │   └── Logs.tsx       # Log viewer
│       ├── components/        # Reusable components
│       ├── stores/            # Zustand state management
│       ├── api/               # API client
│       ├── i18n/              # Internationalization
│       └── types/             # TypeScript types
├── core/                       # Core monitoring logic
│   ├── cli_adapters/          # CLI tool adapters
│   │   ├── base.py            # Base adapter interface
│   │   ├── claude_code.py     # Claude Code adapter
│   │   ├── codex.py           # Codex CLI adapter
│   │   └── gemini.py          # Gemini CLI adapter
│   ├── terminal_adapters/     # Terminal adapters
│   │   ├── base.py            # Base terminal interface
│   │   ├── iterm.py           # iTerm2 adapter (macOS)
│   │   ├── kitty.py           # Kitty adapter (macOS/Linux)
│   │   └── windows_terminal.py# Windows Terminal adapter
│   ├── session/               # Session pool management
│   │   ├── manager.py         # Session manager
│   │   ├── models.py          # Session models
│   │   └── watchdog.py        # Session watchdog
│   ├── cli_monitor.py         # CLI monitor
│   ├── context_manager.py     # Context tracking
│   └── task_manager.py        # Task execution manager
├── e2e/                        # End-to-end tests (Playwright)
└── start_web.py               # Application entry point
```

## Configuration

Settings can be configured via the web UI Settings page:

| Setting | Description | Options |
|---------|-------------|---------|
| CLI Type | Primary AI CLI to use | Claude Code, Codex, Gemini |
| Review CLI | CLI for cross-review | Claude Code, Codex, Gemini |
| Terminal | Terminal emulator | Auto, iTerm2, Kitty, Windows Terminal |
| Max Concurrent Sessions | Parallel task limit | 1-10 |
| Review Mode | Enable cross-review | On/Off |
| Watchdog | Auto-recover sessions | On/Off |
| Language | UI language | English, Chinese |

## Supported Terminals

| Terminal         | macOS | Linux | Windows |
|------------------|-------|-------|---------|
| Windows Terminal | -     | -     | Yes     |
| iTerm2           | Yes   | -     | -       |
| Kitty            | Yes   | Yes   | -       |

**Note:** Kitty terminal supports advanced features like idle detection for automatic session recovery.

## API Reference

The backend exposes a REST API at `http://localhost:8086`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/init` | GET | Get all initial data (tasks, sessions, projects, settings) |
| `/api/tasks` | GET/POST | List/Create tasks |
| `/api/tasks/{id}` | GET/PUT/DELETE | Get/Update/Delete task |
| `/api/tasks/{id}/start` | POST | Start task session |
| `/api/tasks/{id}/notify-status` | POST | CLI callback endpoint |
| `/api/tasks/batch/start` | POST | Start all pending tasks |
| `/api/tasks/batch/delete` | POST | Batch delete tasks |
| `/api/tasks/batch/status` | POST | Batch update status |
| `/api/sessions` | GET | List all sessions |
| `/api/projects` | GET/POST | List/Create projects |
| `/api/projects/{id}/launch` | POST | Launch terminal for project |
| `/api/templates` | GET/POST | List/Create templates |
| `/api/settings` | GET | Get all settings |
| `/api/settings/{key}` | GET/PUT | Get/Update setting |
| `/ws/monitor` | WebSocket | Real-time status updates |

## Troubleshooting

### Callback/Notification Connection Issues

- The callback URL defaults to `http://127.0.0.1:8086`. If you change the port, update `API_BASE_URL` in `.env` accordingly.
- If your machine has proxy/security software blocking local loopback, callbacks may fail. Ensure `127.0.0.1:8086` is accessible locally.
- After starting, run `curl http://127.0.0.1:8086/health` to verify connectivity.

### Session Not Starting

- Check if the selected CLI tool is installed and accessible in PATH
- Verify the terminal emulator is installed (iTerm2, Kitty, or Windows Terminal)
- Check the task logs for detailed error messages

### Session Watchdog

If sessions are being unexpectedly terminated and not recovering:
- Enable the watchdog in Settings
- Check that the terminal window wasn't manually closed
- Review the backend logs for watchdog messages

## Testing

```bash
# Backend unit tests
cd backend
pytest

# Frontend unit tests
cd frontend
npm run test

# E2E tests (requires running backend)
npm run e2e
```

## License

MIT License - see [LICENSE](LICENSE) for details.
