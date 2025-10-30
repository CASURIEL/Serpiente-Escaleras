// =============================
// 👥 players.js — Renderizado de jugadores y avatares
// =============================

/**
 * Renderiza la lista de jugadores en el panel lateral.
 * @param {Array} players - Lista de jugadores del estado del juego
 * @param {number} currentPlayerIndex - Índice del jugador actual
 * @param {HTMLElement} container - Contenedor donde se insertará la lista
 */
export function renderPlayersList(players, currentPlayerIndex, container) {
    if (!container) return;
    
    container.innerHTML = "";
    
    if (!players || players.length === 0) {
        container.innerHTML = "<p>No hay jugadores</p>";
        return;
    }

    players.forEach((player, idx) => {
        const div = document.createElement("div");
        div.className = `player-info ${idx === currentPlayerIndex ? 'active' : ''}`;
        
        const colorClass = player.color.toLowerCase();
        div.style.backgroundColor = getColorHex(colorClass);
        div.style.color = "white";
        div.style.fontWeight = "bold";
        div.style.padding = "8px";
        div.style.borderRadius = "5px";
        div.style.margin = "5px 0";
        div.style.textAlign = "center";

        div.innerHTML = `${player.name} (Pos: ${player.position})`;
        container.appendChild(div);
    });
}

/**
 * Renderiza los avatares de los jugadores directamente en el tablero.
 * @param {Array} players - Lista de jugadores
 * @param {HTMLElement} boardContainer - Contenedor del tablero
 */
export function renderPlayerAvatars(players, boardContainer) {
    if (!boardContainer || !players) return;

    // Primero, eliminar avatares anteriores
    const existingAvatars = boardContainer.querySelectorAll('.player-avatar');
    existingAvatars.forEach(avatar => avatar.remove());

    players.forEach(player => {
        if (player.position <= 0) return; // No renderizar si no ha empezado

        // Encontrar la celda correspondiente
        const cell = boardContainer.querySelector(`.cell[data-number="${player.position}"]`);
        if (!cell) return;

        // Crear avatar
        const avatar = document.createElement("img");
        avatar.className = "player-avatar";
        avatar.src = `http://localhost:3000/img/Jugador${player.color}.png`; // URL completa
        avatar.alt = player.name;
        avatar.title = `${player.name} - Posición ${player.position}`;
        
        // Estilos para el avatar
        avatar.style.position = "absolute";
        avatar.style.width = "30px";
        avatar.style.height = "30px";
        avatar.style.borderRadius = "50%";
        avatar.style.border = "2px solid white";
        avatar.style.bottom = "5px";  // ← Posicionar en la parte inferior
        avatar.style.left = "50%";   // ← Centrar horizontalmente
        avatar.style.transform = "translateX(-50%)"; // ← Ajuste de centrado
        avatar.style.zIndex = "100";
        avatar.style.boxShadow = "0 2px 5px rgba(0,0,0,0.5)";

        // Añadir al contenedor de la celda
        const cellContent = cell.querySelector('img') || cell;
        // cellContent.style.position = "relative"; // ← Asegurar que la celda sea relativa
        // cellContent.style.overflow = "visible"; // ← Evitar que el avatar se corte
        cellContent.appendChild(avatar);
    });
}

// Función auxiliar: convertir nombre de color a hexadecimal
function getColorHex(colorName) {
    const colors = {
        rojo: "#FF0000",
        verde: "#00AA00",
        naranja: "#FF8C00",
        morado: "#800080",
        amarillo: "#FFD700",
        azul: "#0000FF"
    };
    return colors[colorName] || "#CCCCCC";
}