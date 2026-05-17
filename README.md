# PintérMozi – Online Mozijegy Foglaló Rendszer

Webalkalmazás mozijegyek online foglalásához. Flask backend,  JS frontend, PostgreSQL adatbázis, Docker konténerizáció és GitHub Actions pipeline volt használva

---

## Tartalomjegyzék

- [Architektúra](#architektúra)
- [Telepítés és futtatás](#telepítés-és-futtatás)
- [Környezeti változók](#környezeti-változók)
- [API végpontok](#api-végpontok)
- [Tesztek](#tesztek)
- [Docker](#docker)
- [CI/CD pipeline](#cicd-pipeline)
- [Adatbázis séma](#adatbázis-séma)

---

## Architektúra

```
webprogramozas_alapjai/
├── app.py              
├── db.py               
├── test_api.py         
├── requirements.txt    
├── Dockerfile          
├── docker-compose.yml  
├── database/
│   └── init.sql        
├── frontend/
│   ├── index.html      
│   ├── screenings.html 
│   ├── booking.html    
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── api.js      
│       ├── index.js
│       ├── screenings.js
│       └── booking.js
└── .github/
    └── workflows/
        └── ci.yml      
```


---

## Telepítés és futtatás

### Docker (ajánlott)

```bash
git clone https://github.com/PinOliver/webprogramozas_alapjai.git
cd webprogramozas_alapjai
docker compose up --build
```

Az alkalmazás elérhető: `http://localhost:5000`

Az adatbázis séma és a kezdeti adatok automatikusan betöltődnek az első indításkor

### Lokális futtatás (Docker nélkül)

**Követelmények:** Python 3.12+, PostgreSQL 15+

```bash
createdb mozi
psql mozi < database/init.sql

pip3 install -r requirements.txt

export DATABASE_URL=postgresql://mozi:mozi@localhost:5432/mozi
python3 app.py
```

---

## Környezeti változók

| Változó | Alapértelmezett | Leírás |
|---|---|---|
| `DATABASE_URL` | `postgresql://mozi:mozi@localhost:5432/mozi` | PostgreSQL kapcsolati string |

---

## API végpontok

### Filmek

#### `GET /api/films`

Visszaadja az összes filmet.

**Query paraméter:**
- `genre` (opcionális) – szűrés műfajra

**Válasz `200`:**
```json
[
  {
    "id": 1,
    "title": "Inception",
    "description": "...",
    "duration_minutes": 148,
    "genre": "Sci-Fi"
  }
]
```

---

#### `GET /api/films/:id`

Egy film adatait adja vissza

**Válasz `200`:** Film objektum
**Válasz `404`:** `{ "error": "Film nem található" }`

---

### Vetítések

#### `GET /api/screenings`

Visszaadja az összes közelgő vetítést szabad helyek számával együtt

**Query paraméter:**
- `film_id`  szűrés filmre

**Válasz `200`:**
```json
[
  {
    "id": 1,
    "film_id": 1,
    "film_title": "Inception",
    "start_time": "2025-06-01T14:00:00",
    "hall": "1-es terem",
    "rows": 5,
    "seats_per_row": 10,
    "total_seats": 50,
    "available_seats": 48
  }
]
```

**Válasz `400`:** `{ "error": "A film_id egész szám kell legyen" }`

---

#### `GET /api/screenings/:id`

Egy vetítés adatait adja vissza a foglalt helyekkel együtt.

**Válasz `200`:**
```json
{
  "id": 1,
  "film_title": "Inception",
  "start_time": "2025-06-01T14:00:00",
  "hall": "1-es terem",
  "rows": 5,
  "seats_per_row": 10,
  "total_seats": 50,
  "booked_seats": [
    { "seat_row": "A", "seat_number": 1 }
  ]
}
```

**Válasz `404`:** `{ "error": "Vetítés nem található" }`

---

### Foglalások

#### `POST /api/bookings`

Új foglalást hoz létre. Ellenőrzi az ütközéseket.

**Kérés törzse:**
```json
{
  "screening_id": 1,
  "customer_name": "Kovács János",
  "customer_email": "kovacs@example.com",
  "seats": [
    { "row": "A", "number": 3 },
    { "row": "A", "number": 4 }
  ]
}
```

**Validációs szabályok:**
- `customer_name` – kötelező, max 255 karakter
- `customer_email` – kötelező, érvényes e-mail formátum
- `screening_id` – kötelező, pozitív egész szám, a vetítés nem kezdődhetett el
- `seats` – legalább egy elem, minden elemnek van `row` (A–E) és `number` (1–10) mezője

**Válasz `201`:**
```json
{
  "booking_id": 42,
  "screening_id": 1,
  "customer_name": "Kovács János",
  "customer_email": "kovacs@example.com",
  "seats": [{ "row": "A", "number": 3 }],
  "created_at": "2025-05-15T10:30:00"
}
```

**Válasz `409`:** Már foglalt hely – `{ "error": "Az A3 hely már foglalt" }`
**Válasz `422`:** Validációs hiba – `{ "errors": ["A név megadása kötelező"] }`
**Válasz `404`:** Vetítés nem található vagy már elkezdődött

---

#### `GET /api/bookings/:id`

Egy foglalás adatait adja vissza a helyekkel együtt.

**Válasz `200`:**
```json
{
  "id": 42,
  "film_title": "Inception",
  "hall": "1-es terem",
  "start_time": "2025-06-01T14:00:00",
  "customer_name": "Kovács János",
  "customer_email": "kovacs@example.com",
  "created_at": "2025-05-15T10:30:00",
  "seats": [{ "seat_row": "A", "seat_number": 3 }]
}
```

**Válasz `404`:** `{ "error": "Foglalás nem található" }`

---

#### `GET /api/health`

`{ "status": "ok" }` – az alkalmazás állapotának ellenőrzése.

---

## Tesztek

```bash
python -m pytest test_api.py -v
```

A tesztek futtatásához PostgreSQL szükséges. Docker környezetben:

```bash
docker compose up -d
docker exec -it <web_container> python -m pytest test_api.py -v
```

---

## Docker

### Image buildelése és indítása

```bash
docker compose up --build
```

### Leállítás és adatok törlése

```bash
docker compose down -v
```

### Docker Hub image használata

```bash
docker pull oliverpinter/pintermozi:latest
docker run -e DATABASE_URL=postgresql://... -p 5000:5000 oliverpinter/pintermozi:latest
```

---

## CI/CD pipeline

A `.github/workflows/ci.yml` pipeline minden `main` brancher menő  push esetén fut:

1. **Build and Push** – Buildeli a Docker imaget és feltölti a `oliverpinter/pintermozi:latest` taggel a Docker Hubra
2. **Test** – Pullolj a frissen feltöltött imaget, elindít egy PostgreSQL  containert, alkalmazza a sémát, majd a containeren belül lefuttatja a pytesteket

### Szükséges GitHub Secrets

| Secret | Leírás |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub felhasználónév |
| `DOCKERHUB_TOKEN` | Docker Hub access token |


---

## Adatbázis séma

```
films        (id, title, description, duration_minutes, genre, created_at)
screenings   (id, film_id → films, start_time, hall, rows, seats_per_row, created_at)
bookings     (id, screening_id → screenings, customer_name, customer_email, created_at)
booked_seats (id, screening_id → screenings, booking_id → bookings, seat_row, seat_number)
             UNIQUE (screening_id, seat_row, seat_number)
```