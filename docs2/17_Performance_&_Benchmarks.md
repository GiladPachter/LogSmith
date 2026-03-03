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

## Rotation Overhead
Rotation is designed to be safe and efficient:

- atomic renaming (`os.replace`)  
- minimal blocking  
- async rotation offloaded to thread pool  
- concurrency‑safe locks  
- retention checks optimized  

Rotation overhead is typically:

- **sync:** 0.1–3 ms depending on file size  
- **async:** 0.1–1 ms (event loop unaffected)  

Rotation frequency has a much larger impact than rotation cost.

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

## File I/O Performance  
File writes are buffered and efficient.

Performance depends on:

- disk speed  
- filesystem  
- rotation frequency  
- sanitization settings  

ANSI sanitization adds a small overhead (~1–3 µs per log).

---

## Async Queue Performance  
AsyncSmartLogger uses an asyncio queue:

- enqueue is extremely fast  
- worker processes logs in batches  
- rotation happens in worker thread  
- ordering is preserved  

Queue size can be inspected via:

```python
logger.describe()
```

If queue grows too large:

- increase worker throughput (fewer JSON logs)  
- reduce rotation frequency  
- reduce structured field complexity  

---

## Multi‑Threaded Performance  
SmartLogger is thread‑safe:

- per‑handler locks  
- atomic rotation  
- safe concurrent writes  

Performance scales well across threads, but:

- too many threads writing simultaneously can increase contention  
- async logging avoids this entirely  

---

## Multi‑Process Performance  
LogSmith supports multi‑process logging with caveats:

- safe on Unix (fcntl locks)  
- safe on Windows only if each process writes to its own base file  
- rotation is atomic across processes  
- retention is safe  

For multi‑process apps, use:

```
logs/app_worker_1.log
logs/app_worker_2.log
...
```

---

## Memory Usage  
LogSmith is lightweight:

- no global buffers  
- no background threads (sync)  
- one worker task + queue (async)  
- minimal allocations during formatting  

Async queue memory depends on backlog size.

---

## Performance Best Practices  
- prefer NDJSON for structured logs  
- avoid gradients in high‑volume logs  
- minimize rotation frequency  
- avoid attaching too many handlers  
- use async logging for servers  
- use per‑process log files on Windows  
- avoid extremely large structured fields  
- flush async loggers before shutdown  

---

## Summary  
LogSmith delivers:

- high throughput  
- predictable latency  
- safe rotation  
- efficient JSON / NDJSON  
- async and sync performance tuning  
- concurrency‑safe behavior  
- low memory usage  

The next chapter covers **Best Practices**, summarizing recommended patterns for real‑world applications.
