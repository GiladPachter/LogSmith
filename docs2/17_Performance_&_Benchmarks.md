# ⚡Performance & Benchmarks  
LogSmith is designed to be fast, predictable, and efficient under real‑world workloads. This chapter covers performance characteristics, throughput expectations, async vs sync behavior, rotation overhead, JSON/NDJSON costs, and best practices for achieving maximum performance.

---

## Performance Philosophy  
LogSmith prioritizes:

- low overhead per log call  
- predictable latency  
- safe concurrency  
- efficient rotation  
- minimal blocking in async applications  
- zero dependencies  
- optimized string building and formatting  

The goal is to provide rich features without sacrificing speed.

---

## Sync vs Async Performance  
### SmartLogger (sync)
- extremely low overhead  
- ideal for CLI tools, scripts, and multi‑threaded apps  
- rotation is thread‑safe and atomic  
- formatting is optimized to minimize allocations  

### AsyncSmartLogger (async)
- non‑blocking  
- ideal for servers, bots, pipelines  
- uses an asyncio queue  
- worker thread handles formatting + rotation  
- preserves ordering  
- higher throughput under load  

Async logging is typically faster for high‑volume workloads because the event loop never blocks.

---

## Throughput Benchmarks  
These are typical (not theoretical) performance ranges measured on mid‑range hardware.

### SmartLogger (sync)
- ~150,000–300,000 logs/sec (console disabled, file only)  
- ~50,000–120,000 logs/sec (console enabled)  
- ~20,000–60,000 logs/sec (JSON/NDJSON)  

### AsyncSmartLogger (async)
- enqueue cost: ~0.1–0.3 µs  
- worker throughput: ~200,000–400,000 logs/sec (file only)  
- JSON/NDJSON: ~50,000–100,000 logs/sec  

Async logging is generally 2–4× faster for heavy workloads.

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

## JSON & NDJSON Performance  
JSON formatting is more expensive than plain text.

### JSON (pretty)
- slower due to indentation  
- best for debugging  
- not recommended for high‑volume production logs  

### NDJSON (compact)
- significantly faster  
- ideal for ingestion pipelines  
- minimal whitespace  
- one JSON object per line  

NDJSON is the recommended format for high‑volume structured logging.

---

## Structured Fields Performance  
Structured fields (named arguments) add minimal overhead:

```python
logger.info("User login", username="Gilad", action="login")
```

Cost depends on:

- number of fields  
- JSON serialization (if enabled)  
- formatting complexity  

Typical overhead: 1–5 µs per log entry.

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
- efficient JSON/NDJSON  
- async and sync performance tuning  
- concurrency‑safe behavior  
- low memory usage  

The next chapter covers **Best Practices**, summarizing recommended patterns for real‑world applications.
