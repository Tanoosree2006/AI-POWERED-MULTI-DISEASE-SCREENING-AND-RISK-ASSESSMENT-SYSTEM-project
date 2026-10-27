# Milestone 3: React frontend

Responsive dashboard for the screening platform. React 18 + Vite, Tailwind CSS 3, React Router, Axios, Recharts, Lucide.
It needs the backend (Milestone 2, with the models from Milestones 1 and 4) to be running.

## Run it (Windows PowerShell)
```powershell
# Terminal 1: backend (from the repository root, venv active, models trained, `alembic upgrade head` done)
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: frontend
cd frontend
copy .env.example .env        # VITE_API_URL=http://localhost:8000
npm install
npm run dev                   # open http://localhost:5173
npm test                      # 48 tests
npm run build                 # production build into dist/
```
First time: open the site, click Register, create an account, then Screening > pick a module > "Fill with a real example" > Run screening.

## The 12 required pages
| # | Page | Route | Notes |
|---|---|---|---|
| 1 | Landing | `/` | project explanation, prototype disclaimer, no performance or approval claims |
| 2 | Login, Register | `/login`, `/register` | client + server validation; JWT kept in sessionStorage |
| 3 | Dashboard | `/dashboard` | totals, trend line, per-module bars, recent records, all from stored records; honest empty state |
| 4 | Module selection | `/screen` | modules without a trained model are shown as "not available" and cannot be opened |
| 5 | Input form | `/screen/:disease` | fields generated from the API (labels, units, ranges, optional fields, coded options); inline errors and an error summary |
| 6 | Result | `/results/:id` | "model-estimated screening score", threshold, flag, warnings, limits statement |
| 7 | SHAP explanation | component on the result page | bar chart plus an accessible table of the same numbers |
| 8 | Image upload | `/image` | only active when the server has an image model; type and size checks before upload |
| 9 | Grad-CAM view | component on the image page | original beside overlay, with the "attention, not proof" label |
| 10 | History | `/history` | filter, pagination, open, delete with confirmation |
| 11 | Model performance | `/metrics` | tabs per module; every number comes from the API; confusion matrix; repeated-CV table; high-sensitivity operating point |
| 12 | About / methodology / limitations | `/about` | datasets, method, limitations, privacy, live module status |

## Design rules followed
No button that does nothing; loading, empty, success and error states on every data page; labels tied to inputs; errors announced with `role="alert"`; charts always have a text table alternative; no sample data is ever displayed as real.

## Tests (48, all passing in the build environment)
`src/test/utils.test.js` (validation, formatting), `apiClient.test.js` (auth header, error envelope, 401 handling, unreachable server, multipart upload), `pages.test.jsx` (routing guard, sign-in and register validation, module list, form validation, null for blank optional fields, example filling, server errors, results, history delete/cancel/filter, dashboard, metrics, image page).
`node scripts/integration.mjs http://127.0.0.1:8000` runs the same API client against a live backend (20 checks without an image model; 22 with one).

## What was NOT verified
No browser was available in the build environment, so the **visual layout and responsiveness were never looked at on a screen**. The tests check behaviour and text, not appearance. Open the app in a browser, resize it, and fix any styling issues you see. The production bundle is about 650 kB (single chunk); code-splitting is a possible improvement.
