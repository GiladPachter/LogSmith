# 🔐 Security Notes

LogSmith is safe by design, but logging can expose sensitive data if misused.<br/>
This chapter highlights the most important security considerations when using LogSmith in production systems.

---

## 🚫 Do Not Log Sensitive Data

Avoid logging:

- passwords  
- API keys  
- tokens  
- session identifiers  
- private user data
- raw request/response bodies  
- database credentials  
- cryptographic material  

Structured fields (`named_args`) make logs machine‑friendly — but they also make sensitive data easier to extract.  
Never attach secrets to structured fields.

---

## 🔒 File Permissions

Ensure log directories:

- are not world‑writable
- are not publicly exposed
- have correct ownership
- are protected by OS‑level permissions

On Linux:

```
chmod 750 logs/
```

On Windows, ensure the directory ACL restricts access to the service account.

---

## 🧩 Multi‑Process Safety

LogSmith uses OS‑level locks:

- `fcntl` on Unix
- `msvcrt` on Windows

These prevent corruption but **do not enforce access control**.

Security implications:

- multiple processes writing to the same file on Windows is **not supported**  
- use per‑process log files in multi‑process environments
- ensure directories are not shared with untrusted processes

---

## 🛡️ Sanitizing Input

If you log user‑supplied text, sanitize it:

```python
CPrint.escape_control_chars(text)
CPrint.strip_ansi(text)
```

This prevents:

- ANSI injection
- terminal escape attacks
- log poisoning
- malformed JSON/NDJSON

Always sanitize untrusted input before logging it.

---

## 🧨 Avoid Logging Secrets in Exceptions

Tracebacks may contain:

- function arguments
- environment variables
- partial payloads
- internal state

If exceptions may contain sensitive data:

- disable `exc_info=True`
- sanitize exception messages
- wrap exceptions with safe messages

Example:

```python
try:
    risky()
except Exception as e:
    logger.error("Operation failed", error=str(e).replace(secret, "***"))
```

---

## 🧾 JSON / NDJSON Security

JSON and NDJSON logs include:

- `named_args`
- file path
- line number
- function name
- process/thread IDs

Be aware that these logs are highly structured and easy to parse.<br/>
Do not include sensitive metadata in structured fields.

---

## 🎛️ Raw Output Safety

Raw output bypasses formatting:

```python
logger.raw(user_supplied_text)
```

This can be dangerous.

Raw output:

- preserves ANSI
- bypasses sanitization
- bypasses formatting rules

Never send untrusted input to `logger.raw()`.

---

## 🛰️ Auditing Considerations

Audit logs capture **everything**:

- all loggers
- all structured fields
- all exceptions
- all metadata

Security implications:

- audit logs may contain sensitive operational data
- ensure audit directories are protected
- rotate audit logs with retention
- avoid logging secrets anywhere in the system

Audit logs should be treated as sensitive artifacts.

---

## 📦 File Handler Sanitization

By default, file handlers remove ANSI escape sequences.

Only disable sanitization when absolutely necessary:

```python
logger.add_file(
    log_dir="logs",
    logfile_name="colored.log",
    preserve_colors_in_log_files=True,
)
```

Leaving ANSI enabled in files can:

- break ingestion pipelines
- enable log injection attacks
- corrupt NDJSON

---

## 🧱 Hierarchy & Propagation Safety

Propagation is disabled unless auditing is enabled.

When auditing is active:

- all loggers propagate upward
- all logs flow into the audit handler

Ensure:

- audit directories are secure
- audit logs do not leak sensitive data
- dynamic levels do not expose internal state

---

## 📘 Summary

Your logging choices determine your security posture.

- never log secrets
- sanitize untrusted input
- protect log directories
- treat audit logs as sensitive
- avoid raw output for user data
- be careful with exceptions
- use per‑process files on Windows

Logging is powerful — use it responsibly.
