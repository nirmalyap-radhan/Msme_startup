# Quick Execution & Run Guide for Udyog Sathi

## Instant Launch Commands

To run the project instantly without re-scanning or manual setup:

```bash
./run.sh
# OR
./build.sh
# OR
make run
```

### Server Endpoints:
- **Web Portal**: [http://localhost:8000](http://localhost:8000)
- **API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Readiness / Health Check**: [http://localhost:8000/health/ready](http://localhost:8000/health/ready)
- **Official Live Updates Feed**: [http://localhost:8000/api/v1/updates](http://localhost:8000/api/v1/updates)
- **Verified Scheme Catalogue**: [http://localhost:8000/api/v1/schemes](http://localhost:8000/api/v1/schemes)

---

## Command Flags & Options

| Command | Action |
|---|---|
| `./build.sh` or `./run.sh` | Default foreground run (prepares environment, starts uvicorn) |
| `./build.sh --daemon` | Starts the server in the background (logs to `data/server.log`) |
| `./build.sh --status` | Checks if port 8000 is active and queries `/health/ready` |
| `./build.sh --stop` | Cleanly stops server process and frees port 8000 |
| `./build.sh --test` | Runs the complete 93+ test suite via pytest |
| `./build.sh --clean` | Cleans up cache, locks (`data/scheduler.lock`), and temporary files |

---

## What the Build Script Does Automatically:
1. **Python Detection**: Locates Python 3.10+ in `.venv`, `venv`, Homebrew, or system paths.
2. **Configuration**: Initializes `.env` from `.env.example` if not already present.
3. **Data Directories**: Ensures `data/raw`, `data/backups` exist.
4. **Dependency Check**: Automatically verifies FastAPI, Uvicorn, SQLAlchemy, Pydantic, etc.
5. **Database Initialization**: Ensures `data/udyog_sathi.db` tables and schema migrations are applied.
6. **Port Collision Management**: Checks port 8000 and frees any stale orphaned process.
7. **Scheduler Lock Reset**: Clears any stale APScheduler lock so the crawler scheduler boots cleanly.
8. **Launches App**: Starts Uvicorn serving both REST API endpoints and static frontend on port 8000 with hot-reload enabled.
