import os
import re
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

app = Flask(__name__)

films = [
    {"id": 1, "title": "Inception",       "description": "Egy tolvaj, aki álommegosztó technológiával lop vállalati titkokat, azt a feladatot kapja, hogy ültessen egy gondolatot egy vezérigazgató elméjébe.", "duration_minutes": 148, "genre": "Sci-Fi"},
    {"id": 2, "title": "The Dark Knight",  "description": "Batman Gordon hadnagy és Harvey Dent ügyész segítségével új szintre emeli a bűnözők elleni harcát Gotham városában.",                               "duration_minutes": 152, "genre": "Action"},
    {"id": 3, "title": "Interstellar",    "description": "Felfedezők egy csapata féregjáraton át az űrbe utazik, hogy megtalálja az emberiség új otthonát a haldokló Föld helyett.",                         "duration_minutes": 169, "genre": "Sci-Fi"},
    {"id": 4, "title": "Parasite",        "description": "A kapzsiság és az osztálykülönbségek fenyegetik a gazdag Park család és a szegény Kim klán között kialakuló szimbiózist.",                         "duration_minutes": 132, "genre": "Drama"},
    {"id": 5, "title": "Dune",            "description": "Egy nemesi család kerül egy galaktikus háború középpontjába, amelynek tétje az univerzum legértékesebb nyersanyagának feletti uralom.",              "duration_minutes": 155, "genre": "Sci-Fi"},
]

def make_screenings():
    now = datetime.now()
    return [
        {"id": 1, "film_id": 1, "start_time": (now + timedelta(days=1, hours=14)).isoformat(), "hall": "1-es terem", "rows": 5, "seats_per_row": 10},
        {"id": 2, "film_id": 1, "start_time": (now + timedelta(days=1, hours=18)).isoformat(), "hall": "2-es terem", "rows": 5, "seats_per_row": 10},
        {"id": 3, "film_id": 2, "start_time": (now + timedelta(days=2, hours=15)).isoformat(), "hall": "1-es terem", "rows": 5, "seats_per_row": 10},
        {"id": 4, "film_id": 3, "start_time": (now + timedelta(days=2, hours=19)).isoformat(), "hall": "3-as terem", "rows": 5, "seats_per_row": 10},
        {"id": 5, "film_id": 4, "start_time": (now + timedelta(days=3, hours=16)).isoformat(), "hall": "2-es terem", "rows": 5, "seats_per_row": 10},
        {"id": 6, "film_id": 5, "start_time": (now + timedelta(days=3, hours=20)).isoformat(), "hall": "1-es terem", "rows": 5, "seats_per_row": 10},
    ]

screenings = make_screenings()
booked_seats = []
bookings = []
next_booking_id = 1

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/films", methods=["GET"])
def list_films():
    genre = request.args.get("genre", "").strip().lower()
    result = films if not genre else [f for f in films if f["genre"].lower() == genre]
    return jsonify(result), 200

@app.route("/api/films/<int:film_id>", methods=["GET"])
def get_film(film_id):
    film = next((f for f in films if f["id"] == film_id), None)
    if not film:
        return jsonify({"error": "Film nem található"}), 404
    return jsonify(film), 200


@app.route("/api/screenings", methods=["GET"])
def list_screenings():
    film_id = request.args.get("film_id")
    if film_id is not None and not film_id.isdigit():
        return jsonify({"error": "A film_id egész szám kell legyen"}), 400
    result = screenings if not film_id else [s for s in screenings if s["film_id"] == int(film_id)]
    def with_availability(s):
        taken = sum(1 for b in booked_seats if b["screening_id"] == s["id"])
        total = s["rows"] * s["seats_per_row"]
        return {**s, "total_seats": total, "available_seats": total - taken}
    return jsonify([with_availability(s) for s in result]), 200

@app.route("/api/screenings/<int:screening_id>", methods=["GET"])
def get_screening(screening_id):
    screening = next((s for s in screenings if s["id"] == screening_id), None)
    if not screening:
        return jsonify({"error": "Vetítés nem található"}), 404
    film = next((f for f in films if f["id"] == screening["film_id"]), {})
    taken = [{"seat_row": b["seat_row"], "seat_number": b["seat_number"]}
             for b in booked_seats if b["screening_id"] == screening_id]
    return jsonify({
        **screening,
        "film_title": film.get("title", ""),
        "film_description": film.get("description", ""),
        "genre": film.get("genre", ""),
        "duration_minutes": film.get("duration_minutes", 0),
        "total_seats": screening["rows"] * screening["seats_per_row"],
        "booked_seats": taken,
    }), 200


@app.route("/api/bookings", methods=["POST"])
def create_booking():
    global next_booking_id
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON törzs szükséges"}), 400

    errors = []
    name         = (data.get("customer_name") or "").strip()
    email        = (data.get("customer_email") or "").strip()
    screening_id = data.get("screening_id")
    seats        = data.get("seats", [])

    if not name:                               errors.append("A név megadása kötelező")
    if not email or not EMAIL_RE.match(email): errors.append("Érvénytelen e-mail cím")
    if not isinstance(screening_id, int):      errors.append("A screening_id egész szám kell legyen")
    if not seats:                              errors.append("Legalább egy helyet ki kell választani")
    if errors:
        return jsonify({"errors": errors}), 422

    screening = next((s for s in screenings if s["id"] == screening_id), None)
    if not screening:
        return jsonify({"error": "Vetítés nem található"}), 404

    valid_rows = [chr(65 + i) for i in range(screening["rows"])]
    for seat in seats:
        if seat.get("row", "").upper() not in valid_rows:
            return jsonify({"error": f"Nem létező sor: {seat.get('row')}"}), 422
        if not (1 <= seat.get("number", 0) <= screening["seats_per_row"]):
            return jsonify({"error": f"Nem létező szék: {seat.get('number')}"}), 422
        if any(b["screening_id"] == screening_id
               and b["seat_row"] == seat["row"].upper()
               and b["seat_number"] == seat["number"]
               for b in booked_seats):
            return jsonify({"error": f"A {seat['row'].upper()}{seat['number']} hely már foglalt"}), 409

    booking_id = next_booking_id
    next_booking_id += 1
    created_at = datetime.now().isoformat()

    bookings.append({"id": booking_id, "screening_id": screening_id,
                     "customer_name": name, "customer_email": email, "created_at": created_at})
    for seat in seats:
        booked_seats.append({"screening_id": screening_id, "booking_id": booking_id,
                              "seat_row": seat["row"].upper(), "seat_number": seat["number"]})

    return jsonify({
        "booking_id": booking_id,
        "screening_id": screening_id,
        "customer_name": name,
        "customer_email": email,
        "seats": [{"row": s["row"].upper(), "number": s["number"]} for s in seats],
        "created_at": created_at,
    }), 201

@app.route("/api/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    booking = next((b for b in bookings if b["id"] == booking_id), None)
    if not booking:
        return jsonify({"error": "Foglalás nem található"}), 404
    screening = next((s for s in screenings if s["id"] == booking["screening_id"]), {})
    film = next((f for f in films if f["id"] == screening.get("film_id")), {})
    seats = [{"seat_row": b["seat_row"], "seat_number": b["seat_number"]}
             for b in booked_seats if b["booking_id"] == booking_id]
    return jsonify({**booking, "film_title": film.get("title", ""),
                    "hall": screening.get("hall", ""), "seats": seats}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)