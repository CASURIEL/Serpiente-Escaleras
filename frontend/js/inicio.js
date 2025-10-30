// ==============================
// MÓDULO DE ARRANQUE - inicio.js
// ==============================

// Estado inicial de jugadores (solo colores)
const jugadores = [
  { color: "ROJO", activo: true },
  { color: "VERDE", activo: true }
];

const MIN_JUGADORES = 2;
const MAX_JUGADORES = 6;
const COLORES_DISPONIBLES = ["ROJO", "VERDE", "NARANJA", "MORADO", "AMARILLO", "AZUL"];

// Elementos del DOM
const listaJugadores = document.getElementById("listaJugadores");
const btnAgregar = document.getElementById("btnAgregar");
const btnQuitar = document.getElementById("btnQuitar");
const btnComenzar = document.getElementById("btnComenzar");
const contadorJugadores = document.getElementById("contadorJugadores");

// ==============================
// FUNCIONES
// ==============================

function renderJugadores() {
  listaJugadores.innerHTML = "";
  jugadores.forEach(j => {
    const card = document.createElement("div");
    card.className = `jugador-card color-${j.color.toLowerCase()}`;
    card.textContent = j.color;
    listaJugadores.appendChild(card);
  });
  contadorJugadores.textContent = jugadores.length;
}

function agregarJugador() {
  if (jugadores.length < MAX_JUGADORES) {
    const siguienteColor = COLORES_DISPONIBLES[jugadores.length];
    jugadores.push({ color: siguienteColor, activo: true });
    renderJugadores();
  } else {
    alert(`Máximo permitido: ${MAX_JUGADORES} jugadores.`);
  }
}

function quitarJugador() {
  if (jugadores.length > MIN_JUGADORES) {
    jugadores.pop();
    renderJugadores();
  } else {
    alert(`Debe haber al menos ${MIN_JUGADORES} jugadores.`);
  }
}

async function comenzarJuego() {
  try {
    // Preparar datos para el backend
    const playerData = jugadores.map(j => ({
      name: j.color,
      color: j.color,
      position: 0,
      stats: { ladders: 0, snakes: 0 },
      avatar: `/img/${j.color}.png` // Opcional
    }));

    const response = await fetch("http://localhost:3000/api/game/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ players: playerData })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Error ${response.status}`);
    }

    // Redirigir al tablero
    window.location.href = "juego.html";

  } catch (error) {
    console.error("Error al iniciar el juego:", error);
    alert("⚠️ " + error.message);
  }
}

// ==============================
// EVENTOS
// ==============================
btnAgregar.addEventListener("click", agregarJugador);
btnQuitar.addEventListener("click", quitarJugador);
btnComenzar.addEventListener("click", comenzarJuego);

// Render inicial
renderJugadores();