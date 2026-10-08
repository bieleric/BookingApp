# Backend

FastAPI-REST-API mit SQLite über das Python-Modul `sqlite3`. Das Backend verwaltet Sportstätten und Buchungen und setzt die Buchungsregeln durch.

## Einrichtung und Start

Voraussetzung: Python 3.10+.

Im Ordner `backend`:

```bash
python -m venv .venv
```

Virtuelle Umgebung aktivieren:

```bash
# Linux/macOS
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Abhängigkeiten installieren und API starten:

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json

`--reload` ist für die lokale Entwicklung vorgesehen.

## Datenbank

Beim Start werden Tabellen und die initiale Sportstätte `Tennisplatz 1` mit ID 1 angelegt, sofern sie noch nicht existieren. Bestehende Buchungen bleiben erhalten.

Standardpfad: `bookings.sqlite3` neben `main.py`. Für einen anderen Pfad die Variable `BOOKING_DB` vor dem Prozessstart setzen:

```bash
# Linux/macOS
export BOOKING_DB=./data/bookings.sqlite3
```

```powershell
# Windows PowerShell
$env:BOOKING_DB = './data/bookings.sqlite3'
```

Die Elternverzeichnisse werden automatisch erstellt.

### Datenmodell

| Tabelle | Felder |
| --- | --- |
| `facilities` | `id`, `name` |
| `bookings` | `id`, `facility_id`, `date`, `start`, `end` |

Eine UNIQUE-Regel auf `(facility_id, date, start)` verhindert doppelte Buchungen desselben Stundenfensters, auch bei parallelen Anfragen. Das setzt das feste Stundenraster voraus und ersetzt keine allgemeine Überschneidungsprüfung für beliebige Zeiträume.

Weitere Sportstätten können direkt in SQLite ergänzt werden. Aktuell gibt es keine API zum Anlegen oder Bearbeiten von Sportstätten. Beispiel mit einem SQLite-Client:

```sql
INSERT INTO facilities (name) VALUES ('Tennisplatz 2');
```

## API

| Methode | Pfad | Funktion |
| --- | --- | --- |
| GET | `/facilities` | Alle Sportstätten |
| GET | `/bookings` | Alle Buchungen, nach Datum, Startzeit und Sportstätten-ID sortiert |
| GET | `/facilities/{facility_id}/bookings?date=YYYY-MM-DD` | Tagesbuchungen einer Sportstätte |
| POST | `/bookings` | Buchung erstellen |
| DELETE | `/bookings/{booking_id}` | Buchung löschen |

### Buchung erstellen

Anfrage an `POST /bookings`; ein zukünftiges Datum einsetzen:

```json
{
  "facility_id": 1,
  "date": "2027-01-15",
  "start": "09:00"
}
```

Antwort: HTTP 201, beispielsweise:

```json
{
  "id": 1,
  "facility_id": 1,
  "date": "2027-01-15",
  "start": "09:00",
  "end": "10:00"
}
```

Die Endzeit wird vom Backend berechnet und darf nicht im POST-Body mitgesendet werden. Nicht definierte Anfragefelder werden abgelehnt.

### Buchungsregeln

- Zeitangaben beziehen sich auf Europe/Berlin.
- Startzeiten sind volle Stunden von 09:00 bis einschließlich 18:00.
- Jeder Termin dauert genau 60 Minuten.
- Vergangene oder bereits gestartete Termine werden abgelehnt.
- Die Sportstätte muss existieren.

### Fehlercodes

| Status | Bedeutung |
| --- | --- |
| 404 | Sportstätte oder Buchung nicht gefunden |
| 409 | Stundenfenster bereits belegt |
| 422 | Ungültige Eingabe oder vergangener Termin |
| 503 | Datenbank beim Erstellen einer Buchung gesperrt bzw. ausgelastet |

Eine erfolgreiche Stornierung liefert HTTP 204 ohne Antwortinhalt. Die Buchung wird vollständig gelöscht.

## CORS

Für lokale Entwicklung sind `http://localhost:5173` und `http://127.0.0.1:5173` erlaubt. Bei einem anderen Frontend-Ursprung `allow_origins` in `main.py` anpassen.

Im Docker-Betrieb erfolgt der Zugriff über Nginx unter derselben Adresse wie das Frontend.

## Docker

Vom Projektstamm aus:

```bash
docker compose up --build -d
```

Uvicorn lauscht im Container auf `0.0.0.0:8000`. `BOOKING_DB` verweist auf `/data/bookings.sqlite3`; `/data` ist an ein persistentes Volume gebunden. Das Frontend erreicht die API intern über `backend:8000`.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Die mitgelieferten Tests prüfen parallele Buchungsanfragen, Eingabevalidierung, Stornierung, erneute Buchung, Persistenz sowie das Laden mehrerer Sportstätten und sämtlicher Buchungen. Sie verwenden temporäre Datenbanken.

## Einsatzumfang

Keine Authentifizierung und keine Berechtigungsprüfung. Alle Buchungen sind für API-Aufrufer lesbar und löschbar. Es werden keine personenbezogenen Buchungsdaten gespeichert. Für einen öffentlichen Betrieb müssen Zugriffsschutz und HTTPS ergänzt werden.