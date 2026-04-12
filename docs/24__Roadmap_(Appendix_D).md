# Appendix D — 🧭 Roadmap
A forward‑looking overview of LogSmith’s development priorities. This roadmap reflects the current state of the project and the natural next steps that strengthen stability, performance, ergonomics, and ecosystem completeness. It is intentionally concise and high‑signal, serving as a guide for contributors and users who want to understand where LogSmith is heading.

---

# Async Logging Enhancements

### **Profiling Expansion**
Extend async profiling to include formatter cost, rotation latency, queue wait times, and worker scheduling overhead.

### **Worker Health Monitoring**
Expose worker‑alive status, last‑error state, and rotation‑debounce diagnostics.

### **Queue Backpressure Controls**
Optional soft limits, warnings, and adaptive throttling for extreme workloads.

---

# Formatting & Structured Output

### **Extended OptionalRecordFields**
Add missing metadata fields (e.g., process uptime, monotonic timestamps) and ensure full compatibility with JSON/NDJSON output.

### **Improved Extras Handling**
Refine extraction and rendering of structured fields (`named_args`), especially for nested objects and large payloads.

### **Stable JSON/NDJSON Schema**
Define a strict schema for ingestion pipelines to ensure long‑term compatibility.

---

# Auditing & Diagnostics

### **Unified Auditing Model**
Align SmartLogger and AsyncSmartLogger auditing behavior, ensuring consistent formatting, metadata, and lifecycle (`terminate_auditing`).

### **Audit Formatter Improvements**
Enhance audit output to include richer metadata while remaining ingestion‑friendly.

### **Diagnostic Hooks**
Introduce optional hooks for capturing internal events (rotation triggers, handler failures, queue saturation, audit‑worker errors).

### **Hierarchy Diagnostics**
Expose parent/child relationships, invalid hierarchy states, and type‑mismatch errors.

---

# Developer Experience

### **Improved Error Messages**
Provide clearer exceptions for misconfiguration, invalid paths, duplicate handlers, hierarchy violations, and rotation conflicts.

### **Better Introspection Tools**
Expose more metadata about handlers, rotation state, logger hierarchy, and async worker health.

---

# Ecosystem & Integration

### **Third‑Party Integration Helpers**
Optional utilities for integrating LogSmith with frameworks (FastAPI, Flask, asyncio servers, multiprocessing pools).

### **Plugin Architecture (Exploratory)**
Long‑term idea: allow custom formatters, handlers, and themes to be registered externally.

### **Cloud‑Native Helpers**
Optional helpers for Kubernetes, systemd, Docker, and container‑friendly logging patterns.

---

# Performance & Benchmarks

### **Benchmark Suite Expansion**
Add async‑specific benchmarks, rotation stress tests, and structured‑field performance tests.

### **Memory Profiling**
Measure and optimize memory usage for large queues, deep structured fields, and high‑volume JSON output.

### **Rotation Stress Testing**
Simulate extreme rotation conditions (multi‑GB logs, rapid rotation triggers, multi‑process workloads).

---

# Long‑Term Vision

### **Unified Logging Framework**
Position LogSmith as a complete, modern logging solution for Python applications of all sizes.

### **Best‑in‑Class Structured Logging**
Provide the most ergonomic and powerful structured logging experience in Python.

### **Full Sync/Async Parity**
Ensure SmartLogger and AsyncSmartLogger share identical features, formatting, and lifecycle semantics.

---

# 📘 Summary
This roadmap outlines the next phases of LogSmith’s evolution: stabilizing the architecture, strengthening async capabilities, refining formatting and rotation, improving diagnostics, and expanding the ecosystem. The goal is to keep LogSmith fast, predictable, expressive, and production‑ready while maintaining a clean and intuitive API.
