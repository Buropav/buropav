# Buropav Workspace (Umbrella Repo)

This repository is now the umbrella/orchestration repo for the ProtoRyde project.

## Source of Truth Repositories
- Frontend: https://github.com/Buropav/protoryde-frontend
- Backend: https://github.com/Buropav/protoryde-backend

## Why this split
- Prevents accidental cross-pushes between frontend/backend.
- Keeps demo-critical backend APIs isolated.
- Lets frontend and backend move independently with clean ownership.

## Current status
- `protoryde-frontend` contains the Expo application.
- `protoryde-backend` contains the FastAPI backend, simulation logic, policy APIs, and PDF endpoint.
- Legacy backend code is preserved in `protoryde-backend/legacy_v1`.

## Quick start
Clone and run each repository independently from its own folder.

### Frontend
```bash
git clone https://github.com/Buropav/protoryde-frontend.git
cd protoryde-frontend
npm install
npm run start
```

### Backend
```bash
git clone https://github.com/Buropav/protoryde-backend.git
cd protoryde-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Branching safety
- Do not commit frontend code in `protoryde-backend`.
- Do not commit backend code in `protoryde-frontend`.
- Keep this umbrella repo docs-only unless explicitly needed.
