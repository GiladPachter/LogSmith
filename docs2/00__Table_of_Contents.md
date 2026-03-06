# 📚 LogSmith — Complete Documentation Table of Contents

This appendix provides a complete, hierarchical overview of the entire LogSmith documentation set.<br/>
It reflects the full structure of the manual, including all chapters and appendices.

<br/>

<details>
<summary>📘 <strong>1. Introduction</strong></summary>

- What LogSmith is  
- Why LogSmith exists  
- Key features  
- Philosophy of design  
- Where LogSmith fits  
- SmartLogger vs AsyncSmartLogger  
- What to expect from the documentation  

</details>

---

<details>
<summary>⚙️ <strong>2. Installation & Setup</strong></summary>

- Requirements  
- Installing LogSmith (wheel / editable)  
- Building the wheel  
- Verifying installation  
- Project layout  
- Initialization requirements  
- Class & package diagrams  
- Platform notes  

</details>

---

<details>
<summary>🚀 <strong>3. Quickstart</strong></summary>

- First logger (sync)  
- First logger (async)  
- Adding a file handler  
- Structured fields  
- JSON & NDJSON logging  
- Raw output  
- Dynamic log levels  
- Themes  
- stdout() / a_stdout()  
- Summary  

</details>

---

<details>
<summary>🏛️ <strong>4. Core Concepts</strong></summary>

- Structured events  
- LogRecordDetails  
- Output modes  
- Handlers  
- Rotation logic  
- Retention policies  
- Structured fields  
- Color engine & gradients  
- Themes  
- Dynamic levels  
- Hierarchy  
- Auditing  
- Raw output  
- Async logging model  
- Logger lifecycle  

</details>

---

<details>
<summary>💻 <strong>5. Console Logging</strong></summary>

- Adding a console handler  
- Basic console output  
- Structured console output  
- Custom formatting  
- Structured fields  
- Raw console output  
- Gradient output  
- Themes  
- Output modes  
- Handler introspection  
- stdout() synchronized printing  

</details>

---

<details>
<summary>📝 <strong>6. File Logging</strong></summary>

- Adding file handlers  
- Output modes  
- ANSI sanitization  
- Structured file formatting  
- Rotation logic  
- Size‑based rotation  
- Time‑based rotation  
- Combined rotation  
- Retention policies  
- Concurrency‑safe rotation  
- Async file logging  
- Handler introspection  

</details>

---

<details>
<summary>🧱 <strong>7. Structured Formatting</strong></summary>

- Why structured formatting matters  
- LogRecordDetails  
- OptionalRecordFields  
- Field ordering  
- Separator  
- Coloring rules  
- Structured fields  
- Exception formatting  
- JSON formatting  
- NDJSON formatting  
- Raw output  
- Full formatting example  

</details>

---

<details>
<summary>{ ... } <strong>8. JSON & NDJSON Logging</strong></summary>

- Why JSON logging matters  
- Output modes  
- JSON output  
- NDJSON output  
- Structured fields  
- Exceptions in JSON  
- Customizing JSON structure  
- JSON + rotation  
- JSON + async logging  
- JSON + raw output  

</details>

---

<details>
<summary>🧵 <strong>9. AsyncSmartLogger</strong></summary>

- Why async logging matters  
- Creating an async logger  
- Async logging methods  
- Ordering guarantees  
- Worker task  
- Flushing & shutdown  
- Adding handlers  
- a_stdout()  
- Structured fields  
- Exceptions  
- Async rotation  
- Performance characteristics  
- When to use async logging  

</details>

---

<details>
<summary>♻️ <strong>10. Rotation & Retention</strong></summary>

- Why rotation matters  
- RotationLogic  
- Size‑based rotation  
- Time‑based rotation  
- Timestamp anchors  
- Hybrid rotation  
- Rotation file naming  
- Retention policies  
- Concurrency‑safe rotation  
- Rotation in AsyncSmartLogger  
- Rotation + JSON / NDJSON  
- Rotation + raw output  
- Inspecting rotation state  

</details>

---

<details>
<summary>🎭 <strong>11. Themes & Color System</strong></summary>

- Why themes matter  
- Built‑in themes  
- LevelStyle  
- Creating custom themes  
- CPrint engine  
- Gradients  
- Gradient palettes  
- Themes vs raw output  
- Themes + structured formatting  
- Themes + dynamic levels  

