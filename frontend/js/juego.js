// =============================
// 🎮 juego.js — Lógica principal del juego
// =============================

import { renderPlayersList, renderPlayerAvatars } from './players.js';
import { renderBoard } from './celda.js';

const API_BASE = "http://localhost:3000/api";

// Declarar variables globales (pero no asignarlas aún)
let boardContainer, playersList, diceInput;
let gameState = null;

// =============================
// 📥 Cargar estado y renderizar
// =============================
async function loadGameState() {
    // Obtener elementos del DOM (asegurarse de que existan)
    boardContainer = document.getElementById("board");
    playersList = document.getElementById("playersList");
    diceInput = document.getElementById("dice-input");

    if (!boardContainer || !playersList || !diceInput) {
        console.error("❌ Elementos del DOM no encontrados");
        return;
    }

    try {
        // Cargar estado del juego
        const res = await fetch(`${API_BASE}/game/state`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        gameState = await res.json();

        // Renderizar lista de jugadores
        renderPlayersList(
            gameState.players,
            gameState.current_player_index,
            playersList
        );

        // Cargar y renderizar tablero
        const boardRes = await fetch(`${API_BASE}/board`);
        const boardData = await boardRes.json();
        renderBoard(boardData, gameState.players, boardContainer);

        // Renderizar avatares en el tablero
        renderPlayerAvatars(gameState.players, boardContainer);
        
    } catch (err) {
        console.error("Error al cargar el juego:", err);
        alert("⚠️ No se pudo conectar con el servidor.");
    }
}

// =============================
// 🎲 Mover jugador
// =============================
async function movePlayerManual() {
    // Asegurarse de que diceInput esté disponible
    if (!diceInput) {
        console.error("❌ Input de dado no encontrado");
        return;
    }

    const steps = parseInt(diceInput.value);
    if (isNaN(steps) || steps < 1 || steps > 6) {
        alert("Ingresa un número entre 1 y 6.");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/game/move`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ steps })
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Error ${res.status}`);
        }

        const result = await res.json();
        alert(result.message);

        if (result.victory) {
            alert(result.victory.message);
        }

        await loadGameState(); // Actualizar todo
    } catch (err) {
        console.error("Error al mover:", err);
        alert("⚠️ " + err.message);
    }
}

// =============================
// 🚀 Iniciar
// =============================
document.addEventListener("DOMContentLoaded", () => {
    loadGameState();
    
    // Añadir listener al botón después de que el DOM esté listo
    const moveButton = document.getElementById("moveButton");
    if (moveButton) {
        moveButton.addEventListener("click", movePlayerManual);
    }
});