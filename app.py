import os
import re
from flask import Flask, jsonify, request, send_from_directory
import db

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')

app = Flask(__name__)

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
    genre = request.args.get("genre", "").strip()
    if genre:
        rows = db.fetchall("SELECT * FROM films WHERE LOWER(genre) = LOWER(%s) ORDER BY title", (genre,))
    else:
        rows = db.fetchall("SELECT * FROM films ORDER BY title")
    return jsonify([dict(r) for r in rows]), 200

@app.route("/api/films/<int:film_id>", methods=["GET"])
def get_film(film_id):
    film = db.fetchone("SELECT * FROM films WHERE id = %s", (film_id,))
    if not film:
        return jsonify({"error": "Film nem található"}), 404
    return jsonify(dict(film)), 200


@app.route("/api/screenings", methods=["GET"])
def list_screenings():
    film_id = request.args.get("film_id")
    if film_id is not None and not film_id.isdigit():
        return jsonify({"error": "A film_id egész szám kell legyen"}), 400
    sql = """
        SELECT s.*, f.title AS film_title, f.genre, f.duration_minutes,
               (s.rows * s.seats_per_row) AS total_seats,
               (s.rows * s.seats_per_row) - COUNT(bs.id) AS available_seats
        FROM screenings s
        JOIN films f ON f.id = s.film_id
        LEFT JOIN booked_seats bs ON bs.screening_id = s.id
        WHERE s.start_time > NOW() {filter}
        GROUP BY s.id, f.title, f.genre, f.duration_minutes
        ORDER BY s.start_time
    """
    if film_id:
        rows = db.fetchall(sql.format(filter="AND s.film_id = %s"), (film_id,))
    else:
        rows = db.fetchall(sql.format(filter=""))
    result = []
    for r in rows:
        d = dict(r)
        d["start_time"] = d["start_time"].isoformat()
        result.append(d)
    return jsonify(result), 200

@app.route("/api/screenings/<int:screening_id>", methods=["GET"])
def get_screening(screening_id):
    screening = db.fetchone("""
        SELECT s.*, f.title AS film_title, f.description AS film_description,
               f.genre, f.duration_minutes,
               (s.rows * s.seats_per_row) AS total_seats
        FROM screenings s
        JOIN films f ON f.id = s.film_id
        WHERE s.id = %s
    """, (screening_id,))
    if not screening:
        return jsonify({"error": "Vetítés nem található"}), 404
    booked = db.fetchall(
        "SELECT seat_row, seat_number FROM booked_seats WHERE screening_id = %s", (screening_id,)
    )
    result = dict(screening)
    result["start_time"] = result["start_time"].isoformat()
    result["booked_seats"] = [dict(r) for r in booked]
    return jsonify(result), 200


@app.route("/api/bookings", methods=["POST"])
def create_booking():
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

    screening = db.fetchone(
        "SELECT id, rows, seats_per_row FROM screenings WHERE id = %s AND start_time > NOW()",
        (screening_id,)
    )
    if not screening:
        return jsonify({"error": "Vetítés nem található"}), 404

    valid_rows = [chr(65 + i) for i in range(screening["rows"])]
    for seat in seats:
        if seat.get("row", "").upper() not in valid_rows:
            return jsonify({"error": f"Nem létező sor: {seat.get('row')}"}), 422
        if not (1 <= seat.get("number", 0) <= screening["seats_per_row"]):
            return jsonify({"error": f"Nem létező szék: {seat.get('number')}"}), 422
        taken = db.fetchone(
            "SELECT id FROM booked_seats WHERE screening_id = %s AND seat_row = %s AND seat_number = %s",
            (screening_id, seat["row"].upper(), seat["number"])
        )
        if taken:
            return jsonify({"error": f"A {seat['row'].upper()}{seat['number']} hely már foglalt"}), 409

    booking = db.fetchone(
        "INSERT INTO bookings (screening_id, customer_name, customer_email) VALUES (%s, %s, %s) RETURNING id, created_at",
        (screening_id, name, email)
    )
    booking_id = booking["id"]

    for seat in seats:
        db.execute(
            "INSERT INTO booked_seats (screening_id, booking_id, seat_row, seat_number) VALUES (%s, %s, %s, %s)",
            (screening_id, booking_id, seat["row"].upper(), seat["number"])
        )

    return jsonify({
        "booking_id": booking_id,
        "screening_id": screening_id,
        "customer_name": name,
        "customer_email": email,
        "seats": [{"row": s["row"].upper(), "number": s["number"]} for s in seats],
        "created_at": booking["created_at"].isoformat(),
    }), 201

@app.route("/api/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    booking = db.fetchone("""
        SELECT b.*, s.start_time, s.hall, f.title AS film_title
        FROM bookings b
        JOIN screenings s ON s.id = b.screening_id
        JOIN films f ON f.id = s.film_id
        WHERE b.id = %s
    """, (booking_id,))
    if not booking:
        return jsonify({"error": "Foglalás nem található"}), 404
    seats = db.fetchall(
        "SELECT seat_row, seat_number FROM booked_seats WHERE booking_id = %s", (booking_id,)
    )
    result = dict(booking)
    result["start_time"] = result["start_time"].isoformat()
    result["created_at"] = result["created_at"].isoformat()
    result["seats"] = [dict(r) for r in seats]
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)