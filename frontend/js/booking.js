let screening = null;
let selectedSeats = new Set();

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

function seatKey(row, num) {
  return `${row}${num}`;
}

function buildSeatMap(sc, bookedSeats) {
  const bookedSet = new Set(
    bookedSeats.map((s) => seatKey(s.seat_row, s.seat_number))
  );

  const mapEl = document.getElementById("seat-map");
  mapEl.innerHTML = "";

  for (let r = 0; r < sc.rows; r++) {
    const rowLetter = String.fromCharCode(65 + r);
    const rowDiv = document.createElement("div");
    rowDiv.className = "seat-row";

    const label = document.createElement("span");
    label.className = "row-label";
    label.textContent = rowLetter;
    rowDiv.appendChild(label);

    for (let n = 1; n <= sc.seats_per_row; n++) {
      const key = seatKey(rowLetter, n);
      const btn = document.createElement("button");
      btn.className = "seat";
      btn.dataset.row = rowLetter;
      btn.dataset.num = n;
      btn.title = `${rowLetter}${n}`;

      if (bookedSet.has(key)) {
        btn.classList.add("booked");
        btn.disabled = true;
      } else {
        btn.classList.add("available");
        btn.addEventListener("click", () => toggleSeat(btn, rowLetter, n));
      }
      rowDiv.appendChild(btn);
    }
    mapEl.appendChild(rowDiv);
  }
}

function toggleSeat(btn, row, num) {
  const key = seatKey(row, num);
  if (selectedSeats.has(key)) {
    selectedSeats.delete(key);
    btn.classList.replace("selected", "available");
  } else {
    selectedSeats.add(key);
    btn.classList.replace("available", "selected");
  }
  updateSelectionSummary();
}

function updateSelectionSummary() {
  const count = selectedSeats.size;
  document.getElementById("selected-count").textContent = count;
  document.getElementById("selected-labels").textContent =
    count ? [...selectedSeats].sort().join(", ") : "";
  document.getElementById("book-btn").disabled = count === 0;
}

function showError(msg) {
  const el = document.getElementById("form-error");
  el.textContent = msg;
  el.classList.remove("hidden");
}

function hideError() {
  document.getElementById("form-error").classList.add("hidden");
}

function showConfirmation(booking) {
  const seats = booking.seats.map((s) => `${s.row}${s.number}`).join(", ");
  document.getElementById("confirmation-details").innerHTML = `
    <div class="confirmation-row">
      <span><strong>Foglalás azonosítója:</strong> #${booking.booking_id}</span>
      <span><strong>Név:</strong> ${escapeHtml(booking.customer_name)}</span>
      <span><strong>E-mail:</strong> ${escapeHtml(booking.customer_email)}</span>
      <span><strong>Film:</strong> ${escapeHtml(screening.film_title)}</span>
      <span><strong>Dátum:</strong> ${formatDateTime(screening.start_time)}</span>
      <span><strong>Terem:</strong> ${escapeHtml(screening.hall)}</span>
      <span><strong>Helyek:</strong> ${escapeHtml(seats)}</span>
    </div>
  `;
  document.getElementById("confirmation-modal").classList.remove("hidden");
}

document.getElementById("book-btn").addEventListener("click", async () => {
  hideError();
  const name = document.getElementById("customer-name").value.trim();
  const email = document.getElementById("customer-email").value.trim();

  if (!name) { showError("Add meg a teljes neved."); return; }
  if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    showError("Adj meg egy érvényes e-mail címet."); return;
  }
  if (!selectedSeats.size) { showError("Válassz legalább egy helyet."); return; }

  const seats = [...selectedSeats].map((key) => ({
    row: key[0],
    number: parseInt(key.slice(1), 10),
  }));

  const btn = document.getElementById("book-btn");
  btn.disabled = true;
  btn.textContent = "Feldolgozás...";

  try {
    const booking = await api.createBooking({
      screening_id: screening.id,
      customer_name: name,
      customer_email: email,
      seats,
    });
    showConfirmation(booking);
  } catch (err) {
    showError(err.message);
    btn.disabled = false;
    btn.textContent = "Foglalás megerősítése";
  }
});

async function init() {
  const params = new URLSearchParams(window.location.search);
  const screeningId = params.get("screening_id");

  if (!screeningId) {
    window.location.href = "index.html";
    return;
  }

  try {
    screening = await api.getScreening(screeningId);

    document.getElementById("screening-title").textContent =
      `${screening.film_title} — ${screening.hall}`;

    document.getElementById("screening-meta").innerHTML = `
      <span>${formatDateTime(screening.start_time)}</span>
      <span>${escapeHtml(screening.hall)}</span>
      <span>${screening.duration_minutes} perc</span>
    `;

    document.getElementById("back-link").href =
      `screenings.html?film_id=${screening.film_id}`;

    buildSeatMap(screening, screening.booked_seats);
    updateSelectionSummary();
  } catch (err) {
    document.getElementById("seat-map").innerHTML =
      `<div class="empty-state">Hiba: ${err.message}</div>`;
  }
}

init();