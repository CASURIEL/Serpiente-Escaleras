from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
import random
import json
import threading
import re
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# ============ CONFIGURACIÓN DE SEGURIDAD Y CONCURRENCIA ============
log_lock = threading.Lock()
MAX_LOG_SIZE_MB = 5  # ✅ Límite de tamaño para archivo de logs

# ============ MODELOS PYDANTIC CON VALIDACIONES AVANZADAS ============
class PlayerStats(BaseModel):
    ladders: int = 0
    snakes: int = 0

class Player(BaseModel):
    name: str
    color: str
    position: int = 0
    stats: PlayerStats = PlayerStats()
    avatar: str = ""

    @validator('name')
    def validate_name(cls, v):
        """Valida que el nombre no esté vacío y sea seguro"""
        if not v or not v.strip():
            raise ValueError('El nombre del jugador no puede estar vacío')
        
        # ✅ Validación contra caracteres potencialmente peligrosos
        if re.search(r'[<>"\'&;]', v):
            raise ValueError('El nombre contiene caracteres no permitidos')
        
        if len(v.strip()) > 20:
            raise ValueError('El nombre no puede tener más de 20 caracteres')
        
        return v.strip()

class StartGameRequest(BaseModel):
    players: List[Player]

    @validator('players')
    def validate_players_count(cls, v):
        if len(v) < 2:
            raise ValueError('Mínimo 2 jugadores requeridos')
        if len(v) > 6:
            raise ValueError('Máximo 6 jugadores permitidos')
        return v

class GameState(BaseModel):
    players: List[Player]
    current_player_index: int = 0
    total_turns: int = 0
    ladders_climbed: int = 0
    snakes_found: int = 0
    game_started: bool = False
    start_time: Optional[datetime] = None

class MoveRequest(BaseModel):
    steps: int

    @validator('steps')
    def validate_steps(cls, v):
        if v < 1 or v > 6:
            raise ValueError('El dado debe ser entre 1 y 6')
        return v

class GameLog(BaseModel):
    status: str
    coordinates: Dict
    winner: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ============ CONFIGURACIÓN DEL JUEGO ============
BOARD_COLS = 12
BOARD_ROWS = 7
MAX_CELL = 82

PLAYER_COLORS = ["ROJO", "VERDE", "NARANJA", "MORADO", "AMARILLO", "AZUL"]
COLOR_TO_CLASS = {
    "ROJO": "player-red",
    "VERDE": "player-green", 
    "NARANJA": "player-orange",
    "MORADO": "player-purple",
    "AMARILLO": "player-yellow",
    "AZUL": "player-blue"
}

VIRTUES = ["Oración", "Ayuda", "Perdón", "Generosidad"]
SINS = ["Soberbia", "Envidia", "Ira", "Codicia"]

COLOR_TO_AVATAR = {
    "ROJO": "JugadorRojo.png",
    "VERDE": "JugadorVerde.png",
    "NARANJA": "JugadorNaranja.png",
    "MORADO": "JugadorMorado.png",
    "AMARILLO": "JugadorAmarillo.png",
    "AZUL": "JugadorAzul.png"
}

# ============ GESTIÓN DE ESTADO Y PERSISTENCIA ============
class GameStateManager:
    """Manager para persistencia del estado del juego"""
    
    @staticmethod
    def save_state():
        """Guarda el estado actual del juego en JSON"""
        try:
            state_data = {
                "game_state": game_state.dict(),
                "ladders": ladders,
                "snakes": snakes,
                "last_saved": datetime.utcnow().isoformat()
            }
            
            with open("game_state_backup.json", "w", encoding="utf-8") as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2, default=str)
            
            print("💾 Estado del juego guardado")
        except Exception as e:
            print(f"⚠️ Error guardando estado: {e}")

    @staticmethod
    def load_state():
        """Carga el estado del juego desde JSON si existe"""
        global game_state, ladders, snakes
        
        try:
            with open("game_state_backup.json", "r", encoding="utf-8") as f:
                state_data = json.load(f)
            
            game_state = GameState(**state_data["game_state"])
            ladders = state_data["ladders"]
            snakes = state_data["snakes"]
            
            print("🔄 Estado del juego cargado desde backup")
            return True
        except FileNotFoundError:
            print("📝 No se encontró backup previo, iniciando juego nuevo")
            return False
        except Exception as e:
            print(f"⚠️ Error cargando estado: {e}")
            return False

