# SmartLogger

A modern, expressive, high‑performance logging library for Python.

---

For a quick feel & touch of how to harness the full strength of smartlogger package, examine and execute the demo modules under LoggerEx\examples\ 

---

## 📚 Documentation

All documentation is available in the `docs/` directory:

- [1. Overview](                     docs/01-Overview.md )
- [2. Installation](                 docs/02-Installation.md )
- [3. Quickstart](                   docs/03-Quick_Start.md )
- [4. Project Structure](            docs/04-Project_Structure.md )
- [5. Core Concepts](                docs/05-Core_Concepts.md )
- [6. Console Logging](              docs/06-Console_Logging.md )
- [7. File Logging](                 docs/07-File_Logging.md )
- [8. Rotation Logic](               docs/08-Rotation_Logic.md )
- [9. Auditing](                     docs/09-Auditing.md )
- [10. Structured Formatting](       docs/10-Structured_Formatting.md )
- [11. Colors & Gradient System](    docs/11-Colors_&_Gradient_System.md )
- [12. Custom Log Levels](           docs/12-Custom_Log_Levels.md )
- [13. Themes](                      docs/13-Themes.md )
- [14. Logger Hierarchy](            docs/14-Logger_Hierarchy.md )
- [15. Logger Lifecycle](            docs/15-Logger_Lifecycle.md )
- [16. Extras & Structured Fields](  docs/16-Extras_&_Structured_Fields.md )
- [17. Exceptions & Diagnostics](    docs/17-Exceptions_&_Diagnostics.md )
- [18. Performance & Efficiency](    docs/18-Performance_&_Efficiency.md )
- [19. Best Practices & Patterns](   docs/19-Best_Practices_&_Patterns.md )
- [20. Full Examples](               docs/20-Full_Examples.md )
- [21. API Reference Overview](      docs/21-API_Reference_Overview.md )
- [22. Changelog](                   docs/22-Changelog.md )
- [23. Roadmap](                     docs/23-Roadmap.md )
- [24. License](                     docs/24-License.md )
- [25. FAQ](                         docs/25-FAQ.md )
- [26. Troubleshooting](             docs/26-Troubleshooting.md )
- [27. Contributing](                docs/27-Contributing.md )
- [28. Security Notes](              docs/28-Security_Notes.md )
- [29. Versioning](                  docs/29-Versioning.md )
- [30. Examples Gallery](            docs/30-Examples_Gallery.md )
- [31. SmartLogger Philosophy](      docs/31-SmartLogger_Philosophy.md )

---

## 🔧 Building & Installing the Wheel (.whl)
For installing the Package Builder (a one-time operation), execute from the project tree:
```
`tools/install_build_tools.py`
```

For building the package, execute from the project tree.
```
`tools/build_wheel.py`
```
Now you have generated the `.whl`<br/>
So if the current project version is 1.7.0, then you have produced:
```
`dist/logsmith-1.7.0-py3-none-any.whl`
```
which you can pip install at your convenience.


---

## 🔧 Classes diagram & Packages diagram

1. pip install `pylint`
2. install `graphviz` from https://graphviz.org/download/  (choose `add to PATH` &nbsp; - &nbsp; curren userr or all)
3. restart PyCharm.
4. run the following command from (active) terminal: `python -m pylint.pyreverse.main -o png -p MyProject .`
5. result images: `classes_MyProject.png` , `packages_MyProject.png`
