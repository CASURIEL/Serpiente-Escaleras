// =============================
// 🧱 celda.js — Renderizado del tablero con reglas (versión corregida)
// =============================

export function renderBoard(boardData, players, container) {
    if (!container) {
        console.error("❌ Contenedor del tablero no encontrado");
        return;
    }

    container.innerHTML = "";

    for (let i = boardData.rows.length - 1; i >= 0; i--) {
        const row = boardData.rows[i];
        const rowDiv = document.createElement("div");
        rowDiv.className = "row";

        const cellsDiv = document.createElement("div");
        cellsDiv.className = "row-cells";

        row.cells.forEach(cell => {
            const cellDiv = document.createElement("div");
            cellDiv.className = "cell"; // ← Usa la clase CSS definida en HTML
            cellDiv.dataset.number = cell.number;

            // Agregar número de celda
            const numberSpan = document.createElement("span");
            numberSpan.textContent = cell.number;
            numberSpan.style.fontSize = "0.7rem";
            numberSpan.style.fontWeight = "bold";
            numberSpan.style.position = "absolute";
            numberSpan.style.top = "5px";
            numberSpan.style.right = "5px";
            numberSpan.style.backgroundColor = "rgba(0,0,0,0.5)";
            numberSpan.style.padding = "2px 4px";
            numberSpan.style.borderRadius = "4px";
            numberSpan.style.color = "white";
            cellDiv.appendChild(numberSpan);

            // Si es especial, agregar clase
            if (cell.type === "especial") {
                cellDiv.classList.add("especial");
            }

            // Imagen de fondo (opcional)
            if (cell.image) {
                const img = document.createElement("img");
                img.src = cell.image;
                img.alt = "";
                img.style.width = "100%";
                img.style.height = "100%";
                img.style.objectFit = "cover";
                img.style.position = "absolute";
                img.style.top = "0";
                img.style.left = "0";
                img.style.zIndex = "-1"; // ← Detrás del texto y avatar
                cellDiv.appendChild(img);
            }

            // Aplicar estilo según jugador
            players.forEach(p => {
                if (p.position === cell.number) {
                    cellDiv.classList.add(`player-${p.color.toLowerCase()}`);
                    cellDiv.style.border = "3px solid white";
                    cellDiv.style.boxShadow = "0 0 10px rgba(255,255,255,0.8)";
                    cellDiv.style.overflow = "visible";
                }
            });

            cellsDiv.appendChild(cellDiv);
        });

        rowDiv.appendChild(cellsDiv);
        container.appendChild(rowDiv);
    }
}