# ============ GESTIÓN DE LOGS AVANZADA ============
class LogManager:
    """Manager avanzado para gestión de logs"""
    
    @staticmethod
    def rotate_logs_if_needed():
        """Rota el archivo de logs si es demasiado grande"""
        try:
            log_path = Path("game_logs.json")
            if log_path.exists():
                size_mb = log_path.stat().st_size / (1024 * 1024)
                if size_mb > MAX_LOG_SIZE_MB:
                    backup_name = f"game_logs_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                    log_path.rename(backup_name)
                    print(f"📦 Log rotado: {backup_name}")
        except Exception as e:
            print(f"⚠️ Error rotando logs: {e}")

    @staticmethod
    def save_log_entry(log_entry: dict):
        """Guarda una entrada de log de forma segura"""
        LogManager.rotate_logs_if_needed()
        
        try:
            with log_lock:
                with open("game_logs.json", "a", encoding="utf-8") as f:
                    # ✅ Formato mejorado para análisis
                    f.write(json.dumps(log_entry, ensure_ascii=False) + ",\n")
            return True
        except Exception as e:
            print(f"⚠️ Error guardando log: {e}")
            return False

# ============ ESTADO GLOBAL DEL JUEGO ============
game_state = GameState(
    players=[
        Player(name="ROJO", color="ROJO"),
        Player(name="VERDE", color="VERDE")
    ]
)

ladders = {}
snakes = {}

