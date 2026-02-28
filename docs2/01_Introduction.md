# Introduction  
*A modern logging toolkit for developers who want clarity, structure, and expressive output.*

LogSmith is a logging framework built for developers who care about both **readability** and **reliability**. It takes Python’s built‑in `logging` module — a solid but aging foundation — and layers on the features modern applications actually need: structured logs, color and gradients, async support, safe rotation, JSON/NDJSON, themes, and a predictable, explicit API.

This chapter gives you a high‑level understanding of what LogSmith is, why it exists, and how it fits into real‑world applications.

---

## What LogSmith Solves

Python’s standard logging module is powerful but low‑level. It leaves many practical needs to the developer:

- How do I get readable, structured logs without writing format strings everywhere?
- How do I get color output that doesn’t bleed or break?
- How do I rotate logs safely across threads or processes?
- How do I log JSON or NDJSON without hand‑rolling serializers?
- How do I capture *all* logs from *all* loggers into one audit file?
- How do I log asynchronously without losing ordering?
- How do I add new log levels with custom colors?
- How do I avoid the “logger soup” that happens in large applications?

LogSmith answers all of these with a unified, consistent design.

---

## The LogSmith Philosophy

LogSmith is built around a few core principles:

### **1. Explicit is better than implicit**
Nothing happens behind your back.  
You attach handlers explicitly.  
You choose formatting explicitly.  
You enable auditing explicitly.

### **2. Structure first, color second**
Color is great for humans.  
Structure is essential for machines.  
LogSmith gives you both — without mixing concerns.

### **3. Async and sync should feel the same**
SmartLogger (sync) and AsyncSmartLogger (async) share the same API and formatting model.  
If you know one, you know the other.

### **4. Rotation must be safe**
Rotation is notoriously tricky.  
LogSmith’s rotation handlers are:

- thread‑safe  
- process‑safe  
- atomic  
- predictable  

Async rotation is handled in a worker thread so your event loop stays clean.

### **5. Logging should be expressive**
Gradients, themes, raw ANSI output, palette blending — these are tools for developers who want their logs to *communicate*, not just print.

---

## Where LogSmith Fits

LogSmith is ideal for:

- CLI tools  
- Services and daemons  
- Multi‑threaded applications  
- Async applications  
- Multi‑process workloads (with per‑process files)  
- Debugging utilities  
- Data pipelines (NDJSON)  
- Developer tools  
- Anything that benefits from readable, structured logs  

It is **not** a replacement for distributed logging systems like ELK, Loki, or Datadog — but it integrates beautifully with them via JSON/NDJSON.

---

## SmartLogger vs AsyncSmartLogger

LogSmith provides two logger types:

### **SmartLogger (sync)**  
For traditional Python applications, scripts, CLIs, and multi‑threaded workloads.

### **AsyncSmartLogger (async)**  
For asyncio‑based applications, servers, bots, and high‑throughput async pipelines.

Both support:

- console logging  
- file logging  
- rotation  
- structured formatting  
- themes  
- dynamic levels  
- auditing  
- raw output  
- JSON/NDJSON  

The async version adds:

- queue‑based logging  
- ordering guarantees  
- async rotation scheduling  
- a_stdout() for synchronized printing  

---

## What You Can Expect From the Rest of the Documentation

The remaining chapters walk through LogSmith from the ground up:

- Installation  
- Quickstart  
- Console logging  
- File logging  
- Rotation  
- JSON/NDJSON  
- Async logging  
- Structured formatting  
- Themes and gradients  
- Auditing  
- Dynamic levels  
- Hierarchy  
- Lifecycle  
- Diagnostics  
- Performance  
- Best practices  
- Full examples  
- API reference  

Each chapter is practical, example‑driven, and written for developers who want to understand *how things work* and *why they work that way*.

---

LogSmith is designed to make your logs clearer, safer, and more expressive — without adding complexity.  
The next chapter covers installation and setup so you can start using it immediately.
