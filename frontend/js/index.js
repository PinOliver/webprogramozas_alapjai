const GENRE_LABELS = {
  "Sci-Fi": "SF",
  "Action": "AK",
  "Drama": "DR",
  "Comedy": "KO",
  "Horror": "HO",
  "Romance": "RO",
};

function filmLabel(genre) {
  return GENRE_LABELS[genre] || "FM";
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderFilms(films) {
  const grid = document.getElementById("films-grid");
  if (!films.length) {
    grid.innerHTML = '<div class="empty-state">Nem találhatók filmek.</div>';
    return;
  }
  grid.innerHTML = films.map((f) => `
    <div class="film-card" onclick="goToScreenings(${f.id}, '${escapeHtml(f.title)}')">
      <div class="film-poster">${filmLabel(f.genre)}</div>
      <div class="film-info">
        <div class="genre">${escapeHtml(f.genre || "")}</div>
        <h3>${escapeHtml(f.title)}</h3>
        <p class="description">${escapeHtml(f.description || "")}</p>
        <div class="duration">${f.duration_minutes} perc</div>
      </div>
    </div>
  `).join("");
}

function goToScreenings(filmId, title) {
  window.location.href = `screenings.html?film_id=${filmId}&title=${encodeURIComponent(title)}`;
}

async function loadFilms(genre = "") {
  const grid = document.getElementById("films-grid");
  grid.innerHTML = '<div class="loading">Filmek betöltése...</div>';
  try {
    const films = await api.getFilms(genre);
    renderFilms(films);
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Hiba: ${err.message}</div>`;
  }
}

document.getElementById("genre-filter").addEventListener("change", (e) => {
  loadFilms(e.target.value);
});

loadFilms();