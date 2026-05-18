# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Agent Company, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email: **security@agent-company.dev**

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix release**: Depends on severity, typically within 2 weeks for critical issues

### Scope

This policy covers:
- `packages/core` — Core SDK
- `packages/server` — FastAPI server
- `packages/cli` — CLI tool

Third-party dependencies are out of scope but we appreciate reports about vulnerable dependencies.

## Security Best Practices

When using Agent Company:

- Never commit API keys (`.env` is in `.gitignore`)
- Use environment variables for LLM provider credentials
- Review agent outputs before executing in production
- Use budget limits to cap LLM spending
