# 🚀 Performance & Optimization

LogSmith is designed for high‑volume, production‑grade logging.<br/>
It can handle tens of thousands of log events per second when configured correctly.<br/>
This chapter explains how to optimize performance, reduce overhead, tune async behavior, and choose the right handlers and formatters for your workload.

---

## 💡 Why Performance Tuning Matters

Logging is often overlooked as a performance bottleneck.
In real systems, logging can:
- slow down request handlers
- block event loops
- saturate disks
- overwhelm ingestion pipelines
- create backpressure in async applications.


Performance tuning ensures that logging remains fast, predictable, and unobtrusive even under heavy load.

LogSmith prioritizes include:

- low overhead per log call  
- predictable latency  
- safe concurrency  
- efficient rotation  
- minimal blocking in async applications  
- zero dependencies  
- optimized string building and formatting  

The goal is to provide rich features without sacrificing speed.

---

## ⚙️ Sync vs Async Performance

Synchronous logging writes directly to disk or stdout. It is simple and predictable but can block the application during:

- slow disk writes  
- rotation events  
- large JSON encoding  
- high‑volume bursts  

Async logging offloads all I/O to a background worker. This provides:

- non‑blocking logging  
- smoother throughput  
- better CPU utilization  
- safer rotation under load  

Async logging is recommended for:

- web servers  
- microservices  
- data pipelines  
- high‑volume batch jobs  

Sync logging is fine for:

- CLI tools  
- small scripts  
- low‑volume services  

---

## 🧰 Handler Efficiency

Handlers vary in cost:

- console handler → fastest  
- file handler → fast, depends on disk  
- JSON handler → moderate cost  
- NDJSON handler → moderate cost, less than indented JSON
- audit handler → moderate to high cost  
- raw handler → fast, but not structured  

The most expensive operations are:

- JSON encoding  
- NDJSON line generation  
- rotation under heavy load  

If performance is critical:

- prefer NDJSON over JSON  
- avoid excessive structured fields  
- avoid large multi‑line messages  
- use async logging for file handlers  

---

## 🧾 Formatter Cost

Formatters determine how much CPU time is spent per log event. Cost increases with:

- JSON encoding  
- deep structured fields  
- exception formatting  
- stack trace extraction  
- theme rendering  

Theme rendering is negligible compared to JSON encoding. Exception formatting is the most expensive operation in the entire logging pipeline.

If you need maximum throughput:

- avoid logging exceptions in hot loops  
- avoid deep structured fields  
- avoid large dictionaries or lists in fields  
- prefer NDJSON for ingestion pipelines  

---

## 🧩 Structured Field Overhead

Structured fields are powerful but add overhead:

```python
logger.info("User login", username = "Gilad", roles = ["admin", "editor"])
```

Each field must be:

- sanitized  
- serialized  
- merged into the log record  
- encoded into JSON or NDJSON  

For high‑volume systems:

- keep structured fields shallow  
- avoid large lists or nested objects  
- avoid storing raw payloads (e.g., entire HTTP bodies)  
- prefer references or IDs instead of full objects  

Structured logging is worth the cost, but it should be used intentionally.

---

## 🔄 Rotation Optimization

Rotation can become a bottleneck under heavy load. To optimize:

- use async logging so rotation happens in a worker  
- increase `maxBytes` to reduce rotation frequency  
- avoid rotation in small time intervals
- use SSDs instead of HDDs  
- avoid rotating multiple loggers into the same directory at the same moment  

Async rotation uses a thread pool to ensure that rotation does not block the main worker.

---

## 🔓 Minimizing Lock Contention

File handlers use OS‑level locks to ensure safe writes.
Contention increases when:

- multiple processes write to the same file
- rotation triggers frequently
- slow disks cause long lock durations

To reduce contention:

- avoid multi‑process writes on Windows  
- increase rotation thresholds  
- use async logging to shorten lock durations  

On Unix, fcntl locks are efficient, but Windows file locks are more restrictive.

---

## 🧱 Avoiding Bottlenecks

Common bottlenecks include:

- synchronous file writes  
- JSON encoding of large payloads  
- excessively structured fields  
- slow disks  
- too many handlers attached to one logger  
- logging inside tight loops  

To minimize bottlenecks:

- use async logging for all file handlers  
- keep structured fields shallow  
- avoid logging large objects  
- avoid logging inside micro‑loops  
- prefer NDJSON over JSON for ingestion pipelines  

Logging should never be the slowest part of your application.

---

## Multi‑Process Performance  
LogSmith supports multi‑process logging with caveats:

- safe on Unix (fcntl locks)  
- safe on Windows only if each process writes to its own base file(s)  
- rotation is atomic across processes  
- retention is safe  

File handlers use OS-level locks to ensure safe writes.
Contention increases when multiple processes write to the same file
On Linux, fcntl locks are efficient, but Windows file locks are more restrictive and a lot more challenging.
Therefore, for the forseeable future LogSmith does not provide means for logging to the same base file from multiple processes.

For multi‑process apps, use:

```
logs/app_worker_1.log
logs/app_worker_2.log
...
```

---

## Color & Gradient Performance  
Color output is fast.  
Gradients are slower due to per‑character ANSI generation.

### Solid colors
- negligible overhead  

### Gradients
- 5–20× slower than solid colors  
- still fast enough for banners, headers, and occasional use  
- not recommended for high‑volume logs  

Gradients should be used sparingly in production.

---

## Memory Usage  
LogSmith is lightweight:

- no global buffers  
- no background threads (sync)  
- one worker task + queue (async)  
- minimal allocations during formatting  

Async queue memory depends on backlog size.

---

## 🧠 Best Practices

- use async logging for high‑volume workloads  
- minimize rotation frequency (by using smart time/size based rotation rules)  
- avoid logging large objects or payloads  
- prefer NDJSON over indented JSON for ingestion pipelines  
- avoid excessive structured fields
- avoid multi‑process writes to the same base file on Windows  
- minimize the use of gradients in log files
- flush async loggers before shutdown  

---

## Summary  

Performance & Optimization in LogSmith provides tools and strategies for:

- high throughput
- predictable latency
- rotation optimization
- minimal lock contention
- high sync and async performance
- concurrency‑safe behavior
- low memory usage

With proper tuning, LogSmith can handle extremely high log volumes while remaining fast, predictable, and safe.
