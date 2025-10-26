# Legacy Files

This folder contains files that are no longer actively used in the project but kept for reference.

## Files Moved Here

### 1. `Dockerfile_root.old`
- **Original:** `Dockerfile` (root directory)
- **Why:** Replaced by `app/Dockerfile` which is used in docker-compose
- **Date:** October 24, 2024

### 2. `ollama_docker-compose.yaml`
- **Original:** `ollama_services/docker-compose.yaml`
- **Why:** Redundant - Ollama is configured in main `docker-compose.yml`
- **Date:** October 24, 2024

### 3. `FINAL_SETUP.txt`
- **Original:** Root directory
- **Why:** Old setup documentation, superseded by README.md and PROJECT_PLAN.md
- **Date:** October 24, 2024

### 4. `utils/` folder
- **Original:** `utils/utils.py`
- **Why:** Duplicate - App blueprints now use `app/utils.py`
- **Date:** October 24, 2024

## Previously Deleted Files

These files were already removed before archiving:

- `app/config_example.py` - Example config
- `app/test_lly.py` - Test script
- `app/test_signup.py` - Test script
- `app/debug_users.py` - Debug script
- `app/setup_alphavantage.py` - Setup script
- `BUILD_SUMMARY.md` - Old build documentation

## Active Project Structure

Current active files are in:
- `app/` - Main web application
- `rag/` - RAG service
- `db/` - Database module
- `stocks_data_collector/` - Stock data service
- `schedualer/` - Background scheduler
- `ollama_services/` - Ollama/LLM service files (check_models.py, test_client.py, etc.)

## Restoration

If you need any of these files:

```bash
# Copy from legacy back to project
copy legacy\Dockerfile_root.old Dockerfile
```

## Safe to Delete?

You can safely delete this entire `legacy/` folder once you're confident you don't need these files.

```bash
# To delete permanently (after verification)
rmdir /s legacy
```

---

**Archived:** October 24, 2024
**Purpose:** Clean up project structure while preserving history

