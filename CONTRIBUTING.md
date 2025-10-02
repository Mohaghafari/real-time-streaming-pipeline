# Contributing to Real-Time Streaming Pipeline

First off, thank you for considering contributing to this project! 🎉

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples**
- **Describe the behavior you observed** and what you expected
- **Include screenshots** if applicable
- **Specify your environment** (OS, Docker version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Explain why this enhancement would be useful**
- **List some examples** of how it would be used

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** with clear, descriptive commit messages
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Submit a pull request** with a comprehensive description

#### Pull Request Guidelines:

- Follow the existing code style
- Write clear commit messages
- Include tests for new features
- Update the README.md if needed
- Keep pull requests focused on a single feature/fix

## Development Setup

1. Clone your fork:
```bash
git clone https://github.com/Mohaghafari/real-time-streaming-pipeline.git
cd real-time-streaming-pipeline
```

2. Start the development environment:
```bash
docker-compose up -d
```

3. Run tests:
```bash
pytest tests/ -v
```

## Project Structure

```
.
├── src/
│   ├── producer/          # Event generation
│   ├── consumer/          # Spark streaming
│   ├── monitoring/        # Monitoring tools
│   └── utils/             # Shared utilities
├── tests/                 # Test suites
├── config/                # Configuration files
├── docker/                # Docker build files
└── scripts/               # Operational scripts
```

## Coding Standards

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where appropriate
- Write docstrings for all functions/classes
- Keep functions focused and under 50 lines when possible
- Use meaningful variable names

### Documentation

- Update README.md for user-facing changes
- Add inline comments for complex logic
- Include docstrings with examples
- Keep documentation up-to-date with code

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests liberally

Example:
```
Add watermarking support for late events

- Implement 5-minute watermark in streaming consumer
- Add configuration option for watermark duration
- Update documentation with watermarking examples

Closes #123
```

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Aim for high test coverage
- Test edge cases and error conditions

Run tests:
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/test_event_generator.py -v
```

## Documentation

When adding new features, please update:

1. **README.md** - User-facing documentation
2. **LEARNING_GUIDE.md** - Educational content
3. **Inline comments** - For complex code
4. **Docstrings** - For all public functions/classes

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

## Recognition

Contributors will be recognized in:
- The project README
- Release notes
- GitHub contributors page

Thank you for contributing! 🚀


