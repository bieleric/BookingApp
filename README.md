# Sportstätten-Buchung

Minimales Buchungssystem mit Vue 3, FastAPI und SQLite. Sportstätten und Buchungen werden aus der Datenbank geladen. Nutzer wählen eine Sportstätte, ein Datum und ein freies Stundenfenster.

## Funktionen

- Dynamische Sportstättenauswahl
- Datumsauswahl und Anzeige belegter Zeitfenster
- Buchung von 60-Minuten-Terminen zwischen 09:00 und 19:00 Uhr
- Ablehnung vergangener Termine und Schutz vor Doppelbuchungen
- Stornierung über die API
- Persistente Speicherung in SQLite

Alle Termine beziehen sich auf Europe/Berlin. Anmeldung, Berechtigungen und Zahlungen sind nicht implementiert.

## Projektstruktur

```text
.
├── compose.yaml
├── frontend/            # Vue 3 und Vite, Nginx im Container
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/App.vue
└── backend/             # FastAPI und SQLite
    ├── Dockerfile
    ├── main.py
    └── requirements.txt
```

## Start mit Docker

Voraussetzungen: Docker mit Compose-Unterstützung. Unter Windows muss Docker Desktop mit laufender Linux-Engine gestartet sein.

Im Projektstamm:

```bash
docker compose up --build -d
```

- Oberfläche: http://localhost:8080
- API: http://localhost:8080/api/facilities

Nginx liefert das Frontend aus und leitet `/api/` an das Backend weiter. Der Backend-Port ist in der vorgeschlagenen Compose-Konfiguration nicht am Host veröffentlicht.

```bash
# Logs ansehen
docker compose logs -f

# Container stoppen und entfernen; Daten bleiben erhalten
docker compose down

# Nach Codeänderungen neu bauen und starten
docker compose up --build -d
```

SQLite wird unter `/data/bookings.sqlite3` im benannten Volume `booking-data` gespeichert. Compose versieht den tatsächlichen Volume-Namen normalerweise mit einem Projektpräfix. Beim ersten Start entsteht eine neue Datenbank; eine vorhandene lokale Datenbank wird nicht automatisch importiert.

`docker compose down -v` löscht zusätzlich das Volume und damit die gespeicherten Buchungen.

## Lokale Entwicklung

Voraussetzungen: Python 3.10+ und eine Node.js-Version, die mit der Vite-Version des Projekts kompatibel ist. Der Docker-Build verwendet Node.js 22.

Backend und Frontend in getrennten Terminals starten. Die vollständigen Anleitungen stehen in [backend/README.md](backend/README.md) und [frontend/README.md](frontend/README.md).

Standardadressen:

| Dienst | Adresse |
| --- | --- |
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Interaktive API-Dokumentation | http://localhost:8000/docs |

## Konfiguration

| Variable | Verwendung | Standard |
| --- | --- | --- |
| `VITE_API_URL` | API-Basisadresse des Frontends; beim Build ausgewertet | `http://localhost:8000` |
| `BOOKING_DB` | SQLite-Dateipfad im Backend | `bookings.sqlite3` neben `main.py` |

Im Frontend-Docker-Build ist `VITE_API_URL=/api` gesetzt. Im Backend-Container ist `BOOKING_DB=/data/bookings.sqlite3` gesetzt.

## Prüfungen

```bash
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Der Frontend-Build wird mit `npm run build` im Ordner `frontend` geprüft.

## Einsatzumfang

Das Projekt ist ein Prototyp. Jeder API-Aufrufer kann alle Buchungen lesen, erstellen und löschen. Für einen öffentlichen Betrieb sind insbesondere Anmeldung, Berechtigungsprüfung und HTTPS erforderlich. Das Laden aller Buchungen ist für kleine Datenbestände vorgesehen.
