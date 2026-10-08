from contextlib import asynccontextmanager, contextmanager
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo
import os
import sqlite3

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

DB_PATH = Path(os.getenv('BOOKING_DB', str(Path(__file__).with_name('bookings.sqlite3'))))
BERLIN = ZoneInfo('Europe/Berlin')

@contextmanager
def database():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    try:
        with db:
            yield db
    finally:
        db.close()

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with database() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER NOT NULL REFERENCES facilities(id),
                date TEXT NOT NULL,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                UNIQUE(facility_id, date, start)
            );
            INSERT OR IGNORE INTO facilities VALUES (1, 'Beachvolleyballplatz - Sportpark Ostra');
            INSERT OR IGNORE INTO facilities VALUES (2, 'Kunstrasenplatz - Sportpark Ostra');
            INSERT OR IGNORE INTO facilities VALUES (3, 'Basketballplatz - Löbtau-Süd');
        ''')

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title='Sportstätten-Buchung', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_methods=['GET', 'POST', 'DELETE'],
    allow_headers=['Content-Type'],
)

class BookingCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    facility_id: int = Field(default=1, gt=0)
    date: date
    start: str

    @field_validator('start')
    @classmethod
    def valid_start(cls, value):
        if value not in [f'{hour:02d}:00' for hour in range(9, 19)]:
            raise ValueError('Startzeit muss eine volle Stunde zwischen 09:00 und 18:00 sein.')
        return value

class BookingOut(BaseModel):
    id: int
    facility_id: int
    date: date
    start: str
    end: str

@app.get('/facilities')
def facilities():
    with database() as db:
        return [dict(row) for row in db.execute('SELECT * FROM facilities ORDER BY id')]

@app.get('/facilities/{facility_id}/bookings', response_model=list[BookingOut])
def list_bookings(facility_id: int, date: date):
    with database() as db:
        if not db.execute('SELECT id FROM facilities WHERE id=?', (facility_id,)).fetchone():
            raise HTTPException(404, 'Sportstätte nicht gefunden.')
        return [dict(row) for row in db.execute(
            'SELECT * FROM bookings WHERE facility_id=? AND date=? ORDER BY start',
            (facility_id, date.isoformat()),
        )]

@app.get('/bookings', response_model=list[BookingOut])
def all_bookings():
    with database() as db:
        return [dict(row) for row in db.execute(
            'SELECT * FROM bookings ORDER BY date, start, facility_id'
        )]

@app.post('/bookings', response_model=BookingOut, status_code=201)
def create_booking(booking: BookingCreate):
    start_dt = datetime.combine(booking.date, time.fromisoformat(booking.start), BERLIN)
    if start_dt <= datetime.now(BERLIN):
        raise HTTPException(422, 'Vergangene Zeitfenster können nicht gebucht werden.')
    end = f'{int(booking.start[:2]) + 1:02d}:00'
    try:
        with database() as db:
            if not db.execute('SELECT id FROM facilities WHERE id=?', (booking.facility_id,)).fetchone():
                raise HTTPException(404, 'Sportstätte nicht gefunden.')
            cursor = db.execute(
                'INSERT INTO bookings (facility_id, date, start, end) VALUES (?, ?, ?, ?)',
                (booking.facility_id, booking.date.isoformat(), booking.start, end),
            )
            return dict(db.execute('SELECT * FROM bookings WHERE id=?', (cursor.lastrowid,)).fetchone())
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'Dieses Zeitfenster ist bereits belegt.') from None
    except sqlite3.OperationalError as error:
        if 'locked' in str(error).lower():
            raise HTTPException(503, 'Datenbank ist ausgelastet. Erneut versuchen.') from None
        raise

@app.delete('/bookings/{booking_id}', status_code=204)
def cancel_booking(booking_id: int):
    with database() as db:
        cursor = db.execute('DELETE FROM bookings WHERE id=?', (booking_id,))
        if cursor.rowcount == 0:
            raise HTTPException(404, 'Buchung nicht gefunden.')
    return Response(status_code=204)
