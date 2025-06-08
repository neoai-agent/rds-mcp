# Contributing to RDS MCP

Thank you for your interest in contributing to RDS MCP! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in the Issues section
2. Use the bug report template when creating a new issue
3. Include detailed steps to reproduce the bug
4. Include relevant logs and error messages
5. Specify your environment (OS, Python version, etc.)

### Suggesting Features

1. Check if the feature has already been suggested
2. Use the feature request template
3. Provide a clear description of the feature
4. Explain why this feature would be useful
5. Include any relevant examples or use cases

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature/fix
3. Make your changes
4. Add tests for new features
5. Update documentation
6. Ensure all tests pass
7. Submit a pull request

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rds-mcp.git
cd rds-mcp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions and classes
- Keep functions small and focused
- Write meaningful commit messages

### Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Maintain or improve test coverage
- Run tests locally before pushing

### Documentation

- Update README.md if needed
- Add docstrings to new functions/classes
- Update API documentation
- Include examples for new features

### Commit Messages

Follow the conventional commits specification:
- feat: A new feature
- fix: A bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Adding or modifying tests
- chore: Maintenance tasks

Example:
```
feat: add support for Aurora PostgreSQL
```

### Review Process

1. All PRs require at least one review
2. Address review comments promptly
3. Keep PRs focused and small
4. Respond to CI/CD feedback

### Getting Help

- Join our community discussions
- Ask questions in Issues
- Check existing documentation
- Reach out to maintainers

Thank you for contributing to RDS MCP! 