import os
import time
import csv
from datetime import datetime, timedelta
from pathlib import Path

import requests


# =========================
# CONFIG
# =========================

CLIENT_ID = "LV3BhILFdDOi58Opm9NaDWtyOpga"
CLIENT_SECRET = "ISq_dJxfRItHFjQltUXoAV5jCvsa"

STOP_QUERY = "Chalmers"
LINES_TO_KEEP = {"6", "64"}

POLL_EVERY_SECONDS = 60
RUN_FOR_MINUTES = 60

# how far ahead to ask for departures each time
TIME_SPAN_MINUTES = 30

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_FILE = OUTPUT_DIR / "departures_chalmers_snapshots.csv"


# =========================
# AUTH
# =========================

def get_access_token(client_id: str, client_secret: str) -> str:
    url = "https://ext-api.vasttrafik.se/token"
    response = requests.post(
        url,
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


# =========================
# API CALLS
# =========================

def search_stop_area(headers: dict, query: str) -> dict:
    url = "https://ext-api.vasttrafik.se/pr/v4/locations/by-text"
    params = {
        "q": query,
        "types": "stoparea",
        "limit": 10
    }
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def choose_chalmers_stop_area_gid(location_data: dict) -> str:
    results = location_data.get("results", [])
    if not results:
        raise RuntimeError("No stop areas found for Chalmers")

    print("\nStop search results:")
    for i, item in enumerate(results, start=1):
        print(
            f"{i}. "
            f"name={item.get('name')} | "
            f"gid={item.get('gid')} | "
            f"type={item.get('locationType')}"
        )

    # prefer exact name Chalmers if present
    for item in results:
        if (item.get("name") or "").strip().lower() == "chalmers":
            return item["gid"]

    # fallback: first result containing chalmers
    for item in results:
        if "chalmers" in (item.get("name") or "").lower():
            return item["gid"]

    raise RuntimeError("Could not determine Chalmers stop area gid")


def get_departures(headers: dict, stop_area_gid: str) -> dict:
    url = f"https://ext-api.vasttrafik.se/pr/v4/stop-areas/{stop_area_gid}/departures"

    now_local = datetime.now().astimezone().replace(microsecond=0).isoformat()

    params = {
        "startDateTime": now_local,
        "timeSpanInMinutes": TIME_SPAN_MINUTES,
        "limit": 100,
        "maxDeparturesPerLineAndDirection": 10,
    }

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


# =========================
# PARSING
# =========================

def parse_departure(dep: dict, collected_at: str) -> dict:
    service_journey = dep.get("serviceJourney", {}) or {}
    line = service_journey.get("line", {}) or {}
    stop_point = dep.get("stopPoint", {}) or {}
    realtime_stop_point = dep.get("realtimeStopPoint", {}) or {}

    line_short = line.get("shortName")
    line_designation = line.get("designation")
    line_name = line.get("name")
    transport_mode = line.get("transportMode")

    planned_time = dep.get("plannedTime")
    estimated_time = dep.get("estimatedTime")
    best_time = dep.get("estimatedOtherwisePlannedTime")

    direction = service_journey.get("direction")
    service_journey_gid = service_journey.get("gid")

    stop_point_gid = stop_point.get("gid")
    stop_point_name = stop_point.get("name")
    platform = stop_point.get("platform")

    realtime_platform = None
    if realtime_stop_point:
        realtime_platform = realtime_stop_point.get("platform")

    chosen_line = None
    for candidate in [line_short, line_designation, line_name]:
        if candidate is not None and str(candidate).strip() != "":
            chosen_line = str(candidate).strip()
            break

    return {
        "collected_at": collected_at,
        "service_journey_gid": service_journey_gid,
        "line": chosen_line,
        "line_short_name": line_short,
        "line_designation": line_designation,
        "line_name": line_name,
        "transport_mode": transport_mode,
        "direction": direction,
        "stop_point_gid": stop_point_gid,
        "stop_point_name": stop_point_name,
        "platform": platform,
        "realtime_platform": realtime_platform,
        "planned_time": planned_time,
        "estimated_time": estimated_time,
        "best_time": best_time,
        "is_cancelled": dep.get("isCancelled"),
        "is_part_cancelled": dep.get("isPartCancelled"),
        # this will help later when deduplicating one departure
        "departure_key": f"{service_journey_gid}|{stop_point_gid}|{planned_time}",
    }


def append_rows(csv_path: Path, rows: list[dict]) -> None:
    if not rows:
        return

    file_exists = csv_path.exists()
    fieldnames = list(rows[0].keys())

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


# =========================
# MAIN
# =========================

def main():
    if "PASTE_YOUR" in CLIENT_ID or "PASTE_YOUR" in CLIENT_SECRET:
        raise RuntimeError("Paste your real CLIENT_ID and CLIENT_SECRET into the script first.")

    print("Getting access token...")
    token = get_access_token(CLIENT_ID, CLIENT_SECRET)
    headers = get_headers(token)
    print("Access token OK")

    print("Searching for stop area...")
    location_data = search_stop_area(headers, STOP_QUERY)
    stop_area_gid = choose_chalmers_stop_area_gid(location_data)
    print(f"\nUsing Chalmers stopAreaGid: {stop_area_gid}")

    end_time = time.time() + RUN_FOR_MINUTES * 60

    while time.time() < end_time:
        try:
            collected_at = datetime.now().astimezone().replace(microsecond=0).isoformat()

            data = get_departures(headers, stop_area_gid)
            departures = data.get("results", []) or []

            rows = []
            for dep in departures:
                row = parse_departure(dep, collected_at)
                if row["line"] in LINES_TO_KEEP:
                    rows.append(row)

            append_rows(CSV_FILE, rows)
            print(f"{collected_at} | saved {len(rows)} rows")

        except requests.HTTPError as e:
            print("HTTP error:", e)
            if e.response is not None:
                print(e.response.text[:1000])

            print("Refreshing token and continuing...")
            token = get_access_token(CLIENT_ID, CLIENT_SECRET)
            headers = get_headers(token)

        except Exception as e:
            print("Unexpected error:", repr(e))

        time.sleep(POLL_EVERY_SECONDS)

    print(f"\nDone. Data saved to: {CSV_FILE}")


if __name__ == "__main__":
    main()