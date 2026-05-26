import csv, json
from collections import defaultdict

rows = []
with open('dataset/supabase/rail_data_rows_27march.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('train_no') == '18238':
            rows.append(row)

station_seqs = defaultdict(list)
for r in rows:
    station_seqs[r['journey_date']].append(r['station_code'])
canonical_route = max(station_seqs.values(), key=len)

journeys = defaultdict(list)
for r in rows:
    def parse_num(v):
        try:
            return float(v) if v else None
        except:
            return None
    journeys[r['journey_date']].append({
        'stationCode': r['station_code'],
        'scheduledArrival': parse_num(r['scheduled_arrival']),
        'scheduledDeparture': parse_num(r['scheduled_departure']),
        'actualArrival': parse_num(r['actual_arrival']),
        'actualDeparture': parse_num(r['actual_departure']),
        'delayArrival': parse_num(r['delay_arrival_minutes']),
        'delayDeparture': parse_num(r['delay_departure_minutes']),
    })

# Write to JS file
out = 'export const TRAIN_18238 = {\n'
out += '  trainNumber: "18238",\n'
out += '  trainName: "Chhattisgarh Express",\n'
out += '  route: ' + json.dumps(canonical_route) + ',\n'
out += '  journeys: {\n'

for date in sorted(journeys.keys()):
    jdata = journeys[date]
    out += f'    "{date}": {json.dumps(jdata, separators=(",",":"))},\n'

out += '  }\n};\n'

with open('frontend/src/data/train_18238.js', 'w') as f:
    f.write(out)

print('Written train_18238.js, size:', len(out), 'chars')
print('Total journey dates:', len(journeys))
print('Route stations:', len(canonical_route))
