import sys
import random
import pygame
from enum import Enum

# ==========================================
# 1. RESOLUCIÓN Y CONFIGURACIÓN VISUAL
# ==========================================
WIDTH, HEIGHT = 800, 600
FPS = 30
CELL_SIZE = 75 

BG_COLOR = (30, 30, 40)
NO_SLOT_COLOR = (20, 20, 20)
BORDER_COLOR = (60, 60, 70)
NORMAL_COLOR = (200, 200, 200)
GEM_COLOR = (255, 215, 0)
P1_COLOR = (100, 150, 255)
P2_COLOR = (255, 100, 100)
TEXT_COLOR = (255, 255, 255)
SELECT_COLOR = (0, 255, 0)

# ==========================================
# 2. MAPEO DE CONTROLES ARCADE
# ==========================================
P1_CONTROLS = {
    'UP': pygame.K_UP, 'DOWN': pygame.K_DOWN, 'LEFT': pygame.K_LEFT, 'RIGHT': pygame.K_RIGHT,
    'BTN_O': pygame.K_o, 'BTN_Y': pygame.K_y, 'BTN_F': pygame.K_f, 'BTN_G': pygame.K_g,
    'BTN_X': pygame.K_x, 'BTN_C': pygame.K_c, 'BTN_V': pygame.K_v,
    'SELECT': pygame.K_y, 
    'CANCEL': pygame.K_x
}

P2_CONTROLS = {
    'UP': pygame.K_w, 'DOWN': pygame.K_s, 'LEFT': pygame.K_a, 'RIGHT': pygame.K_d,
    'BTN_ENTER': pygame.K_RETURN, 'BTN_SPACE': pygame.K_SPACE, 'BTN_H': pygame.K_h, 'BTN_J': pygame.K_j,
    'BTN_B': pygame.K_b, 'BTN_N': pygame.K_n, 'BTN_M': pygame.K_m,
    'SELECT': pygame.K_SPACE,
    'CANCEL': pygame.K_b
}

# ==========================================
# 3. MODELOS Y LÓGICA LOCAL
# ==========================================
class SlotType(Enum):
    NO_SLOT = 0
    BORDER = 1
    NORMAL = 2
    GEM = 3

class Card:
    def __init__(self, player):
        self.player = player
        posibles = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        self.directions = random.sample(posibles, k=random.randint(1, 3))

class Slot:
    def __init__(self, type_=SlotType.NORMAL):
        self.type = type_
        self.card = None

class TurnReq:
    def __init__(self, card, matrix, x, y, vx, vy):
        self.card = card
        self.matrix = matrix
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

class GameEngine:
    @staticmethod
    def create_matrix(extra_row=0, extra_col=0, extra_gem=0):
        rows, cols, gems = 5 + extra_row, 5 + extra_col, 3 + extra_gem
        matrix = [[Slot(SlotType.BORDER) for _ in range(cols)] for _ in range(rows)]
        for r, c in ((0,0), (0,cols-1), (rows-1,cols-1), (rows-1,0)):
            matrix[r][c].type = SlotType.NO_SLOT
        
        normal_coords = []
        for r in range(1, rows-1):
            for c in range(1, cols-1):
                matrix[r][c].type = SlotType.NORMAL
                normal_coords.append((r, c))
                
        for r, c in random.sample(normal_coords, k=gems):
            matrix[r][c].type = SlotType.GEM
        return matrix

    @staticmethod
    def check_movement(mv):
        if not (0 <= mv.x < len(mv.matrix) and 0 <= mv.y < len(mv.matrix[0])): return False
        slot = mv.matrix[mv.x][mv.y]
        if slot.card is not None or slot.type != SlotType.NORMAL: return False
        if mv.vx == 0 and mv.vy == 0: return True
        
        cx, cy = mv.x + mv.vx, mv.y + mv.vy
        while 0 <= cx < len(mv.matrix) and 0 <= cy < len(mv.matrix[0]):
            n_slot = mv.matrix[cx][cy]
            if n_slot.card is None: return n_slot.type != SlotType.NO_SLOT
            if [-mv.vx, -mv.vy] in n_slot.card.directions or (-mv.vx, -mv.vy) in n_slot.card.directions: 
                return False
            cx += mv.vx; cy += mv.vy
        return False

    @staticmethod
    def execute_movement(mv):
        mv.card.directions.clear()
        if mv.vx != 0 or mv.vy != 0: 
            mv.card.directions.append((mv.vx, mv.vy))
        mv.matrix[mv.x][mv.y].card = mv.card
        
        if mv.vx != 0 or mv.vy != 0:
            train = []
            cx, cy = mv.x, mv.y
            while 0 <= cx < len(mv.matrix) and 0 <= cy < len(mv.matrix[0]):
                c = mv.matrix[cx][cy].card
                if not c: break
                train.append(c)
                cx += mv.vx; cy += mv.vy
            
            mv.matrix[mv.x][mv.y].card = None
            cx, cy = mv.x, mv.y
            for c in train:
                cx += mv.vx; cy += mv.vy
                if 0 <= cx < len(mv.matrix) and 0 <= cy < len(mv.matrix[0]):
                    mv.matrix[cx][cy].card = c
        return mv.matrix

    @staticmethod
    def handle_endgame(matrix):
        p = {"Jugador 1": 0, "Jugador 2": 0}
        for row in matrix:
            for slot in row:
                if slot.type == SlotType.GEM and slot.card:
                    p[slot.card.player] += 1
        if p["Jugador 1"] == p["Jugador 2"]: return "EMPATE", p
        return max(p, key=p.get), p

