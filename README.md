# AITaskRunner

A web-based automation platform for orchestrating and monitoring AI coding assistants (Claude Code, Codex CLI, Gemini CLI).

[English](README.md) | [中文](README_CN.md)

## Features

- **Task Management**: Create, edit, and track tasks with markdown support
- **Multi-CLI Support**: Works with Claude Code, OpenAI Codex CLI, and Google Gemini CLI
- **Multi-Project Parallel Execution**: Run multiple tasks simultaneously with configurable concurrency limits
- **Real-time Monitoring**: WebSocket-based live status updates
- **Context Management**: Automatic session restart when context threshold is reached
- **Template System**: Reusable task templates with variable substitution and i18n support
- **Cross-Review**: Automatic code review using a different AI CLI after task completion
- **Project Organization**: Organize tasks by projects
- **Terminal Integration**: Native support for iTerm2, Kitty, and Windows Terminal
- **Internationalization**: Full i18n support (English/Chinese)
- **Dark Mode**: Built-in dark/light theme support
- **Cross-Platform**: Works on macOS and Windows

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI
- SQLite (async with aiosqlite)
- WebSocket

**Frontend:**
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Radix UI
- Zustand
- i18next

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- One of the supported AI CLI tools:
  - [Claude Code](https://github.com/anthropics/claude-code)
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

**Or use the start script:**

```bash
python start_web.py
```

Then open http://localhost:3000 in your browser.

### 5-Minute Tutorial

Follow these steps to run your first automated task:

**Step 1: Configure Settings**

1. Open http://localhost:3000 and go to **Settings** page
2. Select your preferred **CLI Type** (e.g., Claude Code)
3. Select your **Terminal** (e.g., iTerm2 on macOS)
4. Set **Max Concurrent Sessions** (default: 3)

**Step 2: Create a Project**

1. Go to **Projects** page
2. Click **New Project**
3. Enter project name and select the project directory path

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
- Run multiple tasks in parallel across different projects

## Project Structure

```
AITaskRunner/
├── backend/                    # FastAPI backend
│   ├── app.py                 # Main application & API routes
│   ├── database/              # Database models (SQLite)
│   ├── models/                # Pydantic schemas
│   ├── services/              # Business logic
│   │   ├── codex_service.py   # CLI session management
│   │   ├── task_service_db.py # Task CRUD operations
│   │   ├── template_service.py# Template management
│   │   ├── settings_service.py# Settings management
│   │   └── project_service.py # Project management
│   └── utils/                 # Utility functions
├── frontend/                   # React frontend
│   └── src/
│       ├── pages/             # Page components
│       ├── components/        # Reusable components
│       ├── stores/            # Zustand state management
│       ├── api/               # API client
│       ├── i18n/              # Internationalization
│       └── types/             # TypeScript types
├── core/                       # Core monitoring logic
│   ├── cli_adapters/          # CLI tool adapters
│   │   ├── claude_code.py     # Claude Code adapter
│   │   ├── codex.py           # Codex CLI adapter
│   │   └── gemini.py          # Gemini CLI adapter
│   ├── terminal_adapters/     # Terminal adapters
│   │   ├── iterm.py           # iTerm2 adapter
│   │   ├── kitty.py           # Kitty adapter
│   │   └── windows_terminal.py# Windows Terminal adapter
│   ├── session/               # Session pool management
│   ├── cli_monitor.py         # CLI monitor
│   └── context_manager.py     # Context tracking
```

## Configuration

Settings can be configured via the web UI Settings page:

- **CLI Type**: Select the AI CLI to use (Claude Code, Codex, Gemini)
- **Terminal**: Select the terminal emulator (iTerm2, Kitty, Windows Terminal)
- **Max Concurrent Sessions**: Limit parallel task execution (1-10)
- **Review Mode**: Enable/disable cross-review with a different CLI
- **Language**: Switch between English and Chinese

## Supported Terminals

| Terminal         | macOS | Windows |
|------------------|-------|---------|
| Windows Terminal | -     | Yes     |
| iTerm2           | Yes   | -       |
| Kitty            | Yes   | -       |

## Troubleshooting

### Callback/Notification Connection Issues

- The callback URL defaults to `http://127.0.0.1:8086` (started by `start_web.py`). If you change the port, update `API_BASE_URL` in `.env` or settings page accordingly.
- If your machine has proxy/security software blocking local loopback, callbacks may fail. Ensure `127.0.0.1:8086` is accessible locally.
- In restricted environments (sandboxes, no local network permission), loopback requests may be intercepted. Grant local network access or run the backend in an environment that allows networking.
- After starting, run `curl http://127.0.0.1:8086/health` to verify. If it fails, check for port conflicts, firewall issues, or restart `start_web.py`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.
