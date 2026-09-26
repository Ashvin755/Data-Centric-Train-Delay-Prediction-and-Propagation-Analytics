"""
Fetch and print RailRadar live payload for a train.

Usage:
  python print_live_payload.py 61631
  python print_live_payload.py 18238 --journey-date 2026-05-26

The script reads the API key from the environment variable
RAILRADAR_API_KEY_ONE_DAY and prints the full JSON response from
RailRadar as formatted output.
"""

import argparse
import datetime
import json
import os
import sys

import requests
from dotenv import load_dotenv


def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("RAILRADAR_API_KEY_ONE_DAY")
    if not api_key:
        raise SystemExit(
            "ERROR: RAILRADAR_API_KEY_ONE_DAY is not set in the environment."
        )
    return api_key


def build_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "X-API-Key": api_key,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://railradar.in/",
        "Origin": "https://railradar.in",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }


def fetch_live_payload(train_number: str, journey_date: str, api_key: str) -> dict:
    url = f"https://api.railradar.in/v1/trains/{train_number}/live"
    params = {
        "date": journey_date,
        "haltsOnly": "true",
    }

    response = requests.get(url, headers=build_headers(api_key), params=params, timeout=20)

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        print(f"ERROR: HTTP {response.status_code} - {exc}", file=sys.stderr)
        if response.text:
            print(response.text, file=sys.stderr)
        raise SystemExit(1)

    try:
        return response.json()
    except ValueError:
        print("ERROR: Response is not valid JSON.", file=sys.stderr)
        print(response.text, file=sys.stderr)
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print formatted JSON for RailRadar live payload."
    )
    parser.add_argument(
        "train_number",
        help="RailRadar train number to query (e.g. 61631)",
    )
    parser.add_argument(
        "--journey-date",
        default=datetime.date.today().isoformat(),
        help="Journey date in YYYY-MM-DD format (default: today)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = load_api_key()
    payload = fetch_live_payload(args.train_number, args.journey_date, api_key)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
