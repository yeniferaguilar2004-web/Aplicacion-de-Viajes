const tripsContainer = document.querySelector("#trip-grid");
const tripSelect = document.querySelector("#trip-select");
const bookingForm = document.querySelector("#booking-form");
const reservationList = document.querySelector("#reservation-list");
const message = document.querySelector("#message");
const authForm = document.querySelector("#auth-form");
const nameField = document.querySelector("#name-field");
let trips = [];
let currentUser = null;
let isRegistering = false;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || "Ocurrió un error.");
  }
  return result;
}

function showMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle("error", isError);
}

function setAuthMode(registering) {
  isRegistering = registering;
  const nameInput = authForm.elements.name;
  nameField.hidden = !registering;
  nameInput.required = registering;
  nameInput.autocomplete = registering ? "name" : "off";
  authForm.elements.password.autocomplete = registering ? "new-password" : "current-password";
  document.querySelector("#auth-title").textContent = registering ? "Crear cuenta" : "Iniciar sesión";
  document.querySelector("#auth-submit").textContent = registering ? "Crear cuenta" : "Iniciar sesión";
  document.querySelector("#auth-switch-text").textContent =
    registering ? "¿Ya tienes cuenta?" : "¿No tienes cuenta?";
  document.querySelector("#auth-switch").textContent =
    registering ? "Iniciar sesión" : "Crear cuenta";
}

function showAuth() {
  currentUser = null;
  document.querySelector("#auth-panel").hidden = false;
  document.querySelector("#app-panel").hidden = true;
  document.querySelector("#app-nav").hidden = true;
}

function showApp(user) {
  currentUser = user;
  document.querySelector("#auth-panel").hidden = true;
  document.querySelector("#app-panel").hidden = false;
  document.querySelector("#app-nav").hidden = false;
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Buenos días" : hour < 19 ? "Buenas tardes" : "Buenas noches";
  document.querySelector("#user-greeting").textContent = `${greeting}, ${user.name}`;
  document.querySelector("#welcome-heading").textContent = `${greeting}, ${user.name}. ¡Buen viaje!`;
  bookingForm.elements.customer_name.value = user.name;
  bookingForm.elements.customer_email.value = user.email;
}

function localDateString(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function renderTrips() {
  tripsContainer.innerHTML = trips.map((trip) => `
    <article class="trip-card">
      <h3>${trip.emoji} ${escapeHtml(trip.city)}</h3>
      <p>${escapeHtml(trip.country)} · ${trip.days} días</p>
      <p>${escapeHtml(trip.description)}</p>
      <p><strong>${trip.price} USD por persona</strong></p>
      <button class="button" type="button" data-select-trip="${escapeHtml(trip.id)}">Elegir este destino</button>
    </article>
  `).join("");

  tripSelect.innerHTML = '<option value="">Selecciona un destino</option>' +
    trips.map((trip) => `<option value="${escapeHtml(trip.id)}">${escapeHtml(trip.city)}</option>`).join("");
}

function updatePrice() {
  const trip = trips.find((item) => item.id === tripSelect.value);
  const travelers = Number(document.querySelector("#travelers").value);
  document.querySelector("#price-total").textContent = trip
    ? `${trip.price * travelers} USD (${travelers} viajero(s), ${trip.days} días)`
    : "Selecciona un destino";
}

function renderReservations(reservations) {
  if (!reservations.length) {
    reservationList.textContent = "Todavía no tienes reservas.";
    return;
  }

  reservationList.innerHTML = reservations.map((reservation) => {
    const paidInDemo = reservation.payment_status === "demo_approved";
    return `
      <article class="reservation-card">
        <div>
          <h3>${escapeHtml(reservation.city)} — ${escapeHtml(reservation.customer_name)}</h3>
          <p>Salida: ${escapeHtml(reservation.departure_date)} · ${reservation.travelers} viajero(s)</p>
          <p>Total: ${reservation.total_price} USD · Estado: <span class="status">${reservation.status === "confirmed" ? "Confirmada (demostración)" : "Pendiente"}</span></p>
          ${paidInDemo ? `<p>Pago de prueba: ${reservation.payment_method === "pse" ? "PSE" : "Tarjeta"} · Sin cobro real</p>` : ""}
          ${reservation.ticket_code ? `<p>Ticket de demostración: <strong>${escapeHtml(reservation.ticket_code)}</strong></p>` : ""}
        </div>
        <div class="actions">
          ${reservation.status === "pending" ? `
            <button class="small-button" data-action="edit" data-id="${reservation.id}" type="button">Editar</button>
            <button class="small-button" data-action="pay" data-method="card" data-id="${reservation.id}" type="button">Probar tarjeta</button>
            <button class="small-button" data-action="pay" data-method="pse" data-id="${reservation.id}" type="button">Probar PSE</button>
          ` : `
            <button class="small-button" data-action="ticket" data-id="${reservation.id}" type="button">Ver ticket</button>
          `}
          <button class="small-button delete" data-action="delete" data-id="${reservation.id}" type="button">Eliminar</button>
        </div>
      </article>
    `;
  }).join("");
}

async function loadReservations() {
  reservationList.textContent = "Cargando reservas...";
  try {
    renderReservations(await api("/api/reservations"));
  } catch (error) {
    reservationList.textContent = error.message;
    if (error.message === "Inicia sesión para continuar.") showAuth();
  }
}

function showTicket(reservation) {
  const ticket = document.querySelector("#ticket");
  ticket.hidden = false;
  ticket.innerHTML = `
    <h3>Ticket de demostración</h3>
    <p class="demo-note">Este ticket pertenece a una simulación; no confirma un pago real.</p>
    <p><strong>Código:</strong> ${escapeHtml(reservation.ticket_code)}</p>
    <p><strong>Destino:</strong> ${escapeHtml(reservation.city)}, ${escapeHtml(reservation.country)}</p>
    <p><strong>Pasajero:</strong> ${escapeHtml(reservation.customer_name)}</p>
    <p><strong>Fecha:</strong> ${escapeHtml(reservation.departure_date)}</p>
    <p><strong>Viajeros:</strong> ${reservation.travelers}</p>
    <p><strong>Total estimado:</strong> ${reservation.total_price} USD</p>
  `;
  ticket.scrollIntoView({ behavior: "smooth", block: "center" });
}

function startEditing(reservation) {
  bookingForm.elements.reservation_id.value = reservation.id;
  bookingForm.elements.trip_id.value = reservation.trip_id;
  bookingForm.elements.customer_name.value = reservation.customer_name;
  bookingForm.elements.customer_email.value = reservation.customer_email;
  bookingForm.elements.departure_date.value = reservation.departure_date;
  bookingForm.elements.travelers.value = reservation.travelers;
  document.querySelector("#booking-title").textContent = "Editar reserva";
  document.querySelector("#booking-submit").textContent = "Guardar cambios";
  document.querySelector("#cancel-edit").hidden = false;
  updatePrice();
  document.querySelector("#reservar").scrollIntoView({ behavior: "smooth" });
}

function cancelEditing() {
  bookingForm.reset();
  bookingForm.elements.reservation_id.value = "";
  document.querySelector("#booking-title").textContent = "Cotizar y hacer una reserva";
  document.querySelector("#booking-submit").textContent = "Guardar reserva";
  document.querySelector("#cancel-edit").hidden = true;
  if (currentUser) {
    bookingForm.elements.customer_name.value = currentUser.name;
    bookingForm.elements.customer_email.value = currentUser.email;
  }
  updatePrice();
}

tripsContainer.addEventListener("click", (event) => {
  const button = event.target.closest("[data-select-trip]");
  if (!button) return;
  cancelEditing();
  tripSelect.value = button.dataset.selectTrip;
  updatePrice();
  document.querySelector("#reservar").scrollIntoView({ behavior: "smooth" });
});

tripSelect.addEventListener("change", updatePrice);
document.querySelector("#travelers").addEventListener("change", updatePrice);
document.querySelector("#departure-date").min = localDateString(new Date());
document.querySelector("#refresh-reservations").addEventListener("click", loadReservations);
document.querySelector("#cancel-edit").addEventListener("click", cancelEditing);

document.querySelector("#auth-switch").addEventListener("click", () => {
  setAuthMode(!isRegistering);
  showMessage("");
});

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.querySelector("#auth-submit");
  button.disabled = true;
  try {
    const data = Object.fromEntries(new FormData(authForm));
    const result = await api(isRegistering ? "/api/register" : "/api/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    authForm.reset();
    showApp(result.user);
    showMessage(isRegistering ? "Cuenta creada." : "Sesión iniciada.");
    await loadReservations();
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    button.disabled = false;
  }
});

bookingForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.querySelector("#booking-submit");
  button.disabled = true;
  try {
    const data = Object.fromEntries(new FormData(bookingForm));
    const reservationId = data.reservation_id;
    delete data.reservation_id;
    const result = await api(reservationId ? `/api/reservations/${reservationId}` : "/api/reservations", {
      method: reservationId ? "PUT" : "POST",
      body: JSON.stringify(data),
    });
    showMessage(result.message);
    cancelEditing();
    await loadReservations();
    document.querySelector("#mis-reservas").scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    button.disabled = false;
  }
});

reservationList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const id = button.dataset.id;

  try {
    if (button.dataset.action === "edit") {
      const reservations = await api("/api/reservations");
      const reservation = reservations.find((item) => String(item.id) === id);
      if (reservation) startEditing(reservation);
    } else if (button.dataset.action === "pay") {
      const methodName = button.dataset.method === "pse" ? "PSE" : "tarjeta";
      if (!window.confirm(`Iniciar una simulación de pago por ${methodName}. No se pedirán datos bancarios ni se realizará un cobro real. ¿Continuar?`)) return;
      const result = await api(`/api/reservations/${id}/payments`, {
        method: "POST",
        body: JSON.stringify({ method: button.dataset.method }),
      });
      showMessage(result.message);
      showTicket(result.reservation);
      await loadReservations();
    } else if (button.dataset.action === "delete") {
      if (!window.confirm("¿Seguro que quieres eliminar esta reserva?")) return;
      const result = await api(`/api/reservations/${id}`, { method: "DELETE" });
      showMessage(result.message);
      await loadReservations();
    } else if (button.dataset.action === "ticket") {
      const reservations = await api("/api/reservations");
      const reservation = reservations.find((item) => String(item.id) === id);
      if (reservation) showTicket(reservation);
    }
  } catch (error) {
    showMessage(error.message, true);
  }
});

document.querySelector("#logout-button").addEventListener("click", async () => {
  try {
    await api("/api/logout", { method: "POST" });
    showAuth();
    showMessage("Sesión cerrada.");
  } catch (error) {
    showMessage(error.message, true);
  }
});

async function startApp() {
  try {
    trips = await api("/api/trips");
    renderTrips();
    updatePrice();
    try {
      const result = await api("/api/me");
      showApp(result.user);
      await loadReservations();
    } catch (error) {
      if (error.message !== "Inicia sesión para continuar.") throw error;
      showAuth();
      reservationList.textContent = "Inicia sesión para consultar tus reservas.";
    }
  } catch (error) {
    showMessage(error.message, true);
    tripsContainer.textContent = error.message;
  }
}

startApp();
