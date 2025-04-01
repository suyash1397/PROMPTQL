#!/bin/bash

# Function to create a commit with a specific date
create_commit() {
    local date="$1"
    local message="$2"
    local files="$3"
    
    GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" \
    git commit -m "$message" $files
}

# Initial project setup (Feb 1)
git add README.md requirements.txt .gitignore
create_commit "2024-02-01" "Initial commit: Project setup"

# Core structure (Feb 5)
git add app/__init__.py app/main.py
create_commit "2024-02-05" "feat: Add basic FastAPI application structure"

# Database models (Feb 10)
git add app/models/
create_commit "2024-02-10" "feat: Add database models and schemas"

# Database adapters (Feb 15)
git add app/databases/
create_commit "2024-02-15" "feat: Add database adapters for multiple databases"

# Configuration (Feb 20)
git add app/config/
create_commit "2024-02-20" "feat: Add configuration management"

# LLM integration (Feb 25)
git add app/core/llm.py
create_commit "2024-02-25" "feat: Add LLM integration with Claude"

# Error handling (Mar 1)
git add app/core/errors.py
create_commit "2024-03-01" "feat: Add error handling system"

# Validation (Mar 5)
git add app/core/validation.py
create_commit "2024-03-05" "feat: Add query validation"

# Security features (Mar 10)
git add app/core/security.py
create_commit "2024-03-10" "feat: Add security middleware and rate limiting"

# Monitoring (Mar 15)
git add app/core/monitoring.py
create_commit "2024-03-15" "feat: Add monitoring and metrics"

# Test suite (Mar 20)
git add tests/
create_commit "2024-03-20" "test: Add comprehensive test suite"

# Setup scripts (Mar 25)
git add scripts/
create_commit "2024-03-25" "feat: Add database setup and test scripts"

# Documentation updates (Apr 1)
git add README.md
create_commit "2024-04-01" "docs: Update README with setup instructions"

# Final touches (Apr 5)
git add .
create_commit "2024-04-05" "chore: Final project cleanup and organization" 