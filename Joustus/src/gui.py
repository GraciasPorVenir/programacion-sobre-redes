import os
import threading
import pygame
import queue
from client import Client
from models import SlotType

# Configuración inicial
WIDTH, HEIGHT = 800, 600
FPS = 30
CELL_SIZE = 80

BG_COLOR = (30, 30, 40)
NO_SLOT_COLOR = (20, 20, 20)
BORDER_COLOR = (60, 60, 70)
NORMAL_COLOR = (200, 200, 200)
GEM_COLOR = (255, 215, 0)
MY_CARD_COLOR = (100, 150, 255)
OPP_CARD_COLOR = (255, 100, 100)
TEXT_COLOR = (255, 255, 255)
SELECT_COLOR = (0, 255, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Joustus")
font = pygame.font.SysFont(None, 24)
title_font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 64)

HOST = "127.0.0.1"
PORT = 8091

# UI State globals
current_state = "MENU" # MENU, SETTINGS, GAME
is_fullscreen = False

# GAME variables
state_queue = queue.Queue()
c = None
selected_card_idx = None
selected_cell = None
push_options = []

def get_initial_game_state():
    return {
        "matrix": None,
        "hand": [],
        "turn": False,
        "message": "Conectando al servidor...",
        "me": "",
        "disconnected": False,
        "game_over": False
    }

game_state = get_initial_game_state()

def draw_arrows(surface, dirs, x, y, size):
    cx, cy = x + size//2, y + size//2
    offset = size // 3
    for d in dirs:
        if d == [0, -1] or d == (0,-1):
            pygame.draw.polygon(surface, (0,0,0), [(cx-offset, cy), (cx-offset+10, cy-5), (cx-offset+10, cy+5)])
        elif d == [0, 1] or d == (0,1):
            pygame.draw.polygon(surface, (0,0,0), [(cx+offset, cy), (cx+offset-10, cy-5), (cx+offset-10, cy+5)])
        elif d == [-1, 0] or d == (-1,0):
            pygame.draw.polygon(surface, (0,0,0), [(cx, cy-offset), (cx-5, cy-offset+10), (cx+5, cy-offset+10)])
        elif d == [1, 0] or d == (1,0):
            pygame.draw.polygon(surface, (0,0,0), [(cx, cy+offset), (cx-5, cy+offset-10), (cx+5, cy+offset-10)])

def connect_client():
    global c
    client = Client()
    if not client.connect(HOST, PORT):
        return None
    threading.Thread(target=network_thread, args=(client,), daemon=True).start()
    return client

def network_thread(client):
    while True:
        try:
            raw = client.receive()
            if not raw:
                state_queue.put({"type": "DISCONNECT"})
                break
            state_queue.put({"type": "UPDATE", "data": raw})
        except Exception:
            state_queue.put({"type": "DISCONNECT"})
            break

def start_game_mode(extra_row=0, extra_col=0, extra_gem=0):
    global game_state, c, current_state
    game_state = get_initial_game_state()
    if c: 
        try: c.disconnect() 
        except: pass
    
    c = connect_client()
    if not c:
        game_state["message"] = "Error al conectar"
        game_state["disconnected"] = True
    else:
        try: c.send({"type": "INIT_MODE", "extra_row": extra_row, "extra_col": extra_col, "extra_gem": extra_gem})
        except: pass
        
    current_state = "GAME"

