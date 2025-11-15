# CURSOR Master Template — MOBY Platform (v1)

Cursor PRO must follow these project-wide rules for all code generation:

---

# 📦 Project Summary
MOBY is an Industrial IoT Predictive Maintenance platform.  
Key components:
- Raspberry Pi edge nodes (multi-sensor)
- MQTT → FastAPI backend → InfluxDB
- Grafana dashboards
- Alert engine + LLM summaries
- React/Vite frontend with alert UI

Cursor is responsible for **file-level programming**:
- Writing code files
- Refactoring
- Fixing errors
- Creating new modules
- Maintaining folder structure
- Implementing designs created by Gemini CLI

---

# 📁 Required Folder Structure
Cursor must respect and maintain this structure:

backend/
api/
services/
schemas/
core/
models/

frontend/
src/
components/
pages/
services/
context/
hooks/
utils/

docs/
MASTER_PROMPT_TEMPLATE_v2.md
MASTER_PROMPT_TEMPLATE_GEMINI_v1.md
WORKFLOW_GEMINI_CURSOR_MASTER_v1.md


---

# 🔧 Backend Rules
- Use FastAPI
- Every route → routes_xxx.py
- Business logic → services/
- Data models → schemas/
- Shared logic → core/ & models/
- Keep folder boundaries strict

---

# 🎨 Frontend Rules
- React + Vite + shadcn/ui
- Every UI component → reusable
- Alerts follow:
  - toast + alert panel
  - fade-in / fade-out animation
- WebSocket client auto-handles alerts

---

# 🧠 LLM / Alert Rules
- LLM summary requested only for REAL alerts
- Alert lifecycle:
  `pending → active → acknowledged → resolved`
- Vector anomaly model format:

{ type: "MLP_composite", vector: [0.4,0.33], vector_mag: 0.52 }

---

# ⚙️ Code Quality Requirements
- Python: type hints, docstrings, modular
- JS/TS: ES modules, clean exports, no inline CSS
- Never mix responsibilities
- Always check existing files before generating new ones

---

# 🔥 Cursor Behavior Model
When I ask “코드 생성해줘” or “자동 생성”, Cursor must:
1. Detect correct folder
2. Create proper files with correct names
3. Follow project architecture & naming rules
4. Avoid duplicate folders (never create backend2, services2 etc.)
5. Show diff preview before applying

---

# 🚀 Integration with Gemini
Cursor must accept instructions produced by:
- `MASTER_PROMPT_TEMPLATE_GEMINI_v1.md`
- `WORKFLOW_GEMINI_CURSOR_MASTER_v1.md`

Gemini = system architect  
Cursor = file-level builder

Cursor must always implement Gemini’s designs exactly.

---

# 💬 Response Format
Cursor should:
- Generate clean diffs
- Explain decisions briefly
- Ask for confirmation only when risky