# ==========================================
# 4. MOTOR GRÁFICO Y BUCLE LOCAL
# ==========================================
def draw_arrows(surface, dirs, x, y, size):
    cx, cy = x + size//2, y + size//2
    offset = size // 3
    for d in dirs:
        if d == [0, -1] or d == (0,-1): pygame.draw.polygon(surface, (0,0,0), [(cx-offset, cy), (cx-offset+10, cy-5), (cx-offset+10, cy+5)])
        elif d == [0, 1] or d == (0,1): pygame.draw.polygon(surface, (0,0,0), [(cx+offset, cy), (cx+offset-10, cy-5), (cx+offset-10, cy+5)])
        elif d == [-1, 0] or d == (-1,0): pygame.draw.polygon(surface, (0,0,0), [(cx, cy-offset), (cx-5, cy-offset+10), (cx+5, cy-offset+10)])
        elif d == [1, 0] or d == (1,0): pygame.draw.polygon(surface, (0,0,0), [(cx, cy+offset), (cx-5, cy+offset-10), (cx+5, cy+offset-10)])

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Joustus - Arcade Unificado")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont(None, 24)
    title_font = pygame.font.SysFont(None, 36)
    big_font = pygame.font.SysFont(None, 64)

    app_state = "MENU"
    menu_options = ["Modo Normal", "Modo Extendido", "Reglas", "Salir"]
    menu_idx = 0
    
    matrix = None
    rows, cols = 0, 0
    hands = {}
    current_turn = "Jugador 1"
    
    cursor = {'x': 0, 'y': 0, 'state': 'HAND'} 
    selected_card_idx = None
    selected_cell = None
    push_options = []
    push_idx = 0
    game_over = False
    message = ""

    def start_game(extra_row, extra_col, extra_gem):
        nonlocal matrix, rows, cols, hands, current_turn, game_over, message, cursor
        matrix = GameEngine.create_matrix(extra_row, extra_col, extra_gem)
        rows, cols = len(matrix), len(matrix[0])
        hands = {"Jugador 1": [Card("Jugador 1") for _ in range(3)], "Jugador 2": [Card("Jugador 2") for _ in range(3)]}
        current_turn = "Jugador 1"
        game_over = False
        cursor = {'x': 0, 'y': 0, 'state': 'HAND'}

    running = True
    while running:
        controls = P1_CONTROLS if current_turn == "Jugador 1" or app_state != "GAME" else P2_CONTROLS
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if app_state == "MENU":
                    if event.key == controls['DOWN']:
                        menu_idx = (menu_idx + 1) % len(menu_options)
                    elif event.key == controls['UP']:
                        menu_idx = (menu_idx - 1) % len(menu_options)
                    elif event.key == controls['SELECT']:
                        if menu_idx == 0:
                            start_game(0, 0, 0)
                            app_state = "GAME"
                        elif menu_idx == 1:
                            start_game(1, 1, 1)
                            app_state = "GAME"
                        elif menu_idx == 2:
                            app_state = "RULES"
                        elif menu_idx == 3:
                            running = False

                elif app_state == "RULES":
                    if event.key in (controls['SELECT'], controls['CANCEL']):
                        app_state = "MENU"
                        
                elif app_state == "GAME":
                    if game_over:
                        if event.key in (controls['SELECT'], controls['CANCEL']):
                            app_state = "MENU"
                        continue

                    if event.key == controls['RIGHT']:
                        if cursor['state'] == 'HAND': cursor['x'] = min(cursor['x'] + 1, len(hands[current_turn])-1)
                        elif cursor['state'] == 'BOARD': cursor['x'] = min(cursor['x'] + 1, cols-1)
                        elif cursor['state'] == 'PUSH': push_idx = min(push_idx + 1, len(push_options)-1)
                    elif event.key == controls['LEFT']:
                        if cursor['state'] == 'HAND': cursor['x'] = max(cursor['x'] - 1, 0)
                        elif cursor['state'] == 'BOARD': cursor['x'] = max(cursor['x'] - 1, 0)
                        elif cursor['state'] == 'PUSH': push_idx = max(push_idx - 1, 0)
                    elif event.key == controls['DOWN']:
                        if cursor['state'] == 'BOARD': cursor['y'] = min(cursor['y'] + 1, rows-1)
                        elif cursor['state'] == 'PUSH': push_idx = min(push_idx + 1, len(push_options)-1)
                    elif event.key == controls['UP']:
                        if cursor['state'] == 'BOARD': cursor['y'] = max(cursor['y'] - 1, 0)
                        elif cursor['state'] == 'PUSH': push_idx = max(push_idx - 1, 0)
                    
                    elif event.key == controls['SELECT']:
                        if cursor['state'] == 'HAND':
                            selected_card_idx = cursor['x']
                            cursor['state'] = 'BOARD'
                            cursor['x'], cursor['y'] = cols//2, rows//2 
                        elif cursor['state'] == 'BOARD':
                            if matrix[cursor['y']][cursor['x']].type == SlotType.NORMAL and matrix[cursor['y']][cursor['x']].card is None:
                                selected_cell = (cursor['y'], cursor['x'])
                                cursor['state'] = 'PUSH'
                                push_idx = 0
                                card_dirs = hands[current_turn][selected_card_idx].directions
                                push_options = [d for d in card_dirs] + [(0,0)] 
                                
                        elif cursor['state'] == 'PUSH':
                            vx, vy = push_options[push_idx]
                            req = TurnReq(hands[current_turn][selected_card_idx], matrix, selected_cell[0], selected_cell[1], vx, vy)
                            if GameEngine.check_movement(req):
                                matrix = GameEngine.execute_movement(req)
                                hands[current_turn].pop(selected_card_idx)
                                hands[current_turn].append(Card(current_turn))
                                
                                empty_slots = any(s.type == SlotType.NORMAL and s.card is None for row in matrix for s in row)
                                if not empty_slots:
                                    winner, scores = GameEngine.handle_endgame(matrix)
                                    if winner == "EMPATE":
                                        message = "¡EMPATE!"
                                    else:
                                        message = f"¡Ganó el {winner}! ({scores[winner]} gemas)"
                                    game_over = True
                                else:
                                    current_turn = "Jugador 2" if current_turn == "Jugador 1" else "Jugador 1"
                                    cursor = {'x': 0, 'y': 0, 'state': 'HAND'}
                            else:
                                message = "Movimiento inválido."
                                cursor['state'] = 'BOARD'
                                
                    elif event.key == controls['CANCEL']:
                        if cursor['state'] == 'BOARD': cursor['state'] = 'HAND'; cursor['x'] = 0
                        elif cursor['state'] == 'PUSH': cursor['state'] = 'BOARD'

        screen.fill(BG_COLOR)
        
        if app_state == "MENU":
            title = big_font.render("JOUSTUS", True, GEM_COLOR)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
            
            for i, opt in enumerate(menu_options):
                rect = pygame.Rect(WIDTH//2 - 120, 230 + i * 70, 240, 50)
                color_bg = (80, 150, 80) if i == menu_idx else (50, 50, 60)
                pygame.draw.rect(screen, color_bg, rect, border_radius=5)
                pygame.draw.rect(screen, (100, 100, 120), rect, 2, border_radius=5)
                txt = title_font.render(opt, True, TEXT_COLOR)
                screen.blit(txt, (rect.x + rect.width//2 - txt.get_width()//2, rect.y + 12))
                
        elif app_state == "RULES":
            title = big_font.render("Reglas de Joustus", True, TEXT_COLOR)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
            rules = [
                "1. Coloca una carta en una celda vacía y elige el empuje.",
                "2. La fila se desplazará. Las flechas indican tu defensa.",
                "3. El jugador con más gemas al llenarse el tablero gana.",
                " ",
                "[Presiona SELECCIÓN o ATRÁS para volver]"
            ]
            for i, text in enumerate(rules):
                txt = font.render(text, True, TEXT_COLOR)
                screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 150 + i * 40))
                
        elif app_state == "GAME":
            board_x = WIDTH//2 - (CELL_SIZE*cols)//2
            board_y = HEIGHT//2 - (CELL_SIZE*rows)//2
            
            for r in range(rows):
                for c in range(cols):
                    slot = matrix[r][c]
                    rect = pygame.Rect(board_x + c * CELL_SIZE, board_y + r * CELL_SIZE, CELL_SIZE-2, CELL_SIZE-2)
                    color = NO_SLOT_COLOR if slot.type == SlotType.NO_SLOT else BORDER_COLOR if slot.type == SlotType.BORDER else GEM_COLOR if slot.type == SlotType.GEM else NORMAL_COLOR
                    pygame.draw.rect(screen, color, rect)
                    
                    if slot.card:
                        card_color = P1_COLOR if slot.card.player == "Jugador 1" else P2_COLOR
                        pygame.draw.rect(screen, card_color, rect.inflate(-10, -10))
                        draw_arrows(screen, slot.card.directions, rect.x, rect.y, CELL_SIZE)
                    
                    if cursor['state'] == 'BOARD' and cursor['x'] == c and cursor['y'] == r:
                        pygame.draw.rect(screen, SELECT_COLOR, rect, 4)

                        # Manos centradas y textos a la izquierda
            hand_width = (3 * CELL_SIZE) + (2 * 10)
            hand_start_x = WIDTH//2 - hand_width//2 # Calculado para centrar las 3 cartas
            text_margin_x = 20 # Margen izquierdo de los textos
            text_margin_y = 15 # Margen superior/inferior de los textos
            
            for p_name, p_color, y_pos in [("Jugador 2", P2_COLOR, 20), ("Jugador 1", P1_COLOR, HEIGHT - CELL_SIZE - 30)]:
                is_active = (current_turn == p_name)
                
                label_text = f"{p_name} (TU TURNO)" if is_active and not game_over else p_name
                txt_color = p_color if is_active else (100, 100, 100)
                txt = font.render(label_text, True, txt_color)
                
                # Jugador 2: esquina superior izquierda / Jugador 1: esquina inferior izquierda
                if p_name == "Jugador 2":
                    text_y = text_margin_y
                else:
                    text_y = HEIGHT - txt.get_height() - text_margin_y
                screen.blit(txt, (text_margin_x, text_y))
                
                # Renderiza las cartas centradas en la pantalla
                for i, card in enumerate(hands[p_name]):
                    rect = pygame.Rect(hand_start_x + i * (CELL_SIZE + 10), y_pos, CELL_SIZE, CELL_SIZE)
                    
                    card_color = p_color if is_active else (p_color[0]//3, p_color[1]//3, p_color[2]//3)
                    pygame.draw.rect(screen, card_color, rect)
                    
                    draw_arrows(screen, card.directions, rect.x, rect.y, CELL_SIZE)
                    
                    if is_active and cursor['state'] == 'HAND' and cursor['x'] == i:
                        pygame.draw.rect(screen, SELECT_COLOR, rect, 4)

            if cursor['state'] == 'PUSH':
                panel_rect = pygame.Rect(WIDTH - 190, board_y, 170, 230)
                pygame.draw.rect(screen, (50, 50, 50), panel_rect)
                dir_names = {(0,1): "Der ->", (0,-1): "Izq <-", (-1,0): "Arr ^", (1,0): "Aba v", (0,0): "Sin empuje"}
                for i, opt in enumerate(push_options):
                    opt_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 10 + i*42, 150, 35)
                    pygame.draw.rect(screen, SELECT_COLOR if push_idx == i else (80,80,80), opt_rect)
                    lbl = font.render(dir_names.get(tuple(opt) if isinstance(opt, list) else opt, "Desconocido"), True, TEXT_COLOR if push_idx != i else (0,0,0))
                    screen.blit(lbl, (opt_rect.x + 5, opt_rect.y + 8))

            msg_color = P1_COLOR if current_turn == "Jugador 1" else P2_COLOR
            if game_over: 
                msg_color = GEM_COLOR
                msg_surface = big_font.render(message, True, msg_color)
                screen.blit(msg_surface, (WIDTH//2 - msg_surface.get_width()//2, HEIGHT//2 - 20))
            else:
                msg_surface = title_font.render(message, True, msg_color)
                screen.blit(msg_surface, (WIDTH//2 - msg_surface.get_width()//2, HEIGHT//2 - (CELL_SIZE*rows)//2 - 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()