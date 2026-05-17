import json
import pytest
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


class TestFilms:
    def test_list_films_returns_200(self, client):
        r = client.get("/api/films")
        assert r.status_code == 200

    def test_list_films_returns_list(self, client):
        r = client.get("/api/films")
        assert isinstance(json.loads(r.data), list)

    def test_list_films_not_empty(self, client):
        r = client.get("/api/films")
        assert len(json.loads(r.data)) > 0

    def test_list_films_genre_filter(self, client):
        r = client.get("/api/films?genre=Sci-Fi")
        assert r.status_code == 200
        for film in json.loads(r.data):
            assert film["genre"].lower() == "sci-fi"

    def test_get_film_returns_200(self, client):
        r = client.get("/api/films/1")
        assert r.status_code == 200

    def test_get_film_has_required_fields(self, client):
        data = json.loads(client.get("/api/films/1").data)
        assert "id" in data
        assert "title" in data
        assert "duration_minutes" in data

    def test_get_nonexistent_film_returns_404(self, client):
        r = client.get("/api/films/9999")
        assert r.status_code == 404


class TestScreenings:
    def test_list_screenings_returns_200(self, client):
        r = client.get("/api/screenings")
        assert r.status_code == 200

    def test_list_screenings_has_availability(self, client):
        data = json.loads(client.get("/api/screenings").data)
        assert all("available_seats" in s for s in data)

    def test_filter_by_film_id(self, client):
        r = client.get("/api/screenings?film_id=1")
        assert r.status_code == 200
        for s in json.loads(r.data):
            assert s["film_id"] == 1

    def test_invalid_film_id_returns_400(self, client):
        r = client.get("/api/screenings?film_id=abc")
        assert r.status_code == 400

    def test_get_screening_has_booked_seats(self, client):
        data = json.loads(client.get("/api/screenings/1").data)
        assert "booked_seats" in data

    def test_get_nonexistent_screening_returns_404(self, client):
        r = client.get("/api/screenings/9999")
        assert r.status_code == 404


class TestBookings:
    def test_missing_body_returns_400(self, client):
        r = client.post("/api/bookings", content_type="application/json")
        assert r.status_code == 400

    def test_invalid_email_returns_422(self, client):
        r = client.post("/api/bookings", json={
            "customer_name": "Teszt Elek",
            "customer_email": "nem-email",
            "screening_id": 1,
            "seats": [{"row": "A", "number": 1}]
        })
        assert r.status_code == 422

    def test_empty_seats_returns_422(self, client):
        r = client.post("/api/bookings", json={
            "customer_name": "Teszt Elek",
            "customer_email": "teszt@example.com",
            "screening_id": 1,
            "seats": []
        })
        assert r.status_code == 422

    def test_successful_booking_returns_201(self, client):
        r = client.post("/api/bookings", json={
            "customer_name": "Teszt Elek",
            "customer_email": "teszt@example.com",
            "screening_id": 1,
            "seats": [{"row": "A", "number": 1}]
        })
        assert r.status_code == 201
        data = json.loads(r.data)
        assert "booking_id" in data

    def test_double_booking_returns_409(self, client):
        payload = {
            "customer_name": "Teszt Elek",
            "customer_email": "teszt@example.com",
            "screening_id": 2,
            "seats": [{"row": "B", "number": 2}]
        }
        client.post("/api/bookings", json=payload)
        r = client.post("/api/bookings", json=payload)
        assert r.status_code == 409

    def test_get_nonexistent_booking_returns_404(self, client):
        r = client.get("/api/bookings/9999")
        assert r.status_code == 404

    def test_get_booking_returns_seats(self, client):
        create = client.post("/api/bookings", json={
            "customer_name": "Teszt Elek",
            "customer_email": "teszt@example.com",
            "screening_id": 3,
            "seats": [{"row": "C", "number": 3}]
        })
        booking_id = json.loads(create.data)["booking_id"]
        r = client.get(f"/api/bookings/{booking_id}")
        assert r.status_code == 200
        assert len(json.loads(r.data)["seats"]) == 1


class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
