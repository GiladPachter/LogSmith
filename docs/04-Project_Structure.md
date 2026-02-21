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
│   ├── 01_basic_logging.py                   # getting started with LogSmith
│   ├── 02_formatting_demo.py                 # formatting log entry structure
│   ├── 03_file_output_demo.py                # logger file handlers
│   ├── 04_rotation_demo.py                   # time & size based log file rotation
│   ├── 05_hierarchy_demo.py                  # logger hierarch for controlling logging levels in groups
│   ├── 06_auditing_demo.py                   # auditing the activity of all loggers into one central log
│   ├── 07_gradient_demo.py                   # color gradients with LogSmith color tools
│   ├── 08_stress_test.py                     # verification that concurrency holds up under extreme conditions
│   ├── 09_themes_demo.py                     # assigning alternative level-based colors to logs in console
│   ├── 10_removing_handlers_from_loggers.py  # demonstrating that resulting logs meet expectations
│   ├── 11_misc_issues_demo.py                # some more informative LogSmith tools and error-prevention mechanisms
│
├── LogSmith/
│   ├── __init__.py             # Project's entity publishing
│   ├── colors.py               # CPrint color engine + gradients + palettes
│   ├── formatter.py            # StructuredPlainFormatter, StructuredColorFormatter, AuditFormatter
│   ├── level_registry.py       # LEVELS registry (dynamic log levels)
│   ├── levels.py               # LevelStyle + TRACE definition
│   ├── py.typed                # package building indicator
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
├── classes_MyProject.png       # classe diagram
├── project_definitions.py      # defines ROOT_DIR at current
├── packages_MyProject.png      # packages diagram
├── project_definitions.py      # project globals
├── pyproject.toml              # packaging info
├── README.md                   # the main menu of all docs of this project
```

## This structure ensures:
- **Core logic is isolated** in `SmartLogger/`
- **Demonstrations are complete and runnable** in `examples/`
- **Packaging is clean** via `pyproject.toml`
- **No dependencies on external packages** &nbsp; — &nbsp; everything is pure Python
