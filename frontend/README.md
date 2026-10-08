# Frontend

Vue-3-Oberfläche mit Composition API und Vite für die Buchung von Sportstätten.

## Start

Im Ordner `frontend`:

```bash
npm ci
npm run dev
```

`npm ci` setzt eine vorhandene `package-lock.json` voraus. Fehlt diese, einmal `npm install` ausführen und die erzeugte Lockdatei versionieren.

Das Backend muss parallel laufen. Verwende lokal http://localhost:5173 oder http://127.0.0.1:5173; diese Ursprünge sind im Backend freigegeben. Weicht Vite auf einen anderen Port aus, muss die CORS-Konfiguration im Backend angepasst werden.

## API-Adresse

Standardmäßig verwendet `src/App.vue`:

```js
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

Für eine andere Adresse eine `.env.local` im Frontend-Ordner anlegen:

```dotenv
VITE_API_URL=http://localhost:8000
```

Danach Vite neu starten. Vite-Variablen werden in den Browsercode übernommen; dort keine Geheimnisse speichern.

## Datenfluss

Beim Öffnen werden Sportstätten und sämtliche Buchungen über die API geladen:

| Anfrage | Zweck |
| --- | --- |
| `GET /facilities` | Sportstätten für das Auswahlfeld |
| `GET /bookings` | Alle vorhandenen Buchungen |
| `POST /bookings` | Buchung für die ausgewählte Sportstätte erstellen |

Die Buchungen werden nach `facility_id` und ausgewähltem Datum gefiltert. Nach einem Buchungsversuch werden die Daten erneut geladen. Eine zwischenzeitliche Buchung durch einen anderen Nutzer wird serverseitig als Konflikt erkannt.

Die Oberfläche nutzt kein `localStorage`. Beim Wechsel von Sportstätte oder Datum wird die ausgewählte Uhrzeit zurückgesetzt. Während des Ladens, bei Ladefehlern und während einer Buchung sind Buchungsaktionen gesperrt.

Die Zeitfenster sind aktuell im Frontend fest auf 09:00–19:00 Uhr gesetzt. Die gleiche Regel gilt im Backend. Änderungen an Öffnungszeiten müssen in beiden Komponenten erfolgen.

## Build

```bash
npm run build
```

Das Ergebnis liegt in `dist/`.

## Docker

Vom Projektstamm aus:

```bash
docker compose up --build -d
```

Der mehrstufige Docker-Build installiert Abhängigkeiten mit `npm ci`, baut Vue und kopiert `dist/` in einen Nginx-Container. Die API-Adresse ist beim Build `/api`. Nginx entfernt beim Weiterleiten das Präfix `/api/` und erreicht den Compose-Dienst `backend` auf Port 8000.

Die Oberfläche ist unter http://localhost:8080 erreichbar. Änderungen am Quellcode erfordern einen erneuten Build.

## Logo

Die Logodatei beispielsweise als `public/logo.svg` ablegen und im Header nach dem Titelbereich einfügen:

```vue
<img src="/logo.svg" alt="Logo" style="height: 48px; width: auto;" />
```

## Grenzen

Stornierungen sind derzeit nur über die Backend-API verfügbar. Es gibt keine Benutzeranmeldung. Änderungen anderer Nutzer werden beim erneuten Laden und nach einem Buchungsversuch sichtbar; es gibt keine Live-Synchronisierung.