def draw_menu():
    screen.fill(BG_COLOR)
    title = big_font.render("JOUSTUS", True, GEM_COLOR)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
    
    normal_rect = pygame.Rect(WIDTH//2 - 100, 200, 200, 50)
    extended_rect = pygame.Rect(WIDTH//2 - 100, 270, 200, 50)
    settings_rect = pygame.Rect(WIDTH//2 - 100, 340, 200, 50)
    rules_rect = pygame.Rect(WIDTH//2 - 100, 410, 200, 50)
    exit_rect = pygame.Rect(WIDTH//2 - 100, 480, 200, 50)
    
    buttons = [
        (normal_rect, "Modo Normal"),
        (extended_rect, "Modo Extendido"),
        (settings_rect, "Configuración"),
        (rules_rect, "Reglas"),
        (exit_rect, "Salir")
    ]
    
    for rect, text in buttons:
        pygame.draw.rect(screen, (50, 50, 60), rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 120), rect, 2, border_radius=5)
        txt = title_font.render(text, True, TEXT_COLOR)
        screen.blit(txt, (rect.x + rect.width//2 - txt.get_width()//2, rect.y + 12))
        
    return normal_rect, extended_rect, settings_rect, rules_rect, exit_rect

def draw_rules():
    screen.fill(BG_COLOR)
    title = big_font.render("Reglas de Joustus", True, TEXT_COLOR)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    rules_text = [
        "1. Coloca una carta en una celda vacía y elige hacia dónde empujar.",
        "2. Toda la fila se desplazará una celda en esa dirección.",
        "3. Las cartas sólo pueden defenderse si apuntan en dirección",
        "   contraria al empuje de la fila.",
        "4. Al final de la partida, el jugador con más cartas",
        "   sobre las gemas será el ganador.",
        "5. Las flechas rojas son las tuyas, las flechas azules son",
        "   las de tu rival."
    ]
    
    y = 150
    for line in rules_text:
        txt = font.render(line, True, (200, 200, 200))
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y))
        y += 35
        
    back_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 200, 50)
    pygame.draw.rect(screen, (50, 50, 60), back_rect, border_radius=5)
    pygame.draw.rect(screen, (100, 100, 120), back_rect, 2, border_radius=5)
    txt = title_font.render("Volver", True, TEXT_COLOR)
    screen.blit(txt, (back_rect.x + back_rect.width//2 - txt.get_width()//2, back_rect.y + 12))
    
    return back_rect

def draw_settings():
    screen.fill(BG_COLOR)
    title = big_font.render("Configuración", True, TEXT_COLOR)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    res1_rect = pygame.Rect(WIDTH//2 - 150, 150, 300, 50)
    res2_rect = pygame.Rect(WIDTH//2 - 150, 220, 300, 50)
    full_rect = pygame.Rect(WIDTH//2 - 150, 290, 300, 50)
    back_rect = pygame.Rect(WIDTH//2 - 150, 400, 300, 50)
    
    buttons = [
        (res1_rect, "Resolución: 800x600"),
        (res2_rect, "Resolución: 1024x768"),
        (full_rect, "Pantalla Completa: " + ("SI" if is_fullscreen else "NO")),
        (back_rect, "Volver")
    ]
    
    for rect, text in buttons:
        pygame.draw.rect(screen, (50, 50, 60), rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 120), rect, 2, border_radius=5)
        txt = title_font.render(text, True, TEXT_COLOR)
        screen.blit(txt, (rect.x + rect.width//2 - txt.get_width()//2, rect.y + 12))
        
    return res1_rect, res2_rect, full_rect, back_rect

def apply_resolution(w, h, full):
    global WIDTH, HEIGHT, is_fullscreen, screen, CELL_SIZE
    is_fullscreen = full
    flags = pygame.FULLSCREEN if full else 0
    if full:
        screen = pygame.display.set_mode((0, 0), flags)
        WIDTH, HEIGHT = screen.get_size()
    else:
        WIDTH, HEIGHT = w, h
        screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    CELL_SIZE = HEIGHT // 8

def draw_game():
    screen.fill(BG_COLOR)
    
    rows = len(game_state["matrix"]) if game_state["matrix"] else 5
    cols = len(game_state["matrix"][0]) if game_state["matrix"] and len(game_state["matrix"]) > 0 else 5
    
    BOARD_X = WIDTH//2 - (CELL_SIZE*cols)//2
    BOARD_Y = HEIGHT//2 - (CELL_SIZE*rows)//2 - 20
    
    lines = game_state["message"].split('\n')
    for i, line in enumerate(lines):
        msg_surface = title_font.render(line.strip(), True, TEXT_COLOR)
        screen.blit(msg_surface, (20, 10 + i*30))
    
    me_surface = font.render(f"Sos: {game_state['me']}", True, TEXT_COLOR)
    screen.blit(me_surface, (20, HEIGHT - 30))

    if game_state["matrix"]:
        for r in range(rows):
            for col in range(cols):
                slot = game_state["matrix"][r][col]
                t = SlotType(slot["type"])
                rect = pygame.Rect(BOARD_X + col * CELL_SIZE, BOARD_Y + r * CELL_SIZE, CELL_SIZE-2, CELL_SIZE-2)
                
                if t == SlotType.NO_SLOT: color = NO_SLOT_COLOR
                elif t == SlotType.BORDER: color = BORDER_COLOR
                elif t == SlotType.GEM: color = GEM_COLOR
                else: color = NORMAL_COLOR
                    
                pygame.draw.rect(screen, color, rect)
                
                if slot.get("card"):
                    card = slot["card"]
                    c_color = MY_CARD_COLOR if card["player"] == game_state["me"] else OPP_CARD_COLOR
                    pygame.draw.rect(screen, c_color, rect.inflate(-10, -10))
                    draw_arrows(screen, [d for d in card["directions"] if d], rect.x, rect.y, CELL_SIZE)

                if selected_cell == (r, col):
                    pygame.draw.rect(screen, SELECT_COLOR, rect, 3)

        hand_y = BOARD_Y + rows * CELL_SIZE + 20
        for i, card in enumerate(game_state["hand"]):
            rect = pygame.Rect(BOARD_X + i * (CELL_SIZE + 20), hand_y, CELL_SIZE, CELL_SIZE)
            color = MY_CARD_COLOR if selected_card_idx != i else SELECT_COLOR
            pygame.draw.rect(screen, color, rect)
            draw_arrows(screen, [d for d in card["directions"] if d], rect.x, rect.y, CELL_SIZE)

        if selected_cell is not None and selected_card_idx is not None and game_state["turn"] and not game_state.get("disconnected") and not game_state.get("game_over"):
            card = game_state["hand"][selected_card_idx]
            dirs = [d for d in card["directions"] if d]
            
            panel_rect = pygame.Rect(BOARD_X + cols*CELL_SIZE + 20, BOARD_Y, 150, 200)
            pygame.draw.rect(screen, (50, 50, 50), panel_rect)
            pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)
            
            txt = font.render("Elegir empuje:", True, TEXT_COLOR)
            screen.blit(txt, (panel_rect.x + 10, BOARD_Y + 10))
            
            global push_options
            push_options = []
            y_offset = BOARD_Y + 40
            for i, d in enumerate(dirs + [[0,0]]):
                opt_rect = pygame.Rect(panel_rect.x + 10, y_offset, 130, 30)
                pygame.draw.rect(screen, (80, 80, 80), opt_rect)
                dir_names = {(0,1): "Derecha ->", (0,-1): "Izquierda <-", (-1,0): "Arriba ^", (1,0): "Abajo v", (0,0): "Sin empuje"}
                label = font.render(dir_names.get(tuple(d), "Centro"), True, TEXT_COLOR)
                screen.blit(label, (opt_rect.x + 10, y_offset + 5))
                push_options.append({"rect": opt_rect, "dir": d})
                y_offset += 40

    if game_state.get("disconnected") or game_state.get("game_over"):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        y_center = HEIGHT//2
        if "Ganaste" in game_state["message"] or "Rival" in game_state["message"] or "Empate" in game_state["message"]:
            lines = game_state["message"].split('\n')
            for i, line in enumerate(lines):
                txt = big_font.render(line.strip(), True, GEM_COLOR if "Ganaste" in line else TEXT_COLOR)
                screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y_center - 100 + i*50))
        else:
            txt = title_font.render("Partida Terminada / Desconectado", True, TEXT_COLOR)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y_center - 100))
        
        menu_rect = pygame.Rect(WIDTH//2 - 150, y_center + 50, 300, 50)
        pygame.draw.rect(screen, (50, 100, 150), menu_rect, border_radius=5)
        txt = title_font.render("Volver al Menú Principal", True, TEXT_COLOR)
        screen.blit(txt, (menu_rect.x + 15, menu_rect.y + 12))
        return menu_rect
    return None

def main():
    global current_state, selected_card_idx, selected_cell, push_options, game_state, c
    
    clock = pygame.time.Clock()
    running = True

    try:
        while running:
            # Process Network Queue
            while not state_queue.empty():
                msg = state_queue.get()
                if msg["type"] == "DISCONNECT":
                    if not game_state.get("game_over"):
                        game_state["disconnected"] = True
                        game_state["turn"] = False
                elif msg["type"] == "UPDATE":
                    raw = msg["data"]
                    if "precard" in raw and game_state["hand"]:
                        if len(game_state["hand"]) < 3:
                            game_state["hand"].append(raw["newcard"])
                    elif "hand" in raw:
                        game_state["hand"] = raw["hand"]
                    
                    if raw.get("history"):
                        game_state["final_matrix"] = raw["matrix"]
                        import copy
                        curr_matrix = copy.deepcopy(game_state["matrix"])
                        game_state["animating"] = []
                        for diff in raw["history"]:
                            for change in diff:
                                curr_matrix[change["r"]][change["c"]]["card"] = change["card"]
                            game_state["animating"].append(copy.deepcopy(curr_matrix))
                            
                        game_state["anim_timer"] = pygame.time.get_ticks()
                        game_state["matrix"] = game_state["animating"].pop(0)
                    else:
                        game_state["matrix"] = raw["matrix"]
                        
                    game_state["turn"] = raw["turn"]
                    game_state["message"] = raw["message"]
                    
                    if "Ganaste" in raw["message"] or "Rival ganó" in raw["message"] or "Empate" in raw["message"]:
                        game_state["game_over"] = True
                        game_state["turn"] = False

                    if not game_state["me"]:
                        game_state["me"] = "Jugador 1" if raw.get("turn") else "Jugador 2"

            if game_state.get("animating"):
                current_time = pygame.time.get_ticks()
                if current_time - game_state.get("anim_timer", 0) > 400:
                    if len(game_state["animating"]) > 0:
                        game_state["matrix"] = game_state["animating"].pop(0)
                        game_state["anim_timer"] = current_time
                    else:
                        game_state["matrix"] = game_state.pop("final_matrix")
                        del game_state["animating"]

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    os._exit(0)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    
                    if current_state == "MENU":
                        normal_r, extended_r, set_r, rules_r, exit_r = draw_menu()
                        if normal_r.collidepoint(x, y):
                            start_game_mode(extra_row=0, extra_col=0, extra_gem=0)
                        elif extended_r.collidepoint(x, y):
                            start_game_mode(extra_row=1, extra_col=1, extra_gem=1)
                        elif set_r.collidepoint(x, y):
                            current_state = "SETTINGS"
                        elif rules_r.collidepoint(x, y):
                            current_state = "RULES"
                        elif exit_r.collidepoint(x, y):
                            os._exit(0)

                    elif current_state == "RULES":
                        back = draw_rules()
                        if back.collidepoint(x, y): current_state = "MENU"

                    elif current_state == "SETTINGS":
                        r1, r2, full, back = draw_settings()
                        if r1.collidepoint(x, y): apply_resolution(800, 600, is_fullscreen)
                        elif r2.collidepoint(x, y): apply_resolution(1024, 768, is_fullscreen)
                        elif full.collidepoint(x, y): apply_resolution(WIDTH, HEIGHT, not is_fullscreen)
                        elif back.collidepoint(x, y): current_state = "MENU"

                    elif current_state == "GAME":
                        if game_state.get("disconnected") or game_state.get("game_over"):
                            menu_rect = draw_game()
                            if menu_rect and menu_rect.collidepoint(x, y):
                                if c: 
                                    try: c.disconnect() 
                                    except: pass
                                current_state = "MENU"
                                continue

                        if game_state["turn"] and not game_state.get("disconnected") and not game_state.get("game_over"):
                            rows = len(game_state["matrix"]) if game_state["matrix"] else 5
                            cols = len(game_state["matrix"][0]) if game_state["matrix"] and len(game_state["matrix"]) > 0 else 5
                            
                            BOARD_X = WIDTH//2 - (CELL_SIZE*cols)//2
                            BOARD_Y = HEIGHT//2 - (CELL_SIZE*rows)//2 - 20
                            hand_y = BOARD_Y + rows * CELL_SIZE + 20
                            
                            for i in range(len(game_state["hand"])):
                                rect = pygame.Rect(BOARD_X + i * (CELL_SIZE + 20), hand_y, CELL_SIZE, CELL_SIZE)
                                if rect.collidepoint(x, y):
                                    selected_card_idx = i
                                    selected_cell = None
                            
                            if selected_card_idx is not None:
                                for r in range(rows):
                                    for c_col in range(cols):
                                        rect = pygame.Rect(BOARD_X + c_col * CELL_SIZE, BOARD_Y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                                        if rect.collidepoint(x, y):
                                            selected_cell = (r, c_col)
                            
                            if selected_card_idx is not None and selected_cell is not None:
                                for opt in push_options:
                                    if opt["rect"].collidepoint(x, y):
                                        vx, vy = opt["dir"]
                                        move = {
                                            "card": game_state["hand"][selected_card_idx],
                                            "x": selected_cell[0],
                                            "y": selected_cell[1],
                                            "vx": vx,
                                            "vy": vy
                                        }
                                        if c: c.send(move)
                                        game_state["hand"].pop(selected_card_idx)
                                        selected_card_idx = None
                                        selected_cell = None
                                        push_options = []
                                        game_state["turn"] = False
                                        game_state["message"] = "Enviando jugada..."
                                        break

            # Drawing
            if current_state == "MENU":
                draw_menu()
            elif current_state == "SETTINGS":
                draw_settings()
            elif current_state == "RULES":
                draw_rules()
            elif current_state == "GAME":
                draw_game()

            pygame.display.flip()
            clock.tick(FPS)
    except KeyboardInterrupt:
        os._exit(0)
    finally:
        try: pygame.quit()
        except: pass
        os._exit(0)

if __name__ == "__main__":
    main()