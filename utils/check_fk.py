from db.supabase_client import SupabaseDB
import os
from dotenv import load_dotenv

load_dotenv()
db = SupabaseDB(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Check train_info
trains = db.client.table('train_info').select('train_no').execute()
print(f'train_info records: {len(trains.data)}')
train_nos = [t["train_no"] for t in trains.data]
print(f'train_no values: {train_nos}')

# Check journey_status_flags
journeys = db.client.table('journey_status_flags').select('train_no').execute()
print(f'\njourney_status_flags records: {len(journeys.data)}')
journey_trains = [j['train_no'] for j in journeys.data]
print(f'Unique train_no values: {set(journey_trains)}')

# Check rail_data
rail = db.client.table('rail_data').select('train_no').execute()
print(f'\nrail_data records: {len(rail.data)}')
rail_trains = [r['train_no'] for r in rail.data]
print(f'Unique train_no values: {set(rail_trains)}')

# Check for orphaned records
journey_train_nos = set(journey_trains)
rail_train_nos = set(rail_trains)
train_info_nos = set(train_nos)

orphaned_journeys = journey_train_nos - train_info_nos
orphaned_rail = rail_train_nos - train_info_nos

print(f'\n=== FOREIGN KEY VIOLATION CHECK ===')
if orphaned_journeys:
    print(f'⚠️  Orphaned journey_status_flags: {orphaned_journeys}')
else:
    print(f'✅ journey_status_flags: No orphaned records')
    
if orphaned_rail:
    print(f'⚠️  Orphaned rail_data: {orphaned_rail}')
else:
    print(f'✅ rail_data: No orphaned records')

if orphaned_journeys or orphaned_rail:
    print('\n⚠️  WARNING: Foreign key constraint will FAIL!')
    print('You need to fix orphaned records before adding foreign keys')
else:
    print('\n✅ SAFE TO ADD FOREIGN KEYS - No violations found')
