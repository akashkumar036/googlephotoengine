import urllib.request
import json

data = json.dumps({'email': 'admin@example.com', 'password': 'change-me-admin-password'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/auth/login', data=data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))['access_token']

questions = [
    "What kinds of old photos do users struggle to retrieve?",
    "What information do people actually remember about a photo?",
    "What information have they forgotten?",
    "How do users formulate searches when their memory is incomplete?"
]

for q in questions:
    payload = json.dumps({'query': q, 'limit': 4}).encode('utf-8')
    ask_req = urllib.request.Request(
        'http://127.0.0.1:8000/research/query',
        data=payload,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    )
    res = json.loads(urllib.request.urlopen(ask_req).read().decode('utf-8'))
    print("=" * 70)
    print("QUESTION:", q)
    print("SYNTHESIZED ANSWER:")
    print(res.get("answer"))
    print("\nRETRIEVED CITATIONS:")
    for ev in res.get("evidence", [])[:3]:
        title = ev.get("title") or ev.get("excerpt", "")[:70]
        print(f"  - [{ev.get('id')}] ({ev.get('source')}): {title}")
