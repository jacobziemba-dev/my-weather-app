# CLAUDE.md

This file provides guidance for AI assistants working in this repository.

## Project Overview

A single-page weather application that fetches real-time weather data from the OpenWeather API and displays it in a browser. The backend is a minimal Flask app; the frontend is a self-contained HTML file with embedded CSS and JavaScript.

**Live deployment:** Azure App Service (`my-weather-app`, Production slot)

---

## Repository Structure

```
my-weather-app/
├── app.py                              # Flask backend — all API logic lives here
├── requirements.txt                    # Python dependencies
├── startup.txt                         # Production server startup command
├── templates/
│   └── index.html                      # Frontend — HTML, CSS, and JS in one file
└── .github/
    └── workflows/
        └── main_my-weather-app.yml     # CI/CD: build → deploy to Azure on push to main
```

There is no build system, no Node.js, and no separate frontend tooling. Everything runs as plain Python with Flask serving a single Jinja2 template.

---

## Architecture

### Backend (`app.py`)

Flask app with two routes:

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serves `templates/index.html` |
| `/weather` | GET | Proxies to OpenWeather API, returns JSON |

**`/weather` query parameters (mutually exclusive):**
- `city` — city name string
- `lat` + `lon` — decimal coordinates (used for geolocation)

**Response shape:**
```json
{
  "city": "London",
  "country": "GB",
  "temp": 15,
  "feels_like": 13,
  "humidity": 72,
  "description": "Partly Cloudy",
  "icon": "02d",
  "wind": 18
}
```

- Temperature is in **°C** (metric units from OpenWeather).
- Wind speed is converted from m/s → km/h by multiplying by 3.6.
- Weather description is title-cased before being returned.

**Error responses:**
- `400` — neither `city` nor `lat`/`lon` were provided.
- `404` — OpenWeather returned a non-200 status (e.g., unknown city).

### Frontend (`templates/index.html`)

Vanilla JavaScript, no frameworks. Runs entirely in the browser; communicates only with the local `/weather` endpoint (never directly with OpenWeather).

Key behaviours:
- On page load, `locateMe()` is called automatically — the browser prompts for geolocation and pre-loads local weather.
- City search is triggered by clicking **Search** or pressing **Enter**.
- Weather icons are loaded from `https://openweathermap.org/img/wn/{icon}@2x.png`.
- Loading state, errors, and results share a single `#status` element and `#weather-card`.

Design tokens used in CSS:
- Background: `#0f0f1a` (page), `#1a1a2e` (card/input)
- Primary accent: `#7eb8f7` (text highlights, buttons)
- Error colour: `#ff6b6b`

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENWEATHER_API_KEY` | Yes (production) | API key from openweathermap.org |

The app falls back to the placeholder string `"YOUR_API_KEY_HERE"` when the variable is unset, which will cause all weather requests to fail with a 401 from OpenWeather. Set the variable in your shell or Azure App Service configuration before running.

---

## Running Locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set the API key
export OPENWEATHER_API_KEY=your_key_here

# 4. Start the development server
python app.py
```

Flask's development server starts on `http://localhost:5000` by default.

---

## Production Server

The startup command (used by Azure App Service) is defined in `startup.txt`:

```
gunicorn --bind=0.0.0.0 --timeout 600 app:app
```

- `app:app` — Python module `app`, Flask instance `app`.
- `--timeout 600` — long timeout to accommodate slow OpenWeather responses.
- No workers are specified; Gunicorn defaults to 1 sync worker, which is adequate for this app's scale.

---

## Dependencies

Defined in `requirements.txt` (no pinned versions):

| Package | Purpose |
|---|---|
| `flask` | Web framework, routing, template rendering |
| `requests` | HTTP client used to call OpenWeather API |
| `gunicorn` | Production WSGI server |

When adding dependencies, add them to `requirements.txt`. No lock file is present; Azure's Oryx build engine runs `pip install -r requirements.txt` during deployment.

---

## CI/CD Pipeline

**Workflow file:** `.github/workflows/main_my-weather-app.yml`

**Trigger:** Push to `main` branch (or manual `workflow_dispatch`).

**Steps:**

1. **Build job** (ubuntu-latest, Python 3.11)
   - Checks out code.
   - Creates virtual environment `antenv` and installs dependencies.
   - Uploads the repo (excluding `antenv/`) as a build artifact.

2. **Deploy job**
   - Downloads the artifact.
   - Authenticates to Azure using OIDC (federated credentials — no long-lived secrets).
   - Deploys to Azure Web App `my-weather-app`, slot `Production`.
   - Azure's Oryx build engine runs `pip install` again on the platform side (`SCM_DO_BUILD_DURING_DEPLOYMENT=true`).

**Required GitHub Secrets:**
- `AZUREAPPSERVICE_CLIENTID_AF8653198A4D4BE6A024E866960157A3`
- `AZUREAPPSERVICE_TENANTID_D06B16526ECE4B67A24CF70BE7B7ABCC`
- `AZUREAPPSERVICE_SUBSCRIPTIONID_06C45B6738944D6683E7EFD297A4C1EE`

Changes merged to `main` are deployed automatically. Feature branches are not deployed.

---

## Development Conventions

### Python
- There is no linter or formatter configured. Follow PEP 8 style when editing `app.py`.
- Keep route handlers thin. Business logic (if any is added) should go in separate functions, not inline in the route.
- The API key is read once at module load time (`API_KEY = os.environ.get(...)`). If you add hot-reload support, be aware of this.

### HTML / CSS / JavaScript
- All frontend code lives in `templates/index.html`. There is no bundler or transpiler.
- CSS is embedded in a `<style>` block; JavaScript is embedded in a `<script>` block.
- Use vanilla JS only — no external libraries are loaded.
- Keep the dark-theme colour palette consistent (see design tokens above).

### Git
- `main` is the production branch — pushes trigger deployment.
- Use feature branches for development. Branch names prefixed with `claude/` are used by AI assistants.
- Write descriptive commit messages. The existing history uses imperative mood ("Add ...", "Fix ...", "Refactor ...").

---

## Testing

There is currently no test suite. If tests are added:
- Use `pytest` (install with `pip install pytest`).
- Place test files in a `tests/` directory.
- Use Flask's test client (`app.test_client()`) for route integration tests.
- Mock `requests.get` when testing the `/weather` route to avoid real API calls.

---

## Common Tasks

**Add a new weather field** (e.g., UV index):
1. Update the `params` dict in `app.py` if a different OpenWeather endpoint is needed.
2. Add the new key to the `return jsonify({...})` block in `get_weather()`.
3. Add a corresponding `<div>` in the `.details` section of `index.html`.
4. Update the `fetchWeather` JS function to populate the new element.

**Change units to imperial:**
- In `app.py`, change `"units": "metric"` to `"units": "imperial"` in both `params` dicts.
- In `index.html`, update the unit labels (`°C` → `°F`, `km/h` → `mph`) and remove the `* 3.6` wind conversion (imperial wind is already in mph).

**Add a new Flask route:**
- Define the route in `app.py` using the `@app.route(...)` decorator.
- If it serves HTML, add the template to `templates/`.
- If it returns JSON, follow the existing pattern (return `jsonify(...)` with an appropriate HTTP status code).
