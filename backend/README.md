# Trade With Nilay — Backend (Phase 0 & Phase 1)

This folder contains the initial secure config template and a Phase 1 Core Data Engine prototype.

Quick start (local, dev):

1. Create/activate a Python 3.10+ virtualenv.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

2. Populate secrets: edit `backend/config/keys.env` (DO NOT COMMIT real keys).

3. Add a symbol list to `backend/database/symbols.txt` (one symbol per line). For NSE append `.NS` to symbols (e.g. `TCS.NS`).

4. Initialize DB and run one fetch:

```powershell
python -c "from backend.database.db import init_db; init_db()"
python -m backend.scripts.run_fetcher
```

Notes:
- This is an extensible, modular foundation. For production you should run the `run_fetcher.py` in a Docker container or systemd service, secure `keys.env` via your cloud provider secrets, and scale connectors to use proper market data providers.
