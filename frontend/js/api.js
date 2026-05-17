const API_BASE = "/api";

async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const defaults = { headers: { "Content-Type": "application/json" } };
  const response = await fetch(url, { ...defaults, ...options });
  const data = await response.json();
  if (!response.ok) {
    const msg = data.error || (data.errors && data.errors.join(", ")) || "Ismeretlen hiba";
    throw new Error(msg);
  }
  return data;
}

const api = {
  getFilms: (genre) => {
    const qs = genre ? `?genre=${encodeURIComponent(genre)}` : "";
    return apiFetch(`/films${qs}`);
  },
  getFilm: (id) => apiFetch(`/films/${id}`),
  getScreenings: (filmId) => {
    const qs = filmId ? `?film_id=${filmId}` : "";
    return apiFetch(`/screenings${qs}`);
  },
  getScreening: (id) => apiFetch(`/screenings/${id}`),
  createBooking: (payload) =>
    apiFetch("/bookings", { method: "POST", body: JSON.stringify(payload) }),
  getBooking: (id) => apiFetch(`/bookings/${id}`),
};