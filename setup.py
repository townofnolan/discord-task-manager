from setuptools import find_packages, setup

setup(
    name="discord-task-manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "discord.py>=2.0.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.7.0",
        "fastapi>=0.95.0",
        "uvicorn>=0.15.0",
        "asyncpg>=0.27.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "flake8-docstrings>=1.7.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.3",
            "bandit>=1.7.5",
        ],
    },
    python_requires=">=3.11",
)
