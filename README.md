# Discord Task Manager

A comprehensive Discord bot with Airtable-like task management functionality designed for small teams (10-15 users). This bot provides a complete project management solution with rich Discord integration, natural language processing, time tracking, and calendar integration.

## 🚀 Features

### Core Task Management
- ✅ **Task Creation & Management**: Create, update, and delete tasks with rich metadata
- 📁 **Project Organization**: Organize tasks into projects with team member management
- 👥 **Team Assignments**: Assign tasks to team members with workload balancing
- 🎯 **Status Tracking**: Track task progress through customizable status workflows
- 🏷️ **Priority System**: Set task priorities (Low, Medium, High, Urgent)
- 🔧 **Custom Fields**: Extensible custom field support similar to Airtable

### Rich Discord UI
- 🎛️ **Interactive Buttons**: Rich button interfaces for task management
- 📋 **Modal Forms**: Form-based task creation and editing
- ⚡ **Reaction Updates**: Quick status updates via emoji reactions
- 🧵 **Thread Organization**: Automatic thread creation for task discussions
- 📊 **Rich Embeds**: Beautiful, informative task and project displays

### Smart Scheduling & Analytics
- 🧠 **Workload Analysis**: Detect overloaded team members
- 📅 **Due Date Suggestions**: AI-powered optimal scheduling
- ⚖️ **Task Balancing**: Intelligent assignment distribution
- 📈 **Progress Tracking**: Team and individual productivity insights

### Natural Language Processing
- 🗣️ **Natural Commands**: Parse task details from natural language
- 📝 **Smart Extraction**: Extract dates, priorities, tags, and assignments
- 🤖 **Command Examples**: "Create a task to finish the report by Friday #urgent @john"

### Time Tracking
- ⏱️ **Interactive Timers**: Start/stop timers with Discord UI
- 📊 **Time Reports**: Detailed time tracking by task, project, and user
- 📈 **Productivity Analytics**: Insights into time usage patterns

### Calendar Integration
- 📅 **iCal Generation**: Export tasks as calendar feeds
- 🔗 **URL Subscriptions**: Subscribe to project calendars
- ⏰ **Deadline Tracking**: Upcoming and overdue task notifications

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Discord Bot Token
- Discord Server with appropriate permissions

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd discord-task-manager
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**
   ```bash
   # Initialize database tables
   python -c "import asyncio; from utils.database import init_database; asyncio.run(init_database())"
   
   # Or use Alembic for migrations
   alembic upgrade head
   ```

5. **Run the bot**
   ```bash
   python main.py
   ```

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_discord_guild_id_here

# Database Configuration  
DATABASE_URL=postgresql://username:password@localhost:5432/discord_task_manager

# Bot Configuration
BOT_PREFIX=!
DEBUG=False
LOG_LEVEL=INFO

# Feature Flags
ENABLE_NLP=True
ENABLE_CALENDAR=True
ENABLE_TIME_TRACKING=True
```

### Railway.app Deployment

1. **Connect your repository to Railway**
2. **Set environment variables in Railway dashboard**
3. **Add PostgreSQL database addon**
4. **Deploy with automatic builds**

The bot includes Railway-optimized configuration with `Procfile` and `runtime.txt`.

## 📋 Usage Guide

### Slash Commands

#### Task Management
- `/create-task` - Create a new task with interactive form
- `/task <id>` - View and manage a specific task
- `/my-tasks [status]` - View your assigned tasks
- `/task-modal` - Open task creation modal (prefix command)

#### Project Management  
- `/create-project` - Create a new project
- `/project <id>` - View and manage a specific project
- `/my-projects` - View projects you're a member of
- `/projects` - List all active projects

#### Time Tracking
- `/start-timer <task_id>` - Start tracking time for a task
- `/stop-timer <task_id> [description]` - Stop timer and log time
- `/active-timers` - View your currently running timers
- `/time-report [task_id] [days]` - View time tracking reports

#### Calendar & Deadlines
- `/upcoming-deadlines [days]` - View upcoming task deadlines
- `/overdue-tasks` - View overdue tasks
- `/calendar-export [project_id]` - Export calendar feed

#### Administration
- `/admin-stats` - View bot statistics (Admin only)
- `/sync` - Sync slash commands (Admin only)
- `/db-init` - Initialize database (Admin only)

### Interactive Features

#### Task Creation Modal
Use the task creation modal for rich task input:
- Task title and description
- Priority selection
- Due date setting
- Team member assignment
- Tag management

#### Task Management Buttons
Each task display includes action buttons:
- ✏️ **Edit** - Modify task details
- ✅ **Complete** - Mark task as done
- 🗑️ **Delete** - Remove task

#### Project Management
- Add/remove team members
- View project statistics
- Manage project settings
- Track project progress

## 🏗️ Architecture

### Project Structure
```
discord-task-manager/
├── bot/                    # Discord bot implementation
│   ├── main.py            # Main bot application
│   └── cogs/              # Bot command modules
│       ├── tasks.py       # Task management commands
│       ├── projects.py    # Project management commands
│       ├── time_tracking.py  # Time tracking features
│       ├── calendar_integration.py  # Calendar features
│       └── admin.py       # Administrative commands
├── models/                # Database models (SQLAlchemy)
├── services/              # Business logic layer
│   ├── task_service.py    # Task operations
│   ├── project_service.py # Project operations
│   └── user_service.py    # User management
├── utils/                 # Utility functions
│   └── database.py        # Database connection management
├── config/                # Configuration management
│   ├── settings.py        # Application settings
│   └── logging.py         # Logging configuration
├── migrations/            # Alembic database migrations
├── tests/                 # Test suite
└── requirements.txt       # Python dependencies
```

### Technology Stack
- **Framework**: Discord.py (async/await)
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Migrations**: Alembic
- **Deployment**: Railway.app
- **Testing**: pytest with async support
- **Code Quality**: Black, flake8, mypy

### Database Schema
- **Users**: Discord user profiles and preferences
- **Projects**: Project organization and team membership
- **Tasks**: Task details, assignments, and metadata
- **TimeEntries**: Time tracking records
- **CustomFields**: Extensible field definitions

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_task_service.py
```

## 📊 Monitoring & Logs

The bot includes comprehensive logging:
- Console output for development
- File rotation for production
- Structured logging with timestamps
- Error tracking and reporting

Log files are stored in the `logs/` directory with automatic rotation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Style
- Use Black for code formatting
- Follow PEP 8 guidelines
- Add type hints where appropriate
- Write docstrings for functions and classes

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the documentation above
2. Review the GitHub issues
3. Create a new issue with detailed information

## 🔮 Roadmap

### Phase 1 - Core Features ✅
- Basic task and project management
- Discord UI integration
- Database foundation

### Phase 2 - Advanced Features (In Progress)
- Natural language processing
- Advanced time tracking
- Calendar integration
- Smart scheduling

### Phase 3 - AI & Analytics (Planned)
- AI-powered task suggestions
- Advanced analytics dashboard
- Workload optimization
- Predictive scheduling

### Phase 4 - Integrations (Planned)
- External calendar sync (Google, Outlook)
- Third-party integrations (Slack, Teams)
- API endpoints for external tools
- Mobile companion app