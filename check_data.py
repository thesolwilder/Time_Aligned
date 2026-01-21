import json

d = json.load(open('data.json'))
print(f'Total sessions: {len(d)}')
s = list(d.values())[0]
print(f'Active periods: {len(s.get("active", []))}')
if s.get('active'):
    ap = s['active'][0]
    print(f'First active duration: {ap.get("duration")}')
