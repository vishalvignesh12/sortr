# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 5.1.x   | :white_check_mark: |
| 5.0.x   | :x:                |
| 4.0.x   | :white_check_mark: |
| < 4.0   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by sending an email to [security@yourcompany.com].

We will review the vulnerability and respond to you within 48 hours with next steps.

### When to Report a Security Vulnerability

- You think you discovered a potential security vulnerability in this application
- You're unsure if a vulnerability is present or not
- You discovered a vulnerability in another project that is used by this application

### When NOT to Report a Security Vulnerability

- You need help applying security-related updates to your local deployment
- Your issue is not related to security
- You believe you found a vulnerability in another project that this project uses

For non-security related bugs, please use GitHub Issues instead.

## Security Best Practices

### For Developers
- Never commit sensitive information (passwords, API keys, etc.) to the repository
- Use environment variables for all sensitive data
- Regularly update dependencies to patch known vulnerabilities
- Follow the principle of least privilege for all API calls
- Implement proper input validation and sanitization
- Use secure communication (HTTPS) for all data transmission

### For Users
- Keep your application updated to the latest version
- Use strong authentication methods
- Regularly review and rotate API keys
- Monitor your application for suspicious activity