</details>

---

<details>
<summary>🛰️ <strong>12. Auditing</strong></summary>

- Purpose of auditing  
- How auditing works  
- Enabling auditing (sync)  
- Enabling auditing (async)  
- Audit formatter  
- Audit file rotation  
- JSON / NDJSON audit logs  
- Raw output exclusion  
- Disabling auditing  
- Auditing & hierarchy  
- Multi‑process auditing  
- When to use auditing  

</details>

---

<details>
<summary>🆕 <strong>13. Dynamic Log Levels</strong></summary>

- Why dynamic levels matter  
- Registering new levels  
- Choosing numeric values  
- Styling dynamic levels  
- Dynamic levels in async logging  
- JSON / NDJSON integration  
- Auditing integration  
- Structured fields  
- Themes + dynamic levels  
- Handler compatibility  
- Best practices  

</details>

---

<details>
<summary>🌳 <strong>14. Logger Hierarchy</strong></summary>

- How hierarchy works  
- Creating loggers in a hierarchy  
- Level inheritance  
- Handler behavior  
- Propagation & auditing  
- Logger discovery  
- Retiring / destroying loggers  
- Organizing large applications  
- Async hierarchy  
- Best practices  

</details>

---

<details>
<summary>🔄 <strong>15. Lifecycle Management</strong></summary>

- Logger creation  
- Logger reuse  
- Retiring a logger  
- Destroying a logger  
- Reinitializing a logger  
- Handler shutdown  
- Async shutdown  
- Global shutdown  
- Reconfiguring loggers  
- Clearing handlers  
- Logger introspection  
- Multi‑process behavior  
- Best practices  

</details>

---

<details>
<summary>⚠️ <strong>16. Diagnostics & Debugging</strong></summary>

- Purpose of diagnostics  
- Logger introspection  
- Handler inspection  
- Checking effective level  
- Detecting missing handlers  
- Debugging rotation  
- Debugging async behavior  
- stdout/stderr debugging  
- JSON / NDJSON debugging  
- Theme debugging  
- Auditing debugging  
- Multi‑process debugging  
- Performance diagnostics  

</details>

---

<details>
<summary>🚀 <strong>17. Performance & Benchmarks</strong></summary>

- Why performance matters  
- Sync vs async logging  
- Handler efficiency  
- Formatter cost  
- Structured field overhead  
- Rotation performance  
- Minimizing lock contention  
- Avoiding bottlenecks  
- Multi‑process behavior  
- Color & gradient performance  
- Memory usage  
- Best practices  

</details>

---

<details>
<summary>🧠 <strong>18. Best Practices</strong></summary>

- Designing a clean logging architecture  
- Choosing sync vs async  
- Handler best practices  
- Rotation & retention best practices  
- Structured fields best practices  
- JSON / NDJSON best practices  
- Theme best practices  
- Dynamic level best practices  
- Auditing best practices  
- Lifecycle best practices  
- Performance best practices  
- Testing best practices  

</details>

---

<details>
<summary>🔬🧪🧰🪄✨🔮 <strong>19. Examples & Recipes</strong></summary>

- Basic logging setup  
- File logging with rotation  
- JSON logging for ingestion  
- Structured fields  
- Custom formatting  
- Themes  
- Custom themes  
- Dynamic log levels  
- Async logging  
- Async file logging  
- Synchronized printing  
- Auditing everything  
- Level propagation  
- Exception logging  
- Raw output banners  
- Retiring/destroying loggers  
- Full logger reset  

</details>

---

<details>
<summary>🔐 <strong>20. Security Notes</strong></summary>

- Avoid logging sensitive data  
- File permissions  
- Multi‑process safety  
- Sanitizing input  
- Avoid logging secrets in exceptions  

</details>

---

# 📚 Appendices
 
- 🛠️ **Appendix A — API Reference**<br/>
<br/>

- 📖 **Appendix B — Glossary**  
<br/>  

- 📜 **Appendix C — Changelog**  
<br/>  

- 🧭 **Appendix D — Roadmap**  
<br/>  

- 📄 **Appendix E — License**  
<br/>  

- 🏅 **Appendix F — Credits**  
<br/>  

- 📚 **Appendix G — Table of Contents**  
<br/>
