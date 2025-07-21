"""Database models for Discord Task Manager."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class TaskStatus(Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Association table for task assignees (many-to-many)
task_assignees = Table(
    "task_assignees",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)

# Association table for project members (many-to-many)
project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    """User model for Discord users."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    display_name = Column(String(100))
    avatar_url = Column(String(500))
    timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    assigned_tasks = relationship(
        "Task", secondary=task_assignees, back_populates="assignees"
    )
    created_tasks = relationship(
        "Task", foreign_keys="Task.creator_id", back_populates="creator"
    )
    projects = relationship(
        "Project", secondary=project_members, back_populates="members"
    )
    time_entries = relationship("TimeEntry", back_populates="user")

    def __repr__(self):
        return f"<User(discord_id={self.discord_id}, username='{self.username}')>"


class Project(Base):
    """Project model for organizing tasks."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    discord_channel_id = Column(BigInteger)
    color = Column(String(7), default="#3498db")  # Hex color code
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tasks = relationship("Task", back_populates="project")
    members = relationship("User", secondary=project_members, back_populates="projects")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class Task(Base):
    """Task model for individual tasks."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    status = Column(String(20), default=TaskStatus.TODO.value)
    priority = Column(String(10), default=TaskPriority.MEDIUM.value)

    # Discord-specific fields
    discord_message_id = Column(BigInteger)
    discord_thread_id = Column(BigInteger)
    discord_channel_id = Column(BigInteger)

    # Relationships
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship("Project", back_populates="tasks")

    creator_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship(
        "User", foreign_keys=[creator_id], back_populates="created_tasks"
    )

    assignees = relationship(
        "User", secondary=task_assignees, back_populates="assigned_tasks"
    )

    # Dates
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Custom fields (JSON)
    custom_fields = Column(JSON, default=dict)

    # Tags
    tags = Column(JSON, default=list)

    # Time tracking
    estimated_hours = Column(Float)

    # Relationships
    time_entries = relationship("TimeEntry", back_populates="task")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"

    @property
    def total_time_spent(self) -> float:
        """Calculate total time spent on this task in hours."""
        return sum(entry.duration_hours for entry in self.time_entries)


class TimeEntry(Base):
    """Time tracking entries for tasks."""

    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True)
    description = Column(String(500))
    duration_hours = Column(Float, nullable=False)

    # Relationships
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    task = relationship("Task", back_populates="time_entries")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="time_entries")

    # Timestamps
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, task_id={self.task_id}, duration={self.duration_hours}h)>"


class CustomField(Base):
    """Custom field definitions for projects."""

    __tablename__ = "custom_fields"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    field_type = Column(
        String(50), nullable=False
    )  # text, number, date, select, multi_select
    options = Column(JSON)  # For select/multi_select fields
    is_required = Column(Boolean, default=False)

    # Relationship
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship("Project")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return (
            f"<CustomField(id={self.id}, name='{self.name}', type='{self.field_type}')>"
        )


class TaskTemplate(Base):
    """Template for creating similar tasks."""

    __tablename__ = "task_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    title_template = Column(String(300), nullable=False)
    description_template = Column(Text)
    default_priority = Column(String(10), default=TaskPriority.MEDIUM.value)
    default_tags = Column(JSON, default=list)
    default_custom_fields = Column(JSON, default=dict)
    estimated_hours = Column(Float)

    # Relationship
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship("Project")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<TaskTemplate(id={self.id}, name='{self.name}')>"
