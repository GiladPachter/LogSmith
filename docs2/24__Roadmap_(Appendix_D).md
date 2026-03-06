# Appendix D — 🧭 Roadmap  
A forward‑looking overview of LogSmith’s development priorities. This roadmap reflects the current state of the project and the natural next steps that strengthen stability, performance, ergonomics, and ecosystem completeness. It is intentionally concise and high‑signal, serving as a guide for contributors and users who want to understand where LogSmith is heading.

---

# Async Logging Enhancements

### **Profiling Expansion**  
Extend async profiling to include formatter cost, rotation latency, and queue wait times.

---

# Formatting & Structured Output

### **Extended OptionalRecordFields**  
Add missing metadata fields (e.g., module name) and ensure full compatibility with JSON/NDJSON output.

### **Improved Extras Handling**  
Refine extraction and rendering of structured fields, especially for nested objects and large payloads.

---

# Rotation & Retention

### **Cross‑Process Safety**  
Continue strengthening concurrency guarantees for multi‑process rotation on Unix and Windows.

---

# Auditing & Diagnostics

### **Unified Auditing Model**  
Align SmartLogger and AsyncSmartLogger auditing behavior, ensuring consistent formatting and metadata.

### **Audit Formatter Improvements**  
Enhance audit output to include richer metadata while remaining ingestion‑friendly.

### **Diagnostic Hooks**  
Introduce optional hooks for capturing internal events (rotation triggers, handler failures, queue saturation).

---

# Developer Experience

### **Improved Error Messages**  
Provide clearer exceptions for misconfiguration, invalid paths, duplicate handlers, and rotation conflicts.

### **Better Introspection Tools**  
Expose more metadata about handlers, rotation state, and logger hierarchy.

### **Documentation Expansion**  
Continue refining appendices, examples, and conceptual chapters to match the evolving API.

---

# Ecosystem & Integration

### **Third‑Party Integration Helpers**  
Optional utilities for integrating LogSmith with frameworks (FastAPI, Flask, asyncio servers, multiprocessing pools).

### **Plugin Architecture (Exploratory)**  
Long‑term idea: allow custom formatters, handlers, and themes to be registered externally.

---

# Performance & Benchmarks

### **Benchmark Suite Expansion**  
Add async‑specific benchmarks, rotation stress tests, and structured‑field performance tests.

### **Memory Profiling**  
Measure and optimize memory usage for large queues, deep structured fields, and high‑volume JSON output.

---

# Long‑Term Vision

### **Unified Logging Framework**  
Position LogSmith as a complete, modern logging solution for Python applications of all sizes.

### **Best‑in‑Class Structured Logging**  
Provide the most ergonomic and powerful structured logging experience in Python.

---

# 📘 Summary  
This roadmap outlines the next phases of LogSmith’s evolution: stabilizing the architecture, strengthening async capabilities, refining formatting and rotation, improving diagnostics, and expanding the ecosystem. The goal is to keep LogSmith fast, predictable, expressive, and production‑ready while maintaining a clean and intuitive API.
