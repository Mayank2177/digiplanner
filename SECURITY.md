# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Below are the versions that are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in Digi-planner, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email your findings to the project maintainer with:
   - Description of the vulnerability
   - Steps to reproduce (if applicable)
   - Potential impact
   - Any proposed fixes or suggestions

3. You should receive a response acknowledging receipt of your vulnerability report within **7 days**
4. Once confirmed, you'll receive updates on the progress of the fix

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 7 days
- **Assessment**: We will investigate and assess the vulnerability
- **Fix**: We will develop and test a fix
- **Release**: We will release a patch as soon as possible
- **Disclosure**: We will coordinate with you on the timing of public disclosure

### Our Commitment

- We will credit you for the discovery (unless you prefer anonymity)
- We will keep you informed throughout the process
- We will release patches promptly for confirmed vulnerabilities
- We take all security reports seriously and treat them with confidentiality

## Security Features

### Authentication & Authorization
- User authentication with secure password hashing
- Session management
- User role-based access control

### Data Protection
- Secure data storage for sensitive information
- Encrypted communication channels (HTTPS)
- Input validation and sanitization
- Protection against common vulnerabilities (SQL Injection, XSS, CSRF)

### Secure Dependencies
- Regular updates to dependencies
- Monitoring for known vulnerabilities
- Using trusted and well-maintained packages

### Third-Party Integrations
- Secure API communication
- Authentication tokens handled securely
- Minimal exposure of sensitive credentials

## Best Practices

When using Digi-planner:

1. Keep your dependencies updated by running `npm install` and `pip install --upgrade -r requirements.txt` regularly
2. Use strong, unique passwords for user accounts
3. Enable HTTPS in production environments
4. Store environment variables securely (use `.env` files, never commit credentials)
5. Regularly review access logs and user activities
6. Report any suspicious activities immediately

## Security Disclaimer

While we implement security best practices, no system is entirely secure. Users are responsible for:
- Maintaining their account credentials securely
- Reviewing their uploaded documents for sensitive information
- Following their organization's security policies

## Contact

For security concerns or vulnerability reports, please reach out to the project maintainer:
- GitHub: [@Mayank2177](https://github.com/Mayank2177)

Thank you for helping keep Digi-planner secure!
