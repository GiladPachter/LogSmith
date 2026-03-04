# 📘 LogSmith  
*A modern, expressive logging framework for Python — with structure, color, gradients, async support, and rock‑solid rotation.*

LogSmith takes Python’s built‑in `logging` module and gives it the features developers actually want:

- Structured, user-friendly log message formatting
- Colored messages, color themes and gradient console output  
- Size‑based and time‑based rotation - intermixed when useful
- Thread‑safe and process‑safe file handlers  
- Retention policies  
- Global auditing mode  
- Dynamic log levels  
- JSON and NDJSON modes  
- Async logging with ordering guarantees  
- Raw ANSI output  
- Predictable, explicit behavior  

It’s designed for CLI tools, services, daemons, debugging utilities, and any application that benefits from clean, expressive logs.

---

## 💡 Why LogSmith?

Python’s standard logging module is powerful but low‑level.  
Rich is beautiful but not built for structured logging or rotation.  
structlog is structured but not color‑first or rotation‑aware.

LogSmith combines the strengths of all three:

- Like Python logging → familiar API, handlers, levels, propagation rules  
- Like Rich → expressive color output, gradients, themes  
- Like structlog → structured fields, JSON / NDJSON, predictable formatting  
- Unlike all of them →  
  - async logging engine  
  - concurrency‑safe rotation  
  - raw ANSI output  
  - gradient engine  
  - dynamic log levels  
  - unified formatting model
  - perfect logging and non-logging console output synchronization

If you want logs that are both beautiful and machine‑friendly, LogSmith is built for you.

---

## 📚 Documentation

Full documentation is available in the `docs/` directory on GitHub:

- [1. Overview](                    https://github.com/GiladPachter/LogSmith/blob/main/docs/01-Overview.md)
- [2. Installation](                https://github.com/GiladPachter/LogSmith/blob/main/docs/02-Installation.md)
- [3. Quickstart](                  https://github.com/GiladPachter/LogSmith/blob/main/docs/03-Quick_Start.md)
- [4. Project Structure](           https://github.com/GiladPachter/LogSmith/blob/main/docs/04-Project_Structure.md)
- [5. Core Concepts](               https://github.com/GiladPachter/LogSmith/blob/main/docs/05-Core_Concepts.md)
- [6. Console Logging](             https://github.com/GiladPachter/LogSmith/blob/main/docs/06-Console_Logging.md)
- [7. File Logging](                https://github.com/GiladPachter/LogSmith/blob/main/docs/07-File_Logging.md)
- [8. Rotation Logic](              https://github.com/GiladPachter/LogSmith/blob/main/docs/08-Rotation_Logic.md)
- [9. Auditing](                    https://github.com/GiladPachter/LogSmith/blob/main/docs/09-Auditing.md)
- [10. Structured Formatting](      https://github.com/GiladPachter/LogSmith/blob/main/docs/10-Structured_Formatting.md)
- [11. Colors & Gradient System](   https://github.com/GiladPachter/LogSmith/blob/main/docs/11-Colors_%26_Gradient_System.md)
- [12. Custom Log Levels](          https://github.com/GiladPachter/LogSmith/blob/main/docs/12-Custom_Log_Levels.md)
- [13. Themes](                     https://github.com/GiladPachter/LogSmith/blob/main/docs/13-Themes.md)
- [14. Logger Hierarchy](           https://github.com/GiladPachter/LogSmith/blob/main/docs/14-Logger_Hierarchy.md)
- [15. Logger Lifecycle](           https://github.com/GiladPachter/LogSmith/blob/main/docs/15-Logger_Lifecycle.md)
- [16. Extras & Structured Fields]( https://github.com/GiladPachter/LogSmith/blob/main/docs/16-Extras_%26_Structured_Fields.md)
- [17. Exceptions & Diagnostics](   https://github.com/GiladPachter/LogSmith/blob/main/docs/17-Exceptions_%26_Diagnostics.md)
- [18. Performance & Efficiency](   https://github.com/GiladPachter/LogSmith/blob/main/docs/18-Performance_%26_Efficiency.md)
- [19. Best Practices & Patterns](  https://github.com/GiladPachter/LogSmith/blob/main/docs/19-Best_Practices_%26_Patterns.md)
- [20. Full Examples](              https://github.com/GiladPachter/LogSmith/blob/main/docs/20-Full_Examples.md)
- [21. API Reference Overview](     https://github.com/GiladPachter/LogSmith/blob/main/docs/21-API_Reference_Overview.md)
- [22. Changelog](                  https://github.com/GiladPachter/LogSmith/blob/main/docs/22-Changelog.md)
- [23. Roadmap](                    https://github.com/GiladPachter/LogSmith/blob/main/docs/23-Roadmap.md)
- [24. License](                    https://github.com/GiladPachter/LogSmith/blob/main/docs/24-License.md)
- [25. FAQ](                        https://github.com/GiladPachter/LogSmith/blob/main/docs/25-FAQ.md)
- [26. Troubleshooting](            https://github.com/GiladPachter/LogSmith/blob/main/docs/26-Troubleshooting.md)
- [27. Contributing](               https://github.com/GiladPachter/LogSmith/blob/main/docs/27-Contributing.md)
- [28. Security Notes](             https://github.com/GiladPachter/LogSmith/blob/main/docs/28-Security_Notes.md)
- [29. Versioning](                 https://github.com/GiladPachter/LogSmith/blob/main/docs/29-Versioning.md)
- [30. Examples Gallery](           https://github.com/GiladPachter/LogSmith/blob/main/docs/30-Examples_Gallery.md)
- [31. SmartLogger Philosophy](     https://github.com/GiladPachter/LogSmith/blob/main/docs/31-SmartLogger_Philosophy.md)

---

## 🔧 Building & Installing the Wheel (.whl)

To install the package builder (one‑time setup):

```
python tools/install_build_tools.py
```

To build the wheel:

```
python tools/build_wheel.py
```

This produces a `.whl` file under `dist/`.

For example, for version `1.7.0`:

```
dist/logsmith-1.7.0-py3-none-any.whl
```

Install locally:

```
pip install dist/logsmith-1.7.0-py3-none-any.whl
```

---

## 🔧 Class & Package Diagrams

1. Install `pylint`
2. Install Graphviz from https://graphviz.org/download/ (ensure “Add to PATH” is selected)
3. Restart PyCharm
4. Run:

```
python -m pylint.pyreverse.main -o png -p MyProject .
```

5. Output files:

- `classes_MyProject.png`
- `packages_MyProject.png`