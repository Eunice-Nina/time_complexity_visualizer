# Time Complexity Visualizer

A small Flask API that measures how long an algorithm takes on inputs of increasing size, then draws a graph of time against input size. Each request returns the raw timings as JSON along with the graph as a base64-encoded PNG.

## Getting Started

### 1. Install the dependencies

From the project folder, run:

```bash
python -m pip install -r requirements.txt
```

### 2. Start the server

```bash
python app.py
```

Leave this terminal open. The API is served at `http://localhost:8000` for as long as the command keeps running.

## Using the API

### Request

```
GET /analyze?algo=<name>&step=<int>&n_max=<int>
```

| Parameter | Description |
|-----------|-------------|
| `algo`    | Name of the algorithm to time (see the list below) |
| `step`    | Gap between consecutive input sizes |
| `n_max`   | Largest input size to test |

The smallest input size (`n_min`) is fixed at 0.

Example:

```
http://localhost:8000/analyze?algo=linear_search&step=10&n_max=1000
```

### Available algorithms

- `linear_search`
- `binary_search`
- `bubble_sort`
- `insertion_sort`
- `merge_sort`
- `nested_loops`
- `factorial`

### Response format

```json
{
  "algorithm": "linear_search",
  "n_min": 0,
  "n_max": 1000,
  "step": 10,
  "input_sizes": [1, 10, 20, ...],
  "times_seconds": [0.000002, 0.000004, ...],
  "image_path": "/absolute/path/to/static/linear_search_plot.png",
  "image_base64": "iVBORw0KG..."
}
```

Every graph is also written to the `static/` folder as a PNG.

## Trying Out Each Algorithm

With the server running, open these URLs in your browser one after another:

```
http://localhost:8000/analyze?algo=linear_search&step=10&n_max=1000
http://localhost:8000/analyze?algo=binary_search&step=10&n_max=1000
http://localhost:8000/analyze?algo=bubble_sort&step=10&n_max=1000
http://localhost:8000/analyze?algo=nested_loops&step=10&n_max=1000
http://localhost:8000/analyze?algo=insertion_sort&step=10&n_max=1000
http://localhost:8000/analyze?algo=merge_sort&step=10&n_max=1000
http://localhost:8000/analyze?algo=factorial&step=100&n_max=10000
```

The browser will show a block of JSON rather than a picture. That is normal, because this is an API and not a web page. To see the graph itself, open the matching file in `static/`, for example `static/bubble_sort_plot.png`. A PNG is created (or overwritten) each time you call an algorithm's URL.

### What to expect from each graph

- **`linear_search` and `binary_search`:** these stay fairly flat. Small spikes are normal, since timings at the microsecond level pick up noise from the system.
- **`bubble_sort`, `insertion_sort` and `nested_loops`:** all quadratic, so the curve bends upward like a parabola. Try `n_max=5000` or `n_max=10000` to make the shape clearer.
- **`merge_sort`:** it grows as n log n, so the curve rises more gently than the quadratic ones.
- **`factorial`:** despite the name, it is a single loop multiplying up to n, so it grows linearly like `linear_search`. A large `n_max` (such as 10000) makes the trend easier to spot, since each step is very cheap.

## Authentication (JWT)

`/save_analysis` requires a valid JWT. The token must be sent in the
`Authorization` header as a Bearer token (never as a query parameter).

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/register` | POST | Create a user (JSON body: `username`, `password`) |
| `/login` | POST | Log in and receive an `access_token` |
| `/save_analysis` | POST | Protected: requires `Authorization: Bearer <access_token>` |

### Example (PowerShell)

```powershell
# 1. register (once)
Invoke-RestMethod -Method Post -Uri http://localhost:8000/register -ContentType "application/json" -Body '{"username":"nina","password":"secret123"}'

# 2. log in and store the token
$token = (Invoke-RestMethod -Method Post -Uri http://localhost:8000/login -ContentType "application/json" -Body '{"username":"nina","password":"secret123"}').access_token

# 3. call the protected endpoint
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/save_analysis?algo=bubble_sort&step=100&n_max=1000" -Headers @{Authorization="Bearer $token"}
```

### Error responses

- No token: `401 {"error": "I don't know you"}`
- Invalid or expired token: `401 {"error": "Bye"}`

Tokens expire after 1 hour. Set a real secret with the `JWT_SECRET_KEY`
environment variable before deploying.

## Saving an Analysis to the Database

```
POST /save_analysis?algo=<name>&step=<int>&n_max=<int>
```

This runs the same timing/plot logic as `/analyze`, but instead of only
returning the result, it persists it with **SQLAlchemy** (no raw SQL) to a
local SQLite database (`analysis.db`, created automatically on first run
and excluded from git via `.gitignore`). Each saved run becomes a row in
the `analysis` table (see `models.py`), storing the algorithm, its
parameters, the timing data, and the path to the generated plot.

Example:

```
http://localhost:8000/save_analysis?algo=bubble_sort&step=100&n_max=1000
```

Response:

```json
{
  "message": "Analysis saved successfully",
  "analysis": {
    "id": 1,
    "algorithm": "bubble_sort",
    "n_min": 0,
    "n_max": 1000,
    "step": 100,
    "input_sizes": [1, 100, 200, ...],
    "times_seconds": [0.000002, 0.0004, ...],
    "image_path": "/absolute/path/to/static/bubble_sort_plot.png",
    "created_at": "2026-09-27T20:24:55.226385"
  }
}
```

### Viewing saved analyses

```
GET /analyses
```

Returns every saved analysis (newest first) straight from the database.

## Design Notes

- **Searches** look for a value that is never in the data, which forces the worst case and shows the true complexity instead of an early lucky match.
- **Sorts** are fed reverse-sorted input, which is the worst case for the simple sorting algorithms used here.
