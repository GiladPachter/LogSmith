# 🔐 Security Notes

LogSmith is safe by design, but logging can expose sensitive data if misused.

---

## 🚫 Do Not Log Sensitive Data

Avoid logging passwords, tokens, API keys, or private user data.

---

## 🔒 File Permissions

Ensure log directories are not world‑writable or publicly exposed.

---

## 🧩 Multi‑Process Safety

Locks prevent corruption but do not enforce access control.

---

## 🛡️ Sanitizing Input

Use:

```
CPrint.escape_control_chars(text)
CPrint.strip_ansi(text)
```

---

## 🧨 Avoid Logging Secrets in Exceptions

Tracebacks may contain sensitive values.

---

## 🧩 Summary

Your logging choices determine your security posture.
