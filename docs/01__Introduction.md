# 📘 Introduction  
*A modern logging toolkit for developers who want clarity, structure, and expressive output.*

LogSmith is a logging framework built for developers who care about both **readability** and **reliability**.<br/>
It takes Python’s built‑in `logging` module — a solid but aging foundation — and layers on the features modern applications actually need:

✔ Structured Logs  
✔ Color & Gradients  
✔ Safe Rotation & Retention  
✔ Async support  
✔ JSON / NDJSON  
✔ Themes  
✔ Predictable, explicit API  

This chapter gives you a high‑level understanding of what LogSmith is, why it exists, and how it fits into real‑world applications.

---

## 🧮 What LogSmith Solves

Python’s standard logging module is powerful but low‑level. It leaves many practical needs to the developer:

- How do I get readable, structured logs without having to deal with logging format string?
- How do I get rich color output that doesn’t bleed or break?
- How do I rotate logs safely across threads?
- How do I log JSON or NDJSON without hand‑rolling serializers?
- How do I capture logs from *all* loggers into one audit file?
- How do I log asynchronously without losing ordering?
- How do I add new log levels with custom colors?
- How do I avoid the “logger soup” that happens in large applications?

LogSmith answers all of these and more with a unified, consistent design.

---

## 🧠 The LogSmith Philosophy

LogSmith is built around a few core principles:

### 🔹 Explicit is better than implicit
Nothing happens behind your back.  
You attach handlers explicitly.  
You choose formatting explicitly.  
You enable auditing explicitly.

### 🔹 Structure first, color second
Color is great for humans.  
Structure is essential for machines.  
LogSmith gives you both — without mixing concerns.

### 🔹 Async and sync should feel the same
SmartLogger (sync) and AsyncSmartLogger (async) share the same API and formatting model.  
If you know one, you know the other.

### 🔹 Rotation must be safe
Rotation is notoriously tricky.  
LogSmith’s rotation handlers are:

- thread‑safe  
- atomic  
- predictable  

Async rotation is handled in a worker thread so your event loop stays clean.

### 🔹 Logging should be expressive**
Gradients, themes, raw ANSI output, palette blending — these are tools for developers who want their logs to *communicate*, not just print.

---

## 🧩 Where LogSmith Fits

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

It is **not** a replacement for distributed logging systems like ELK, Loki, or Datadog — but it integrates beautifully with them via JSON / NDJSON.

---

## 🔄 SmartLogger vs AsyncSmartLogger

LogSmith provides two logger types:

### **SmartLogger (sync)**  
For traditional Python applications, scripts, CLIs, and multi‑threaded workloads.

### **AsyncSmartLogger (async)**  
For asyncio‑based applications, servers, bots, and high‑throughput async pipelines.

Both support:

- console logging  
- file logging  
- rotation & retention
- structured formatting  
- themes  
- dynamic levels  
- auditing  
- raw output  
- JSON / NDJSON  

The async version adds:

- queue‑based logging  
- ordering guarantees  
- async rotation scheduling  
- a_stdout() for synchronized printing  

---

## ❓ What You Can Expect From the Rest of the Documentation

The remaining chapters walk through LogSmith from the ground up:

- Installation  
- Quickstart  
- Console logging  
- File logging  
- Rotation  
- JSON / NDJSON  
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

LogSmith is designed to make your logs clearer, safer, and more expressive — and at the same time making powerful logging a child's play.  