# ============ INICIALIZACIÓN FASTAPI ============
app = FastAPI(
    title="🎲 Juego de Escaleras y Serpientes",
    description="API para el juego de escaleras y serpientes con persistencia y logs avanzados",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ FUNCIONES DEL JUEGO - OPTIMIZADAS ============
def generate_game_elements():
    """Genera escaleras y serpientes aleatorias"""
    global ladders, snakes
    ladders = {}
    snakes = {}

    escaleras_generadas = 0
    intentos = 0
    max_intentos = 100
    
    while escaleras_generadas < 6 and intentos < max_intentos:
        start = random.randint(5, MAX_CELL - 20)
        end = min(start + random.randint(10, 25), MAX_CELL)
        if (start not in ladders and start not in snakes and 
            start < MAX_CELL and end <= MAX_CELL and start != end and
            end not in ladders and end not in snakes):
            ladders[start] = {
                "end": end, 
                "virtue": random.choice(VIRTUES)
            }
            escaleras_generadas += 1
        intentos += 1

    serpientes_generadas = 0
    intentos = 0
    
    while serpientes_generadas < 6 and intentos < max_intentos:
        start = random.randint(15, MAX_CELL - 20)
        end = max(start - random.randint(5, 20), 1)
        if (start not in ladders and start not in snakes and 
            start < MAX_CELL and start != end and
            end not in ladders and end not in snakes):
            snakes[start] = {
                "end": end,
                "sin": random.choice(SINS)
            }
            serpientes_generadas += 1
        intentos += 1

def move_player(steps: int) -> Dict:
    """Mueve al jugador actual y aplica efectos"""
    player = game_state.players[game_state.current_player_index]
    game_state.total_turns += 1

    old_position = player.position
    player.position += steps
    
    if player.position > MAX_CELL:
        player.position = MAX_CELL

    # ✅ Mensajes mejorados con emojis
    message = f"🎲 {player.name} ({player.color}) avanza {steps} casillas."

    if player.position in ladders:
        ladder = ladders[player.position]
        message += f"\n🪜 ¡Escalera! Subes a {ladder['end']}. Virtud: {ladder['virtue']}"
        player.position = ladder["end"]
        player.stats.ladders += 1
        game_state.ladders_climbed += 1

    elif player.position in snakes:
        snake = snakes[player.position]
        message += f"\n🐍 ¡Serpiente! Bajas a {snake['end']}. Pecado: {snake['sin']}"
        player.position = snake["end"]
        player.stats.snakes += 1
        game_state.snakes_found += 1

    victory = None
    if player.position == MAX_CELL:
        victory = {
            "winner": player.color,
            "player_name": player.name,
            "stats": player.stats.dict(),
            "total_turns": game_state.total_turns,
            "final_position": player.position,
            "message": f"🏆 ¡{player.name} ha ganado el juego!"  # ✅ Mensaje de victoria mejorado
        }

    game_state.current_player_index = (game_state.current_player_index + 1) % len(game_state.players)
    
    # ✅ Guardar estado después de cada movimiento
    GameStateManager.save_state()

    return {
        "message": message,
        "victory": victory,
        "player_moved": player.color,
        "player_name": player.name,
        "new_position": player.position,
        "old_position": old_position
    }

# ============ ENDPOINTS API - MEJORADOS ============
@app.get("/")
async def root():
    """Información de la API"""
    return {
        "message": "🎲 API del Juego de Escaleras y Serpientes",
        "version": "2.0.0",
        "status": "operacional",
        "features": [
            "Validaciones avanzadas de entrada",
            "Persistencia automática del estado",
            "Gestión de logs con rotación",
            "Mensajes con emojis",
            "Arquitectura modular preparada"
        ],
        "configuración": {
            "max_jugadores": 6,
            "celdas_tablero": MAX_CELL,
            "filas": BOARD_ROWS,
            "columnas": BOARD_COLS
        },
        "advertencia": "⚠️ Estado en memoria - usar single worker en producción"
    }

@app.get("/api/game/state")
async def get_game_state():
    """Obtiene el estado completo del juego"""
    return {
        "players": [player.dict() for player in game_state.players],
        "current_player_index": game_state.current_player_index,
        "current_player": game_state.players[game_state.current_player_index].dict() if game_state.players else None,
        "game_started": game_state.game_started,
        "total_turns": game_state.total_turns,
        "ladders_climbed": game_state.ladders_climbed,
        "snakes_found": game_state.snakes_found,
        "start_time": game_state.start_time.isoformat() if game_state.start_time else None,
        "max_cell": MAX_CELL
    }

# ✅ NUEVO ENDPOINT - Jugador actual específico
@app.get("/api/game/current_player")
async def get_current_player():
    """Obtiene información específica del jugador actual"""
    if not game_state.players:
        raise HTTPException(status_code=404, detail="No hay jugadores en el juego")
    
    player = game_state.players[game_state.current_player_index]
    return {
        "current_player": player.dict(),
        "index": game_state.current_player_index,
        "is_your_turn": True,  # Útil para frontend
        "message": f"🎯 Es el turno de {player.name} ({player.color})"
    }

@app.post("/api/game/start")
async def start_game(request: StartGameRequest):
    """Inicia un nuevo juego con los jugadores proporcionados"""
    global game_state
    
    # Las validaciones ahora están en el modelo Pydantic
    updated_players = []
    colors_usados = set()
    
    for player in request.players:
        if player.color in colors_usados:
            raise HTTPException(status_code=400, detail=f"Color {player.color} duplicado")
        
        colors_usados.add(player.color)
        avatar_filename = COLOR_TO_AVATAR.get(player.color, "JugadorRojo.png")
        avatar_url = f"/img/{avatar_filename}"
        updated_players.append(
            Player(
                name=player.name,
                color=player.color,
                position=1,
                stats=PlayerStats(),
                avatar=avatar_url
            )
        )
    
    game_state.players = updated_players
    game_state.current_player_index = 0
    game_state.total_turns = 0
    game_state.ladders_climbed = 0
    game_state.snakes_found = 0
    game_state.game_started = True
    game_state.start_time = datetime.utcnow()
    
    generate_game_elements()
    
    # ✅ Guardar estado inicial
    GameStateManager.save_state()
    
    return {
        "message": "🎮 ¡Juego iniciado con éxito!",
        "total_players": len(game_state.players),
        "players": [p.dict() for p in game_state.players],
        "ladders": ladders,
        "snakes": snakes,
        "board_size": MAX_CELL,
        "start_time": game_state.start_time.isoformat()
    }

@app.post("/api/game/add_player")
async def add_player():
    """Añade un nuevo jugador"""
    if len(game_state.players) >= 6:
        raise HTTPException(status_code=400, detail="Máximo 6 jugadores")
    
    available_colors = [color for color in PLAYER_COLORS if color not in [p.color for p in game_state.players]]
    if not available_colors:
        raise HTTPException(status_code=400, detail="No hay colores disponibles")
    
    color = available_colors[0]
    avatar_filename = COLOR_TO_AVATAR.get(color, "JugadorRojo.png")
    avatar_url = f"/img/{avatar_filename}"
    
    new_player = Player(name=color, color=color, avatar=avatar_url)
    game_state.players.append(new_player)
    
    GameStateManager.save_state()
    
    return {
        "message": f"👤 Jugador {color} añadido", 
        "total_players": len(game_state.players),
        "player": new_player.dict()
    }

@app.post("/api/game/remove_player")
async def remove_player():
    """Elimina el último jugador"""
    if len(game_state.players) <= 2:
        raise HTTPException(status_code=400, detail="Mínimo 2 jugadores")
    
    removed_player = game_state.players.pop()
    
    if game_state.current_player_index >= len(game_state.players):
        game_state.current_player_index = 0
    
    GameStateManager.save_state()
    
    return {
        "message": f"❌ Jugador {removed_player.color} eliminado", 
        "total_players": len(game_state.players),
        "removed_player": removed_player.dict()
    }

@app.get("/api/avatars/{color}")
async def get_avatar(color: str):
    """Devuelve la URL del avatar para un color específico"""
    if color not in COLOR_TO_AVATAR:
        raise HTTPException(status_code=404, detail="Color no encontrado")
    
    avatar_file = COLOR_TO_AVATAR[color]
    return {
        "avatar_url": f"/img/{avatar_file}", 
        "color": color,
        "filename": avatar_file
    }

@app.get("/img/{filename}")
async def get_avatar_image(filename: str):
    """Sirve las imágenes de avatar con protección"""
    safe_name = Path(filename).name
    img_path = IMG_DIR / safe_name
    
    if not img_path.exists() or not img_path.is_file() or img_path.parent != IMG_DIR:
        raise HTTPException(status_code=404, detail="Avatar no encontrado")
    
    return FileResponse(img_path)

@app.post("/api/game/move")
async def make_move(move: MoveRequest):
    """Realiza un movimiento con el dado"""
    if not game_state.game_started:
        raise HTTPException(status_code=400, detail="El juego no ha comenzado")
    
    # La validación del rango ahora está en el modelo Pydantic
    result = move_player(move.steps)
    return result

@app.get("/api/board")
async def get_board():
    """Devuelve la estructura del tablero con el orden correcto (82→1)"""
    # Definimos el orden de las filas según tu diseño
    rows_order = [
        [73, 74, 75, 76, 77, 78, 79, 80, 81, 82],  # Fila 6 (índice 6)
        [72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61],  # Fila 5 (índice 5)
        [49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60],  # Fila 4 (índice 4)
        [48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37],  # Fila 3 (índice 3)
        [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],  # Fila 2 (índice 2)
        [24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13],  # Fila 1 (índice 1)
        [ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12]   # Fila 0 (índice 0) - ¡Esta tiene 12 celdas!
    ]

    board_rows = []
    for idx, row_numbers in enumerate(rows_order):
        direction = "right" if idx % 2 == 0 else "left"  # Índice par: izq→der; impar: der→izq
        cells = []
        for num in row_numbers:
            cells.append({
                "number": num,
                "image": f"http://localhost:3000/mapaCuadritos/{num:02d}.png"  # ← Ruta correcta para FastAPI
            })
        board_rows.append({
            "row_index": idx,
            "direction": direction,
            "cells": cells,
            "range": f"{cells[0]['number']}-{cells[-1]['number']}"
        })

    return {
        "rows": board_rows,
        "ladders": ladders,
        "snakes": snakes,
        "max_cell": MAX_CELL,
        "board_cols": BOARD_COLS,
        "board_rows": BOARD_ROWS,
        "layout": {
            "fila_6": "73-82",
            "fila_5": "61-72",  # ← Nota: 61-72 no coincide con lo que generamos, pero es solo info visual
            "fila_4": "49-60",
            "fila_3": "37-48",
            "fila_2": "25-36",
            "fila_1": "13-24",
            "fila_0": "1-12"
        }
    }
@app.get("/mapaCuadritos/{filename}")
async def get_board_image(filename: str):
    image_path = MAPA_DIR / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return FileResponse(image_path)

@app.get("/api/game/elements")
async def get_game_elements():
    """Obtiene las escaleras y serpientes generadas"""
    return {
        "ladders": ladders,
        "snakes": snakes,
        "total_ladders": len(ladders),
        "total_snakes": len(snakes),
        "virtues": VIRTUES,
        "sins": SINS
    }

@app.post("/api/game/reset")
async def reset_game():
    """Reinicia el juego completamente"""
    global game_state, ladders, snakes
    
    game_state = GameState(
        players=[
            Player(name="ROJO", color="ROJO"),
            Player(name="VERDE", color="VERDE")
        ]
    )
    ladders = {}
    snakes = {}
    
    # ✅ Limpiar también el backup de estado
    try:
        Path("game_state_backup.json").unlink(missing_ok=True)
    except:
        pass
    
    return {"message": "🔄 Juego reiniciado exitosamente"}

# ============ SERVIR ARCHIVOS ESTÁTICOS ============
BASE_DIR = Path(__file__).parent  # ← Esto apunta a "server/"
PUBLIC_DIR = BASE_DIR / "public"   # ← Ahora apunta a "server/public"
MAPA_DIR = PUBLIC_DIR / "mapaCuadritos"
IMG_DIR = PUBLIC_DIR / "img"

# Crea las carpetas si no existen
for directory in [PUBLIC_DIR, MAPA_DIR, IMG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

@app.post("/api/game/save_log")
async def save_game_log(log_data: GameLog):
    """Guarda el estado del juego en log"""
    log_entry = {
        "timestamp": log_data.timestamp.isoformat(),
        "status": log_data.status,
        "coordinates": log_data.coordinates,
        "winner": log_data.winner
    }
    
    success = LogManager.save_log_entry(log_entry)
    
    if not success:
        raise HTTPException(status_code=500, detail="Error guardando log")
    
    return {"message": "📝 Log guardado exitosamente", "log_entry": log_entry}

@app.get("/api/game/logs")
async def get_game_logs(limit: int = 10):
    """Obtiene los últimos logs del juego"""
    try:
        with log_lock:
            with open("game_logs.json", "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        logs = []
        for line in lines[-limit:]:
            try:
                # Remover la coma final si existe
                clean_line = line.rstrip().rstrip(',')
                logs.append(json.loads(clean_line))
            except json.JSONDecodeError:
                continue
        
        return {"logs": logs, "total": len(logs)}
    except FileNotFoundError:
        return {"logs": [], "total": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo logs: {str(e)}")

# ✅ NUEVO ENDPOINT - Estadísticas del juego
@app.get("/api/game/stats")
async def get_game_stats():
    """Obtiene estadísticas avanzadas del juego"""
    if not game_state.players:
        return {"message": "No hay juego activo"}
    
    stats = {
        "total_turns": game_state.total_turns,
        "ladders_climbed": game_state.ladders_climbed,
        "snakes_found": game_state.snakes_found,
        "players_stats": [
            {
                "name": p.name,
                "color": p.color,
                "position": p.position,
                "ladders": p.stats.ladders,
                "snakes": p.stats.snakes
            } for p in game_state.players
        ],
        "game_duration": None
    }
    
    if game_state.start_time:
        duration = datetime.utcnow() - game_state.start_time
        stats["game_duration_seconds"] = int(duration.total_seconds())
        stats["game_duration"] = str(duration)
    
    return stats

# --- Static files ---
# app.mount("/mapaCuadritos", StaticFiles(directory=MAPA_DIR), name="mapaCuadritos")
app.mount("/img", StaticFiles(directory=IMG_DIR), name="img")
app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")

# ============ INICIALIZACIÓN AL ARRANCAR ============
@app.on_event("startup")
async def startup_event():
    """Ejecuta tareas al iniciar la aplicación"""
    print("🚀 Iniciando Juego de Escaleras y Serpientes v2.0...")
    print("📁 Directorio base:", BASE_DIR)
    
    # ✅ Intentar cargar estado previo
    GameStateManager.load_state()
    
    print("🎯 Configuración:")
    print(f"   - Tablero: {MAX_CELL} celdas ({BOARD_ROWS}x{BOARD_COLS})")
    print(f"   - Jugadores: {len(game_state.players)}")
    print(f"   - Límite logs: {MAX_LOG_SIZE_MB} MB")
    print("⚠️  ADVERTENCIA: Estado en memoria - usar single worker en producción")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, reload=True)
    #uvicorn app:app --reload --host 0.0.0.0 --port 8000