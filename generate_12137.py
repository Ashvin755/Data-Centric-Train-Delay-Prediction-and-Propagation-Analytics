import json
import csv
from collections import defaultdict

with open('docs/statics/12137_static.json', 'r', encoding='utf-8') as f:
    static_data = json.load(f)

train = static_data['data']['train']
train_number = train['trainNumber']
train_name = train['trainName']

route = [x['stationCode'] for x in sorted(static_data['data']['route'], key=lambda x: x['sequence'])]

journeys = defaultdict(list)
with open('dataset/supabase/rail_data_rows.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['train_no'] == '12137':
            date = row['journey_date']
            journeys[date].append({
                'stationCode': row['station_code'],
                'scheduledArrival': float(row['scheduled_arrival']) if row['scheduled_arrival'] else None,
                'scheduledDeparture': float(row['scheduled_departure']) if row['scheduled_departure'] else None,
                'actualArrival': float(row['actual_arrival']) if row['actual_arrival'] else None,
                'actualDeparture': float(row['actual_departure']) if row['actual_departure'] else None,
                'delayArrival': float(row['delay_arrival_minutes']) if row['delay_arrival_minutes'] else None,
                'delayDeparture': float(row['delay_departure_minutes']) if row['delay_departure_minutes'] else None,
            })

js_content = f"export const TRAIN_{train_number} = {{\n"
js_content += f"  trainNumber: \"{train_number}\",\n"
js_content += f"  trainName: \"{train_name}\",\n"
js_content += f"  route: {json.dumps(route)},\n"
js_content += f"  journeys: {json.dumps(journeys, separators=(',', ':'))}\n"
js_content += f"}};\n"

with open('frontend/src/data/train_12137.js', 'w', encoding='utf-8') as f:
    f.write(js_content)
