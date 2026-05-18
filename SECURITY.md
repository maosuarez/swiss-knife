# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Status | Security Updates |
|---------|--------|------------------|
| 1.0.x   | Current | Supported |
| < 1.0   | EOL | Not supported |

If you're using an older version, please upgrade to the latest version to receive security updates.

---

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Swiss Knife, please report it responsibly.

### How to Report

**Do not open a public GitHub issue for security vulnerabilities.** Instead:

1. **Email us** at: `maosuarezbarrer@gmail.com`
   - Subject: `[SECURITY] Swiss Knife Vulnerability Report`
   - Include a clear description of the vulnerability, affected version(s), and steps to reproduce if applicable.

2. **Or use GitHub's private security advisory** (if available):
   - Go to the [Security](https://github.com/yourusername/swiss-knife/security) tab on GitHub.
   - Click "Report a vulnerability" and fill out the form privately.

### What to Include

- **Tool affected** (e.g., `transcribe`, `convert`, `crypto`)
- **Affected version** (e.g., 1.0.0)
- **Type of vulnerability** (see categories below)
- **Description** of the issue
- **Steps to reproduce** (if applicable)
- **Proof of concept** (if applicable)
- **Suggested fix** (if you have one)

### Response Timeline

We commit to:

- **Acknowledge receipt** of your report within 48 hours
- **Provide an initial assessment** within 7 days
- **Release a fix** for critical vulnerabilities within 14 days of confirmation
- **Publish a security advisory** after you've had time to patch

If you report a vulnerability, we may ask follow-up questions. Please keep communication confidential until we release a fix.

---

## What Constitutes a Security Issue

### Security Issues (Please Report)

- **Local file access vulnerabilities** — A tool reads files it shouldn't or exposes sensitive file paths unintentionally.
- **Cryptographic implementation flaws** — The `crypto` tool's cipher implementations have logical errors that compromise security.
- **Unsafe deserialization** — A tool deserializes untrusted data without validation.
- **Command injection** — A tool passes user input unsafely to external commands (ffmpeg, pandoc, etc.).
- **Dependency vulnerabilities** — A critical security flaw in a dependency (reported via dependabot or security advisories).
- **Privilege escalation** — A tool can be exploited to gain elevated privileges.
- **Information disclosure** — Sensitive data (passwords, API keys, etc.) is logged, cached, or exposed unintentionally.

### NOT Security Issues (Use GitHub Issues)

- **Intended behaviors** — Features that work as designed but you disagree with (e.g., `crypto` tool supporting weak ciphers for educational purposes).
- **UX/usability rough edges** — Unclear error messages, missing options, confusing help text.
- **Performance issues** — Slow batch processing, high memory usage (performance, not security).
- **Missing features** — Requests for new tools or functionality.
- **Documentation gaps** — Unclear or incomplete docs.

---

## Security Practices

### What We Do

- **Local-First Design** — All processing happens on your machine. Swiss Knife does not send data to external services (except user-initiated downloads like `fetch`).
- **Dependency Management** — We track and update dependencies regularly. See `pyproject.toml` for the full list.
- **Validation** — All tools validate input files, paths, and user arguments before processing.
- **No Logging** — Swiss Knife does not log execution data, user inputs, or results by default.
- **Windows Security** — We follow Windows security best practices (no hardcoded credentials, safe temp file handling, etc.).

### What You Should Do

- **Keep dependencies updated** — Regularly run `pip install --upgrade -e .` to get the latest versions.
- **Use from trusted locations** — If using Swiss Knife in automated workflows, ensure the scripts are trusted and the environment is secure.
- **Be cautious with sensitive files** — The `crypto` tool is for educational use, not protecting highly sensitive data. Use proper encryption tools for that.
- **Report issues responsibly** — Follow this policy. Don't publish exploits publicly before we've had time to patch.

---

## Known Limitations

- **Classic ciphers (crypto tool)** — The `crypto` tool implements educational ciphers (Caesar, Vigenère, etc.) for learning. These are not suitable for protecting real secrets. Use proper encryption libraries (like cryptography) for sensitive data.
- **AI models (transcribe, rembg)** — Whisper and U2Net models are downloaded and cached locally on first use (~200MB combined). Verify the integrity of these models if you're running Swiss Knife in a sensitive environment.
- **Windows-specific features** — The `convert` tool uses MS Word COM for docx→pdf conversion, which requires Word to be installed. This is a Windows-only feature.

---

## Dependency Security

Swiss Knife depends on several third-party libraries. We monitor these dependencies for security issues:

- **Rich** — Terminal output styling
- **Whisper** — Audio transcription
- **rembg** — Background removal
- **ffmpeg** — Media processing (via conda)
- **PyPDF2** — PDF manipulation
- **requests** — HTTP requests
- **BeautifulSoup4** — HTML parsing
- And others (see [pyproject.toml](pyproject.toml))

If a critical vulnerability is found in any dependency, we will:

1. Assess the impact on Swiss Knife
2. Update the dependency or release a workaround
3. Publish a security advisory

You can also check for vulnerable dependencies yourself using:

```powershell
pip install safety
safety check
```

---

## Security Contact

**Email:** `maosuarezbarrer@gmail.com`

**GitHub:** [@maosuarezbarrer](https://github.com/maosuarezbarrer)

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) — Common web application security risks
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/) — Most dangerous software weaknesses
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

Thank you for helping us keep Swiss Knife secure!
