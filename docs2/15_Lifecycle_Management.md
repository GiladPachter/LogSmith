# 🔄 Lifecycle Management

LogSmith gives you explicit control over the entire lifecycle of a logger: creation, configuration, retirement, destruction, and safe shutdown. This chapter explains how loggers live, how they die, and how to manage them cleanly in both synchronous and asynchronous applications.

---

## 💡 Why Lifecycle Management Matters

Large applications often need to:

- recreate loggers with the same name  
- temporarily disable logging  
- close file handles cleanly  
- flush async queues before shutdown  
- avoid memory leaks from unused loggers  
- reset the logging system during tests  

LogSmith provides explicit lifecycle operations to handle all of these safely.

---

## 🏗️ Logger Creation
Creating a logger is straightforward:

```python
from LogSmith import SmartLogger

logger = SmartLogger("myapp.module", level=20)
```

Loggers are created on demand. If a logger with the same name already exists, LogSmith returns the existing instance unless it has been destroyed.

Async version:

```python
from LogSmith import AsyncSmartLogger

logger = AsyncSmartLogger("myapp.async")
```

---

## 🔁 Logger Reuse

Loggers are singletons by name:

```python
a = SmartLogger("myapp.api")
b = SmartLogger("myapp.api")    # Error!
```

This ensures consistent configuration across your application and prevents accidental duplication of handlers or state.

---

## 🛑 Retiring a Logger

Retiring a logger disables it without removing it from the system:

```python
logger.retire()
```

Retirement:

- closes all handlers  
- flushes pending writes  
- disables logging methods  
- preserves the logger object for inspection  

A retired logger cannot log until reconfigured.

---

## 💥 Destroying a Logger

Destroying a logger removes it entirely:

```python
logger.destroy()
```

Destruction:

- closes handlers  
- removes the logger from the registry  
- frees memory  
- allows clean recreation with the same name  

After destruction:

```python
logger = SmartLogger("myapp.api")  # brand new logger
```

---

## 🔧 Reinitializing a Logger

To fully reset a logger:

```python
logger.destroy()
logger = SmartLogger("myapp.api")
logger.add_console()
```

This is useful in test suites, dynamic plugin systems, and long‑running services that reload configuration.

---

## 🧹 Handler Shutdown
Handlers are closed automatically when:

- a logger is retired  
- a logger is destroyed  
- the application exits cleanly  
- auditing is stopped  

Closing a handler:

- flushes buffers  
- closes file descriptors  
- releases locks  

Async handlers flush before closing.

---

## 🌀 Async Logger Shutdown

AsyncSmartLogger requires explicit flushing to guarantee ordering and durability:

```python
await logger.flush()
```

Flushing ensures that:

- all queued logs are written  
- rotation is completed  
- file handles are closed  
- worker tasks exit cleanly  

Destroying an async logger:

```python
logger.destroy()
```

This removes the logger from the registry after safely shutting down its worker.

---

## 🛑 Global Shutdown

You can shut down all loggers at once.

### Sync

```python
SmartLogger.shutdown()
```

### Async

```python
await AsyncSmartLogger.shutdown()
```

Global shutdown:

- flushes all handlers  
- closes all files  
- stops auditing  
- terminates async workers  
- clears the logger registry  

This is ideal for application exit or test teardown.

---

## 🔧 Reconfiguring Loggers at Runtime

You can reconfigure a logger at any time:

```python
logger.setLevel(10)
logger.clear_handlers()
logger.add_console()
logger.add_file(log_dir="logs", logfile_name="new.log")
```

Reconfiguration is safe and atomic. Loggers can be reshaped dynamically without restarting the application.

---

## 🗑️ Clearing Handlers

Remove all handlers from a logger:

```python
logger.remove_console()
logger.remove_file_handler(logfile_name, log_dir)
```

This does not disable the logger — it simply removes one of its output channels.

---

## 🔍 Logger Introspection

You can inspect a logger’s state:

```python
print(logger.handler_info())
print(logger.console_handler())
print(logger.file_handlers())
```

This returns:

- name  
- level  
- formatter type name
- rotation settings  
- output modes  
- theme state  
- async queue status (for async loggers)  

Introspection is essential for debugging and diagnosing configuration issues.

---

## 🧵 Lifecycle in Multi‑Process Environments

Each process has its own logger registry.<br/>
Destroying a logger in one process does not affect others.

---

## 🧠 Best Practices

- Destroy loggers during test teardown.  
- Flush async loggers before application exit.  
- Use retirement for temporary disablement.  
- Use destruction for full reset.  
- Avoid creating many short‑lived loggers — reuse names.  
- Use global shutdown for clean application termination.  

---

## 📘 Summary

Lifecycle management in LogSmith provides:

- explicit creation and reuse  
- retirement and destruction  
- handler shutdown  
- async flushing  
- global shutdown  
- safe reconfiguration  
- introspection tools  

The next chapter covers **Diagnostics & Debugging**, including how to inspect handlers, detect misconfiguration, and troubleshoot rotation or async behavior.
