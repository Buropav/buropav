# ProtoRyde Deployment Runbook

This runbook is for the umbrella repo (`buropav`) with two submodules:
- `protoryde-backend` (Render)
- `protoryde-frontend` (Vercel)

## 1) Pre-deploy sync (required)

```bash
git pull --ff-only
git submodule update --init --recursive

git -C protoryde-backend pull --ff-only origin main
git -C protoryde-frontend pull --ff-only origin main
```

## 2) Backend deploy (Render)

Repository: `Buropav/protoryde-backend`

Render settings:
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

Environment variables:
- `DATABASE_URL` (Render Postgres connection string)
- `ENABLE_SCHEDULER=false`

Validation after deploy:
```bash
curl -s https://<backend>.onrender.com/health
curl -s https://<backend>.onrender.com/api/premium/model-status
```

## 3) Frontend deploy (Vercel)

Repository: `Buropav/protoryde-frontend`

Vercel build settings (already in `vercel.json`):
- Install: `npm install`
- Build: `npx expo export -p web`
- Output directory: `dist`

Environment variables:
- `EXPO_PUBLIC_API_URL=https://<backend>.onrender.com/api`

Validation after deploy:
- Open the site and complete onboarding to premium reveal.
- Confirm network requests hit the Render backend URL.

## 4) Umbrella repo pointer update (only if needed)

If you changed submodule commits and want `Buropav/buropav` to point to latest:

```bash
git add protoryde-backend protoryde-frontend
git commit -m "chore: bump submodule pointers"
git push origin main
```

## 5) Demo-day smoke checklist

- Registration works end-to-end.
- Exclusions acknowledgement is mandatory.
- Policy and claim APIs return data.
- Trigger simulation returns fraud layers.
- Policy PDF downloads successfully.
