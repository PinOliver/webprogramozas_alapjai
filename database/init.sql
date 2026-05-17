CREATE TABLE IF NOT EXISTS films (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    genre VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS screenings (
    id SERIAL PRIMARY KEY,
    film_id INTEGER NOT NULL REFERENCES films(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    hall VARCHAR(50) NOT NULL,
    rows INTEGER NOT NULL DEFAULT 5 CHECK (rows > 0),
    seats_per_row INTEGER NOT NULL DEFAULT 10 CHECK (seats_per_row > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    screening_id INTEGER NOT NULL REFERENCES screenings(id) ON DELETE CASCADE,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS booked_seats (
    id SERIAL PRIMARY KEY,
    screening_id INTEGER NOT NULL REFERENCES screenings(id) ON DELETE CASCADE,
    booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    seat_row VARCHAR(5) NOT NULL,
    seat_number INTEGER NOT NULL CHECK (seat_number > 0),
    UNIQUE (screening_id, seat_row, seat_number)
);

CREATE INDEX IF NOT EXISTS idx_screenings_film_id ON screenings(film_id);
CREATE INDEX IF NOT EXISTS idx_booked_seats_screening ON booked_seats(screening_id);

INSERT INTO films (title, description, duration_minutes, genre) VALUES
('Inception',       'Egy tolvaj, aki álommegosztó technológiával lop vállalati titkokat, azt a feladatot kapja, hogy ültessen egy gondolatot egy vezérigazgató elméjébe.', 148, 'Sci-Fi'),
('The Dark Knight', 'Batman Gordon hadnagy és Harvey Dent ügyész segítségével új szintre emeli a bűnözők elleni harcát Gotham városában.',                               152, 'Action'),
('Interstellar',    'Felfedezők egy csapata féregjáraton át az űrbe utazik, hogy megtalálja az emberiség új otthonát a haldokló Föld helyett.',                         169, 'Sci-Fi'),
('Parasite',        'A kapzsiság és az osztálykülönbségek fenyegetik a gazdag Park család és a szegény Kim klán között kialakuló szimbiózist.',                         132, 'Drama'),
('Dune',            'Egy nemesi család kerül egy galaktikus háború középpontjába, amelynek tétje az univerzum legértékesebb nyersanyagának feletti uralom.',              155, 'Sci-Fi');

INSERT INTO screenings (film_id, start_time, hall, rows, seats_per_row) VALUES
(1, NOW() + INTERVAL '1 day 14 hours',  '1-es terem', 5, 10),
(1, NOW() + INTERVAL '1 day 18 hours',  '2-es terem', 5, 10),
(2, NOW() + INTERVAL '2 days 15 hours', '1-es terem', 5, 10),
(3, NOW() + INTERVAL '2 days 19 hours', '3-as terem', 5, 10),
(4, NOW() + INTERVAL '3 days 16 hours', '2-es terem', 5, 10),
(5, NOW() + INTERVAL '3 days 20 hours', '1-es terem', 5, 10);