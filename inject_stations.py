import json
coords = {
    'CSMT': {'name': 'Mumbai CSM Trm', 'lat': 18.9398, 'lon': 72.8354},
    'DR': {'name': 'Dadar Ctrl', 'lat': 19.0190, 'lon': 72.8427},
    'KYN': {'name': 'Kalyan Jn', 'lat': 19.2372, 'lon': 73.1363},
    'KSRA': {'name': 'Kasara', 'lat': 19.6385, 'lon': 73.4735},
    'IGP': {'name': 'Igatpuri', 'lat': 19.6974, 'lon': 73.5516},
    'NK': {'name': 'Nashik Road', 'lat': 19.9678, 'lon': 73.8340},
    'MMR': {'name': 'Manmad Jn', 'lat': 20.2543, 'lon': 74.4379},
    'CSN': {'name': 'Chalisgaon Jn', 'lat': 20.4611, 'lon': 75.0118},
    'JL': {'name': 'Jalgaon Jn', 'lat': 21.0113, 'lon': 75.5684},
    'BSL': {'name': 'Bhusaval Jn', 'lat': 21.0504, 'lon': 75.7946},
    'BAU': {'name': 'Burhanpur', 'lat': 21.3142, 'lon': 76.2234},
    'KNW': {'name': 'Khandwa Jn', 'lat': 21.8268, 'lon': 76.3533},
    'ET': {'name': 'Itarsi Jn', 'lat': 22.6133, 'lon': 77.7667},
    'RKMP': {'name': 'Rani Kamalapati', 'lat': 23.2128, 'lon': 77.4332},
    'BPL': {'name': 'Bhopal Jn', 'lat': 23.2676, 'lon': 77.4143},
    'BINA': {'name': 'Bina Jn', 'lat': 24.1677, 'lon': 78.1884},
    'LAR': {'name': 'Lalitpur Jn', 'lat': 24.6931, 'lon': 78.4116},
    'VGLJ': {'name': 'VGL Jhansi Jn', 'lat': 25.4411, 'lon': 78.5524},
    'DBA': {'name': 'Dabra', 'lat': 25.8829, 'lon': 78.3340},
    'GWL': {'name': 'Gwalior Jn', 'lat': 26.2081, 'lon': 78.1752},
    'MRA': {'name': 'Morena', 'lat': 26.4952, 'lon': 78.0051},
    'DHO': {'name': 'Dholpur Jn', 'lat': 26.7029, 'lon': 77.8860},
    'AGC': {'name': 'Agra Cantt', 'lat': 27.1594, 'lon': 77.9897},
    'MTJ': {'name': 'Mathura Jn', 'lat': 27.4815, 'lon': 77.6749},
    'KSV': {'name': 'Kosi Kalan', 'lat': 27.7981, 'lon': 77.4312},
    'PWL': {'name': 'Palwal', 'lat': 28.1408, 'lon': 77.3275},
    'FDB': {'name': 'Faridabad', 'lat': 28.3888, 'lon': 77.3090},
    'NZM': {'name': 'Hazrat Nizamuddin', 'lat': 28.5888, 'lon': 77.2530},
    'NDLS': {'name': 'New Delhi', 'lat': 28.6429, 'lon': 77.2191},
    'SSB': {'name': 'Shakur Basti', 'lat': 28.6789, 'lon': 77.1308},
    'BGZ': {'name': 'Bahadurgarh', 'lat': 28.6835, 'lon': 76.9248},
    'ROK': {'name': 'Rohtak Jn', 'lat': 28.8955, 'lon': 76.5892},
    'JIND': {'name': 'Jind Jn', 'lat': 29.3150, 'lon': 76.3117},
    'NRW': {'name': 'Narwana Jn', 'lat': 29.6108, 'lon': 76.1130},
    'TUN': {'name': 'Tohana', 'lat': 29.7042, 'lon': 75.9015},
    'JHL': {'name': 'Jakhal Jn', 'lat': 29.7891, 'lon': 75.8273},
    'BLZ': {'name': 'Budhlada', 'lat': 29.9329, 'lon': 75.5658},
    'MSZ': {'name': 'Mansa', 'lat': 29.9880, 'lon': 75.3995},
    'BTI': {'name': 'Bathinda Jn', 'lat': 30.2016, 'lon': 74.9455},
    'KKP': {'name': 'Kot Kapura Jn', 'lat': 30.5843, 'lon': 74.8251},
    'FDK': {'name': 'Faridkot', 'lat': 30.6720, 'lon': 74.7431},
    'FZR': {'name': 'Firozpur Cantt Jn', 'lat': 30.9163, 'lon': 74.6231}
}

existing_content = open('frontend/src/data/stations.js').read()

lines = []
for code, data in coords.items():
    if f' {code}: ' not in existing_content and f'  {code}:' not in existing_content:
        lines.append(f'  {code}: {{ name: \"{data["name"]}\", lat: {data["lat"]}, lon: {data["lon"]} }},')

if lines:
    new_content = existing_content.replace('};', '') + '\n' + '\n'.join(lines) + '\n};\n'
    open('frontend/src/data/stations.js', 'w').write(new_content)
    print(f'Added {len(lines)} new stations.')
else:
    print('No new stations to add.')
