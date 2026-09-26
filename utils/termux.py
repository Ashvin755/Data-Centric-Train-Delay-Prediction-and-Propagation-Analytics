import requests
from typing import Dict, Any

BASE_URL = "https://api.railradar.in"
ENDPOINT = "/v1/trains"


def get_train_info(api_key: str, train_number: str, journey_date: str = None, data_type: str = "live") -> Dict[str, Any]:
    url = f"{BASE_URL}{ENDPOINT}/{train_number}/live"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-API-Key": api_key,
        "User-Agent": "RailRadar-Python-Client/1.0"
    }
    
    # Build query parameters (current live endpoint)
    params = {"haltsOnly": "true"}
    if journey_date:
        params["date"] = journey_date

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
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
            
            # Optional: Journey Date
            journey_date = input("Enter journey date (YYYY-MM-DD) [press Enter to auto-detect]: ").strip()
            if not journey_date:
                journey_date = None
            
            # Optional: Data Type
            print("\nData Type Options:")
            print("  1. full (default) - Complete data with static + live info")
            print("  2. static - Only static schedule data")
            print("  3. live - Only real-time tracking data")
            data_type_choice = input("Select data type (1-3) [press Enter for full]: ").strip()
            
            data_type_map = {
                "1": "full",
                "2": "static",
                "3": "live",
                "": "full"
            }
            data_type = data_type_map.get(data_type_choice, "full")
            
            data = get_train_info(api_key, train_number, journey_date, data_type)
            print_train_info(data)

        elif choice == "2":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()