# 🚀 Performance & Optimization

LogSmith is built for high‑volume, production‑grade logging.  
With proper configuration it can sustain tens of thousands of log events per second while keeping latency predictable and rotation safe.  
This chapter explains how to tune performance, understand cost factors, and choose the right tools for your workload.

---

## 💡 Why Performance Matters

Logging is often a hidden bottleneck. Under load it can:

- slow down request handlers  
- block event loops  
- saturate disks  
- overwhelm ingestion pipelines  
- create backpressure in async systems  

LogSmith is designed to minimize these risks through:

- low overhead per log call  
- predictable latency  
- efficient async pipelines  
- safe rotation under load  
- minimal lock contention  
- optimized formatting and string building  

The goal is rich features without sacrificing speed.

---

## ⚙️ Sync vs Async Logging

### Synchronous Logging
Writes directly to disk or stdout. Simple and predictable, but can block during:

- slow disk writes  
- rotation  
- JSON encoding  
- high‑volume bursts  

Best for:

- CLI tools  
- small scripts  
- low‑volume services  

### Asynchronous Logging
Offloads all I/O to a background worker. Benefits include:

- non‑blocking log calls  
- smoother throughput  
- better CPU utilization  
- safe rotation under load  

Recommended for:

- web servers  
- microservices  
- data pipelines  
- high‑volume batch jobs  

---

## 🧰 Handler Efficiency

Different handlers have different costs:

- **Console handler** — fastest  
- **File handler** — fast, depends on disk  
- **NDJSON handler** — moderate  
- **JSON handler** — moderate to high  
- **Audit handler** — moderate to high  
- **Raw handler** — fast, minimal processing  

Most expensive operations:

- JSON encoding  
- NDJSON generation  
- rotation under heavy load  

For maximum throughput:

- prefer NDJSON over JSON  
- avoid deep structured fields  
- avoid large multi‑line messages  
- use async logging for file handlers  

---

## 🧾 Formatter Cost

Formatter overhead grows with:

- JSON encoding  
- deep structured fields  
- exception formatting  
- stack trace extraction  
- theme rendering  

Exception formatting is the single most expensive operation in the pipeline.

For high‑volume workloads:

- avoid logging exceptions in hot loops  
- avoid large dictionaries or nested objects  
- prefer NDJSON for ingestion pipelines  

---

## 🧩 Structured Field Overhead

Structured fields add power but also cost.  
Each field must be sanitized, merged, and serialized.

Example:

```python
logger.info("User login", username="Gilad", roles=["admin", "editor"])
```

For high‑volume systems:

- keep fields shallow  
- avoid large lists or nested objects  
- avoid logging raw payloads (e.g., full HTTP bodies)  
- prefer IDs or references over full objects  

Structured logging is worth the cost, but should be used intentionally.

---

## 🔄 Rotation Performance

Rotation can become a bottleneck if misconfigured.  
To optimize:

- use async logging so rotation happens in a worker  
- increase `maxBytes` to reduce rotation frequency  
- avoid very small time intervals  
- use SSDs instead of HDDs  
- avoid rotating many loggers simultaneously  

Async rotation uses a thread pool to ensure rotation does not block the main worker.

---

## 🔓 Minimizing Lock Contention

File handlers use OS‑level locks. Contention increases when:

- multiple processes write to the same file  
- rotation triggers frequently  
- disks are slow  

To reduce contention:

- avoid multi‑process writes on Windows  
- increase rotation thresholds  
- use async logging to shorten lock durations  

Linux `fcntl` locks are efficient; Windows locks are more restrictive.

---

## 🧱 Avoiding Bottlenecks

Common bottlenecks:

- synchronous file writes  
- JSON encoding of large payloads  
- deep structured fields  
- slow disks  
- too many handlers on one logger  
- logging inside tight loops  

To minimize them:

- use async logging for file handlers  
- keep structured fields shallow  
- avoid logging large objects  
- avoid logging inside micro‑loops  
- prefer NDJSON for ingestion pipelines  

Logging should never become the slowest part of your application.

---

## 🧵 Multi‑Process Behavior

LogSmith supports multi‑process logging with important caveats:

- safe on Linux (fcntl locks)  
- safe on Windows **only** if each process writes to its own base file  
- rotation is atomic  
- retention is safe  

File handlers use OS-level locks to ensure safe writes.
Contention increases when multiple processes write to the same file
On Linux, fcntl locks are efficient, but Windows file locks are more restrictive and a lot more challenging.
LogSmith intentionally does not support multiple processes writing to the same base file on Windows.

For multi‑process apps:

```
logs/app_worker_1.log
logs/app_worker_2.log
...
```

---

## 🎨 Color & Gradient Performance

Color output is fast.  
Gradients are slower due to per‑character ANSI generation.

- **Solid colors** — negligible overhead  
- **Gradients** — 5–20× slower, still fine for banners or occasional use  
- Not recommended for high‑volume logs  

---

## 🧮 Memory Usage

LogSmith is lightweight:

- no global buffers  
- no background threads (sync)  
- one worker task + queue (async)  
- minimal allocations during formatting  

Async queue memory usage depends on backlog size.

---

## 🧠 Best Practices

- use async logging for high‑volume workloads  
- minimize rotation frequency (by using smart time/size based rotation rules)  
- avoid logging large objects or payloads  
- prefer NDJSON over indented JSON for ingestion pipelines  
- avoid excessive structured fields  
- avoid multi‑process writes to the same file on Windows  
- use gradients sparingly in log files  
- flush async loggers before shutdown  

---

## Summary

LogSmith provides tools and strategies for:

- high throughput
- predictable latency
- efficient rotation
- minimal lock contention
- safe concurrency
- low memory usage  

With proper tuning, LogSmith can handle extremely high log volumes while remaining fast, predictable, and safe.
