function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatDateTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString("hu-HU", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function availBadge(available, total) {
  const pct = available / total;
  let cls = "";
  if (available === 0) cls = "sold";
  else if (pct < 0.2) cls = "low";
  const label = available === 0 ? "Telt ház" : `${available} hely szabad`;
  return `<span class="avail-badge ${cls}">${label}</span>`;
}

function renderScreenings(screenings) {
  const list = document.getElementById("screenings-list");
  if (!screenings.length) {
    list.innerHTML = '<div class="empty-state">Nincs közelgő vetítés ehhez a filmhez.</div>';
    return;
  }
  list.innerHTML = screenings.map((s) => `
    <div class="screening-card">
      <div class="screening-info">
        <div class="datetime">${formatDateTime(s.start_time)}</div>
        <div class="hall">${escapeHtml(s.hall)}</div>
      </div>
      <div class="screening-availability">
        ${availBadge(s.available_seats, s.total_seats)}
        ${s.available_seats > 0
          ? `<button class="btn btn-primary" style="width:auto;padding:0.5rem 1.25rem"
               onclick="goToBooking(${s.id})">Helyek kiválasztása</button>`
          : ""}
      </div>
    </div>
  `).join("");
}

function goToBooking(screeningId) {
  window.location.href = `booking.html?screening_id=${screeningId}`;
}

async function init() {
  const params = new URLSearchParams(window.location.search);
  const filmId = params.get("film_id");
  const titleParam = params.get("title");

  if (titleParam) {
    document.getElementById("film-title").textContent = decodeURIComponent(titleParam);
  }

  if (filmId) {
    document.getElementById("back-link").href = "index.html";
  }

  const list = document.getElementById("screenings-list");
  list.innerHTML = '<div class="loading">Vetítések betöltése...</div>';

  try {
    const [screenings, film] = await Promise.all([
      api.getScreenings(filmId),
      filmId ? api.getFilm(filmId) : Promise.resolve(null),
    ]);

    if (film) {
      document.getElementById("film-title").textContent = film.title;
      document.getElementById("film-meta").innerHTML = `
        <span><strong>${escapeHtml(film.genre)}</strong></span>
        <span>${film.duration_minutes} perc</span>
        <span>${escapeHtml(film.description || "")}</span>
      `;
    }

    renderScreenings(screenings);
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Hiba: ${err.message}</div>`;
  }
}

init();