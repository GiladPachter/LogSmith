# Best Practices  
This chapter distills everything in LogSmith into practical, real‑world guidance. These best practices help you design clean, maintainable, high‑performance logging setups for applications of any size — from tiny scripts to distributed async systems.

---

## Designing a Clean Logging Architecture  
A well‑structured logging system is predictable, easy to debug, and easy to extend. The following principles keep your architecture clean:

- use dot‑separated logger names to mirror your module structure  
- attach a console handler only to the root logger  
- attach file handlers to specific modules or subsystems  
- use JSON/NDJSON for ingestion pipelines  
- use themes for readability in development  
- use auditing in production for global capture  

This keeps logs organized without duplication or handler chaos.

---

## Choosing Between Sync and Async  
### SmartLogger (sync)
Use when:

- your application is synchronous  
- you want minimal overhead  
- you don’t use asyncio  
- you want simple lifecycle management  

### AsyncSmartLogger (async)
Use when:

- your application uses asyncio  
- you need non‑blocking logging  
- you want ordering guarantees across tasks  
- you want async‑safe rotation  

Async logging is ideal for servers, bots, and pipelines.

---

## Handler Best Practices  
Handlers define where logs go and how they look.

- attach **one console handler** to the root logger  
- attach **file handlers** to module‑level loggers  
- avoid attaching many handlers to many loggers  
- use NDJSON for ingestion  
- use PLAIN mode for file logs unless color is explicitly needed  
- sanitize ANSI in files (default)  

This prevents duplication and keeps logs clean.

---

## Rotation & Retention Best Practices  
Rotation is essential for long‑running applications.

- use size‑based rotation for unpredictable workloads  
- use time‑based rotation for predictable workloads  
- use hybrid rotation for high‑volume logs  
- set retention rules to avoid disk bloat  
- avoid rotating too frequently (increases overhead)  
- use timestamp anchors for daily/weekly rotation  

Async rotation is recommended for heavy workloads.

---

## Structured Fields Best Practices  
Structured fields make logs machine‑friendly.

- use named arguments for structured fields  
- keep field names short and consistent  
- avoid deeply nested structures  
- ensure values are JSON‑serializable  
- use structured fields instead of embedding data in the message  

This improves readability and ingestion quality.

---

## JSON & NDJSON Best Practices  
JSON is for humans; NDJSON is for machines.

- use JSON for debugging  
- use NDJSON for ingestion pipelines  
- avoid pretty JSON in production (slower)  
- ensure raw output is not mixed with JSON  
- ensure structured fields are serializable  

NDJSON is the recommended format for production systems.

---

## Theme & Color Best Practices  
Color improves readability but should be used wisely.

- use themes during development  
- avoid gradients in high‑volume logs  
- avoid color in file logs unless explicitly needed  
- reset themes when switching environments  
- style dynamic levels for clarity  

Themes should enhance readability, not distract.

---

## Dynamic Level Best Practices  
Dynamic levels add expressive power.

- choose numeric values that fit between existing levels  
- use dynamic levels for domain‑specific events  
- style them with themes  
- avoid creating too many levels  
- use them consistently across modules  

Dynamic levels should clarify, not complicate.

---

## Auditing Best Practices  
Auditing provides a global capture of all logs.

- enable auditing in production  
- use NDJSON for audit logs  
- rotate audit logs with retention  
- ensure audit directory is writable  
- disable auditing during tests unless needed  

Auditing is ideal for compliance, debugging, and forensics.

---

## Lifecycle Best Practices  
Clean lifecycle management prevents leaks and corruption.

- retire loggers when temporarily disabling them  
- destroy loggers when resetting configuration  
- flush async loggers before shutdown  
- use global shutdown at application exit  
- avoid creating many short‑lived loggers  

Lifecycle management keeps your logging system stable.

---

## Performance Best Practices  
Logging should be fast and predictable.

- use async logging for high‑volume workloads  
- avoid gradients in production  
- minimize rotation frequency  
- avoid attaching too many handlers  
- prefer NDJSON over pretty JSON  
- avoid extremely large structured fields  

These practices maximize throughput and minimize latency.

---

## Testing Best Practices  
Logging should be test‑friendly.

- destroy loggers between tests  
- use temporary directories for file handlers  
- disable auditing during tests  
- use PLAIN mode for predictable output  
- avoid async logging unless testing async behavior  

This ensures clean, reproducible test output.

---

## Summary  
These best practices help you build:

- clean logging architectures  
- predictable handler setups  
- efficient rotation and retention  
- readable console output  
- ingestion‑friendly JSON/NDJSON logs  
- safe async logging  
- maintainable lifecycle management  
- high‑performance logging pipelines  

The next chapter covers **Examples & Recipes**, providing ready‑to‑use patterns for common real‑world scenarios.
