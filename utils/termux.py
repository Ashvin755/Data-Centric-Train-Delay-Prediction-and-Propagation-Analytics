import requests
from typing import Dict, Any

BASE_URL = "https://api.railradar.in/api"
ENDPOINT = "/v1/trains"


def get_train_info(api_key: str, train_number: str) -> Dict[str, Any]:
    url = f"{BASE_URL}{ENDPOINT}/{train_number}"
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "RailRadar-Python-Client/1.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        payload = response.json()
        print("\nRAW JSON RESPONSE:\n", payload)
        data = payload.get("data", {})
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return {}


def get_current_delay(route):

    delays = []



    for stop in route:

        if stop.get("delayDepartureMinutes") is not None:

            delays.append(stop["delayDepartureMinutes"])

        elif stop.get("delayArrivalMinutes") is not None:

            delays.append(stop["delayArrivalMinutes"])



    if not delays:

        return None



    return max(delays)

    latest = None
    for stop in route:
        if stop.get("actualArrival") or stop.get("actualDeparture"):
            latest = stop

    if not latest:
        return None

    return latest.get("delayDepartureMinutes") or latest.get("delayArrivalMinutes")


def print_train_info(data: Dict[str, Any]):
    train = data.get("train", {})
    route = data.get("route", [])

    if not train:
        print("No train data received.")
        return

    print("\n" + "=" * 60)
    print(f"Train: {train.get('trainName', 'N/A')} ({train.get('trainNumber', 'N/A')})")

    delay = get_current_delay(route)
    if delay is not None:
        print(f"Current Delay: +{delay} min")
    else:
        print("Current Delay: Not Available")

    print(f"Departure Station: {train.get('sourceStationName', 'N/A')}")
    print(f"Destination: {train.get('destinationStationName', 'N/A')}")
    print("=" * 60 + "\n")


def main():
    api_key = input("Enter your RailRadar API key: ").strip()
    if not api_key:
        print("API key required. Exiting.")
        return

    print("\nRailRadar Train Info Tool\n")

    while True:
        print("Options:")
        print("1. Get Train Info (by train number)")
        print("2. Exit")

        choice = input("\nEnter choice (1-2): ").strip()

        if choice == "1":
            train_number = input("Enter train number (e.g., 12951): ").strip()
            data = get_train_info(api_key, train_number)
            print_train_info(data)

        elif choice == "2":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()