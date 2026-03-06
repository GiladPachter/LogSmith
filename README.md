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

[Table_of_Contents](                             https://github.com/GiladPachter/LogSmith/blob/main/docs/00__Table_of_Contents.md)
- [1.  Introduction](                            https://github.com/GiladPachter/LogSmith/blob/main/docs/01__Introduction.md)
- [2.  Installation_&_Setup](                    https://github.com/GiladPachter/LogSmith/blob/main/docs/02__Installation_&_Setup.md)
- [3.  QuickstartStructure](                     https://github.com/GiladPachter/LogSmith/blob/main/docs/03__Quickstart.md)
- [4.  Core_ConceptsConcepts](                   https://github.com/GiladPachter/LogSmith/blob/main/docs/04__Core_Concepts.md)
- [5.  Console_LoggingLogging](                  https://github.com/GiladPachter/LogSmith/blob/main/docs/05__Console_Logging.md)
- [6.  File_LoggingLogging](                     https://github.com/GiladPachter/LogSmith/blob/main/docs/06__File_Logging.md)
- [7.  Structured_FormattingLogic](              https://github.com/GiladPachter/LogSmith/blob/main/docs/07__Structured_Formatting.md)
- [8.  JSON_&_NDJSON_Logging](                   https://github.com/GiladPachter/LogSmith/blob/main/docs/08__JSON_&_NDJSON_Logging.md)
- [9.  AsyncSmartLoggerFormatting](      		 https://github.com/GiladPachter/LogSmith/blob/main/docs/09__AsyncSmartLogger.md)
- [10. Rotation_&_Retention& Gradient System](   https://github.com/GiladPachter/LogSmith/blob/main/docs/10__Rotation_&_Retention.md)
- [11. Themes_&_Color_SystemLog Levels](         https://github.com/GiladPachter/LogSmith/blob/main/docs/11__Themes_&_Color_System.md)
- [12. Auditing](                                https://github.com/GiladPachter/LogSmith/blob/main/docs/12__Auditing.md)
- [13. Dynamic_Log_LevelsHierarchy](             https://github.com/GiladPachter/LogSmith/blob/main/docs/13__Dynamic_Log_Levels.md)
- [14. Logger_HierarchyLifecycle](               https://github.com/GiladPachter/LogSmith/blob/main/docs/14__Logger_Hierarchy.md)
- [15. Lifecycle_Management& Structured Fields]( https://github.com/GiladPachter/LogSmith/blob/main/docs/15__Lifecycle_Management.md)
- [16. Diagnostics_&_Debugging& Diagnostics](    https://github.com/GiladPachter/LogSmith/blob/main/docs/16__Diagnostics_&_Debugging.md)
- [17. Performance_&_Benchmarks& Efficiency](    https://github.com/GiladPachter/LogSmith/blob/main/docs/17__Performance_&_Benchmarks.md)
- [18. Best_PracticesPractices & Patterns](      https://github.com/GiladPachter/LogSmith/blob/main/docs/18__Best_Practices.md)
- [19. Examples_&_RecipesExamples](              https://github.com/GiladPachter/LogSmith/blob/main/docs/19__Examples_&_Recipes.md)
- [20. Security_NotesReference Overview](        https://github.com/GiladPachter/LogSmith/blob/main/docs/20__Security_Notes.md)
- [21. API_Reference_(Appendix_A)](              https://github.com/GiladPachter/LogSmith/blob/main/docs/21__API_Reference_(Appendix_A).md)
- [22. Glossary_(Appendix_B)](                   https://github.com/GiladPachter/LogSmith/blob/main/docs/22__Glossary_(Appendix_B).md)
- [23. Changelog_(Appendix_C)](                  https://github.com/GiladPachter/LogSmith/blob/main/docs/23__Changelog_(Appendix_C).md)
- [24. Roadmap_(Appendix_D)](                    https://github.com/GiladPachter/LogSmith/blob/main/docs/24__Roadmap_(Appendix_D).md)
- [25. License_(Appendix_E)](                    https://github.com/GiladPachter/LogSmith/blob/main/docs/25__License_(Appendix_E).md)
- [26. Credits_(Appendix_F)](                    https://github.com/GiladPachter/LogSmith/blob/main/docs/26__Credits_(Appendix_F).md)
