# statinf_project

Statistical inference study comparing scheduled vs actual departure times for Västtrafik lines 6 (tram) and 64 (bus) from Chalmers station in Gothenburg.

## Project structure

```
statinf_project/
├── python_code/
│   ├── data/
│   │   ├── raw_data/           # Raw collected data (gitignored)
│   │   └── cleaned_data/
│   │       └── final_departures.csv   # Final output (tracked)
│   ├── data_clean.ipynb        # Data cleaning pipeline
│   └── get_directions.ipynb    # Scrape scheduled departure times per direction
└── r_kod/
    └── main.R                  # Statistical analysis
```

## Data collection

Departure data was collected by polling the [Västtrafik API v4](https://developer.vasttrafik.se/) every 60 seconds using `python_code/main.py`. Each snapshot records:

| Column | Description |
|---|---|
| `collected_at` | Timestamp when the snapshot was taken |
| `line` | Line number (6 or 64) |
| `transport_mode` | `tram` or `bus` |
| `planned_time` | Scheduled departure time |
| `estimated_time` | Real-time estimated departure time |

## Python notebooks

### `get_directions.ipynb`

Parses HTML pasted from the Västtrafik journey planner to extract the scheduled timetable for each direction. Produces four CSVs in `data/cleaned_data/`:

- `line_6__kortedala_scheduled.csv` — Line 6 towards Kortedala via Centralstationen
- `line_6_varmfront_scheduled.csv` — Line 6 towards Länsmansgården via Sahlgrenska
- `line_64_heden_scheduled.csv` — Line 64 towards Heden
- `line_64_axel_scheduled.csv` — Line 64 towards Högsbohöjd

### `data_clean.ipynb`

Two-step pipeline:

1. **Convert** `data/raw_data/data.txt` (tab-separated) → `data/raw_data/data.csv`
2. **Clean & process**:
   - Cross-references `planned_time (HH:MM)` against the direction CSVs to assign a direction to each departure
   - Deduplicates on `(line, direction, planned_time)`, keeping the last snapshot per departure
   - Computes `delay_minutes = estimated_time − planned_time`
   - Saves `data/cleaned_data/final_departures.csv`

### Output: `final_departures.csv`

| Column | Description |
|---|---|
| `line` | 6 or 64 |
| `direction` | Direction label (e.g. "Heden") |
| `planned_time` | Scheduled departure (`HH:MM:SS`) |
| `estimated_time` | Real-time estimated departure (`HH:MM:SS`) |
| `delay_minutes` | `estimated − planned` in minutes |

## Setup

```bash
cd python_code
python3 -m venv .venv
source .venv/bin/activate
pip install requests pandas beautifulsoup4 lxml
```
