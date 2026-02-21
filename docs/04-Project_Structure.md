# 🗂️ Project Structure

LogSmith is organized into a clean, modular package layout.</br>
Each module has a clear responsibility, making the system easy to understand, extend, and maintain.

```
LoggerEx/
│
├── docs/
│   ├── . . .
│   ├── *  (31 '.md' files) # all documentation of this project
│   ├── . . .
│
├── examples/
│   ├── __init__.py
│   ├── auditing_demo.py        # Global auditing + rotation
│   ├── basic_console.py        # Basic usage, dynamic levels, raw output
│   ├── gradient_demo.py        # Full gradient + palette demonstration
│   ├── hierarchy_demo.py       # Logger hierarchy + inheritance
│   ├── retention_demo.py       # Retention policies + expiration rules
│   ├── stress_test.py          # Multi-threaded stress test
│   ├── themes_demo.py          # Theme switching demonstration
│
├── LogSmith/
│   ├── __init__.py             # Project's entity publishing
│   ├── colors.py               # CPrint color engine + gradients + palettes
│   ├── formatter.py            # StructuredPlainFormatter, StructuredColorFormatter, AuditFormatter
│   ├── levels.py               # LevelStyle + TRACE definition
│   ├── level_registry.py       # LEVELS registry (dynamic log levels)
│   ├── rotation.py             # RotationLogic + retention + concurrency-safe handler
│   ├── SmartLogger.py          # Core LogSmith implementation
│   ├── themes.py               # Built-in themes (light, dark, neon, pastel)
│
├── tools/
│   ├── build_wheel.py          # Packaging helper
│   ├── install_build_tools.py  # one-time use script for installing Packaging tools
│
├── __init__.py
├── LICENSE                     # Description of the MIT License
├── project_definitions.py      # defines ROOT_DIR at current
├── pyproject.toml              # Build metadata + version + dependencies
├── README.md                   # the main menu of all docs of this project
```

## This structure ensures:
- **Core logic is isolated** in `SmartLogger/`
- **Demonstrations are complete and runnable** in `examples/`
- **Packaging is clean** via `pyproject.toml`
- **No dependencies on external packages** &nbsp; — &nbsp; everything is pure Python
