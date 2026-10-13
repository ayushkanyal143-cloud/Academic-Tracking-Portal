# SE_PROJECT — Academic Tracking Portal

An academic dashboard upgraded from a static display into a **dynamic, data-driven academic tracking portal**.

It supports **semester-wise subject mark tracking**, where marks are stored in a **CSV/Excel-style dataset** and are reflected in the dashboard automatically. The backend **reads the data file on every request**, so updates appear instantly without code changes.

The portal also provides **automatic SGPA and CGPA calculation**, plus a **semester-to-semester performance comparison** to track improvement.

## Layout

```
SE_project/
├── backend/
│   ├── app.py
│   ├── data/              # runtime JSON (optional legacy share demo)
│   ├── routes/            # api.py, auth.py, pages.py
│   ├── services/          # auth_service.py, academic.py, compute.py, key_sharing.py
│   └── utils/helpers.py
├── data/students_login.csv  # demo login users (CSV-backed auth)
├── data/academic_marks.csv  # semester-wise subject marks dataset (dashboard source)
├── frontend/templates/
├── frontend/static/
├── instructions.txt         # full explanation + demo passwords
├── notes.txt                # viva bullets
├── requirements.txt
└── run.py
```

## Run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:5000/` → log in (see **instructions.txt** for `username` / `password` pairs) → **Open academic dashboard**.

To update marks, edit `data/academic_marks.csv` and refresh the dashboard.

## APIs

| Endpoint | Purpose |
|----------|---------|
| `POST /submit-data` | Legacy share upload → `student_token` |
| `GET /get-result` | Metrics for token |
| `GET /api/my-summary` | Logged-in user’s CSV row + metrics + ML |
| `GET /api/academic-summary` | Semester-wise marks + SGPA/CGPA + comparisons |

## Docs

- **instructions.txt** — features, workflow, technologies  
- **notes.txt** — short viva answers  
