from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import main


def test_booking_lifecycle_and_parallel_conflicts(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DB_PATH', tmp_path / 'test.sqlite3')
    tomorrow = (datetime.now(main.BERLIN) + timedelta(days=1)).date().isoformat()
    payload = {'facility_id': 1, 'date': tomorrow, 'start': '09:00'}
    with TestClient(main.app) as client:
        assert client.get('/facilities').json()[0]['name'] == 'Beachvolleyballplatz - Sportpark Ostra'
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: client.post('/bookings', json=payload), range(8)))
        assert sorted(r.status_code for r in results) == [201] + [409] * 7
        booking = next(r.json() for r in results if r.status_code == 201)
        assert booking['end'] == '10:00'
        assert len(client.get('/facilities/1/bookings', params={'date': tomorrow}).json()) == 1
        assert client.post('/bookings', json={**payload, 'start': '09:30'}).status_code == 422
        assert client.post('/bookings', json={**payload, 'date': '2000-01-01'}).status_code == 422
        assert client.post('/bookings', json={**payload, 'facility_id': 99}).status_code == 404
        assert client.delete(f"/bookings/{booking['id']}").status_code == 204
        assert client.delete(f"/bookings/{booking['id']}").status_code == 404
        assert client.post('/bookings', json=payload).status_code == 201
    with TestClient(main.app) as client:
        assert len(client.get('/facilities/1/bookings', params={'date': tomorrow}).json()) == 1
