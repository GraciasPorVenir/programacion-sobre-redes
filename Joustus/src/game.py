"""
Joustus – Cliente Pygame
Ejecutar: python3 game.py [host] [port]
Ejemplo:  python3 game.py 127.0.0.1 8091
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import threading
import pygame
from client import Client
from classes import Card, Slot, SlotType, TurnReq, Hand, TurnRes

# ── Ventana ─────────────────────────────────────────────────────────────────
W, H  = 960, 700
FPS   = 60

# ── Tablero ──────────────────────────────────────────────────────────────────
CELL      = 78
BOARD_X   = 50
BOARD_Y   = 105

# ── Carta en mano ────────────────────────────────────────────────────────────
CW, CH = 130, 90

# ── Paleta ──────────────────────────────────────────────────────────────────
BG       = (13,  11,  30)
C_NOSLOT = ( 8,   8,  18)
C_BORDER = (50,  50,  80)
C_NORMAL = (35,  35,  60)
C_GEM    = (70,  55,  15)
C_VALID  = (25,  80,  45)
C_SEL    = (30,  60, 110)
C_P1     = (60, 120, 220)
C_P2     = (210,  60,  60)
C_TEXT   = (210, 210, 230)
C_DIM    = (110, 110, 140)
C_GOLD   = (255, 200,  50)
C_CYAN   = ( 80, 210, 255)

DIR_SYM  = {(0,1):'→', (1,0):'↓', (0,-1):'←', (-1,0):'↑'}


# ── Estado de pantalla ───────────────────────────────────────────────────────
class St:
    CONNECTING   = 0
    WAITING      = 1
    MY_TURN      = 2
    OPP_TURN     = 3
    GAME_OVER    = 4
    RECONNECTING = 5


# ── Juego principal ──────────────────────────────────────────────────────────
class JoustusGUI:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Joustus — Programación sobre Redes")
        self.clock  = pygame.time.Clock()

        # Fuentes
        self.f_xl = pygame.font.SysFont("segoeui", 30, bold=True)
        self.f_lg = pygame.font.SysFont("segoeui", 22, bold=True)
        self.f_md = pygame.font.SysFont("segoeui", 18)
        self.f_sm = pygame.font.SysFont("segoeui", 14)

        # Red
        self.client    = Client()
        self._incoming = None
        self._lock     = threading.Lock()

        # Estado del juego
        self.state   = St.CONNECTING
        self.message = "Conectando al servidor…"
        self.matrix  = None
        self.hand  : list[Card] = []
        self.rhand : list[Card] = []
        self.my_name = ""

        # Interacción
        self.sel         = None   # índice en self.hand
        self.valid_moves : list[tuple] = []  # (r, c, vx, vy)
        self.anim_tick   = 0

        # Botón volver a jugar
        self.btn_replay_rect = pygame.Rect(W // 2 - 110, H // 2 + 40, 220, 50)

        # Reconexión
        self._host       = "127.0.0.1"
        self._port       = 8091
        self._recon_at   = 0.0

    # ── Red ──────────────────────────────────────────────────────────────────

    def connect(self, host: str, port: int):
        self._host = host
        self._port = port
        self.client = Client()
        if self.client.connect(host, port):
            self.state   = St.WAITING
            self.message = "Esperando un rival…"
            threading.Thread(target=self._listen, daemon=True).start()
        else:
            self.message = "No se pudo conectar. ¿Está corriendo el servidor?"

    def _reset_game(self):
        """Resetea el estado de partida sin cerrar la ventana."""
        self.matrix  = None
        self.hand    = []
        self.rhand   = []
        self.my_name = ""
        self.sel         = None
        self.valid_moves = []

    def _schedule_reconnect(self, seconds: int = 5):
        import time
        self.state      = St.RECONNECTING
        self._recon_at  = time.monotonic() + seconds

    def _listen(self):
        while True:
            data = self.client.receive()
            if data is None:
                with self._lock:
                    self._incoming = {"_lost": True}
                break
            with self._lock:
                self._incoming = data

    def _flush(self):
        with self._lock:
            data = self._incoming
            self._incoming = None
        if not data:
            return

        if data.get("_lost"):
            if self.state != St.GAME_OVER:
                self.message = "Conexión perdida. Reconectando…"
                self._reset_game()
                self._schedule_reconnect(5)
            return

        if "hand" in data:
            self._on_hand(data)
        elif "newcard" in data:
            self._on_turn_res(data)

    def _on_hand(self, data: dict):
        h = Hand.create(**data)
        self.matrix  = h.matrix
        self.hand    = list(h.hand)
        self.rhand   = list(h.rhand)
        self.message = h.message
        if h.turn:
            self.state   = St.MY_TURN
            self.my_name = "Jugador 1"
        else:
            self.state   = St.OPP_TURN
            self.my_name = "Jugador 2"

    def _on_turn_res(self, data: dict):
        tr = TurnRes.create(**data)
        self.matrix  = tr.matrix
        self.message = tr.message

        if tr.precard.player == self.my_name:
            for i, c in enumerate(self.hand):
                if c.directions == tr.precard.directions:
                    self.hand[i] = tr.newcard
                    break
        else:
            for i, c in enumerate(self.rhand):
                if c.directions == tr.precard.directions:
                    self.rhand[i] = tr.newcard
                    break

        end_msgs = ("Ganaste", "Rival ganó", "Empate")
        interrupt_msgs = ("Partida interrumpida",)
        if tr.message in end_msgs:
            self.state = St.GAME_OVER
        elif tr.message in interrupt_msgs:
            self._schedule_reconnect(5)
        elif tr.turn:
            self.state = St.MY_TURN
        else:
            self.state = St.OPP_TURN

        self.sel         = None
        self.valid_moves = []

    # ── Lógica de movimientos ────────────────────────────────────────────────

    def _compute_valid(self, card: Card) -> list[tuple]:
        if not self.matrix:
            return []
        moves = []
        for r in range(5):
            for c in range(5):
                slot = self.matrix[r][c]
                if slot.card is None and slot.type == SlotType.NORMAL:
                    vx, vy = self._safe_dir(r, c)
                    moves.append((r, c, vx, vy))
                    continue
                if slot.card is not None:
                    for d in card.directions:
                        if d is None:
                            continue
                        vx, vy = d
                        nx, ny = r + vx, c + vy
                        if not (0 <= nx < 5 and 0 <= ny < 5):
                            continue
                        tslot = self.matrix[nx][ny]
                        if tslot.type == SlotType.NO_SLOT:
                            continue
                        if tslot.card and (-vx, -vy) in [tuple(x) for x in tslot.card.directions if x]:
                            continue
                        moves.append((nx, ny, vx, vy))
        return moves

    def _safe_dir(self, r: int, c: int) -> tuple:
        for vx, vy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            pr, pc = r - vx, c - vy
            if pr < 0 or pr >= 5 or pc < 0 or pc >= 5:
                return vx, vy
            if self.matrix[pr][pc].type in (SlotType.BORDER, SlotType.NO_SLOT):
                return vx, vy
        return 1, 0

    def _send_move(self, card: Card, r: int, c: int, vx: int, vy: int):
        req = TurnReq(card=card, matrix=self.matrix, x=r, y=c, vx=vx, vy=vy)
        self.client.send(req.to_dict())
        self.state   = St.OPP_TURN
        self.message = "Movimiento enviado. Turno del rival…"
        self.sel         = None
        self.valid_moves = []

    # ── Manejo de eventos ────────────────────────────────────────────────────

    def _on_click(self, pos):
        if self.state == St.GAME_OVER:
            if self.btn_replay_rect.collidepoint(pos):
                self.client.disconnect()
                self._reset_game()
                self.connect(self._host, self._port)
            return

        if self.state != St.MY_TURN:
            return
        mx, my = pos

        hand_y = H - 110
        for i, card in enumerate(self.hand):
            cx = 30 + i * (CW + 18)
            if cx <= mx <= cx + CW and hand_y <= my <= hand_y + CH:
                if self.sel == i:
                    self.sel, self.valid_moves = None, []
                else:
                    self.sel         = i
                    self.valid_moves = self._compute_valid(card)
                return

        if self.sel is not None:
            bc = (mx - BOARD_X) // CELL
            br = (my - BOARD_Y) // CELL
            if 0 <= br < 5 and 0 <= bc < 5:
                matched = [(vx, vy) for vr, vc, vx, vy in self.valid_moves
                           if vr == br and vc == bc]
                if matched:
                    vx, vy = matched[0]
                    self._send_move(self.hand[self.sel], br, bc, vx, vy)

    # ── Dibujo ───────────────────────────────────────────────────────────────

    def _draw_hud(self):
        pygame.draw.rect(self.screen, (22, 18, 50), (0, 0, W, 90))
        pygame.draw.line(self.screen, (60, 60, 120), (0, 90), (W, 90), 1)

        if self.state == St.MY_TURN:
            label, col = "● TU TURNO", (100, 230, 100)
        elif self.state == St.OPP_TURN:
            label, col = "● TURNO DEL RIVAL", (230, 100, 100)
        elif self.state == St.WAITING:
            label, col = "⏳  ESPERANDO RIVAL…", C_GOLD
        elif self.state == St.GAME_OVER:
            label, col = "■  FIN DE PARTIDA", C_GOLD
        else:
            label, col = "CONECTANDO…", C_DIM

        self.screen.blit(self.f_xl.render(label, True, col), (20, 14))
        self.screen.blit(self.f_md.render(self.message, True, C_TEXT), (20, 58))

        if self.my_name:
            t = self.f_sm.render(f"Jugás como: {self.my_name}", True, C_DIM)
            self.screen.blit(t, (W - t.get_width() - 20, 20))

    def _draw_cell(self, r, c, slot):
        x = BOARD_X + c * CELL
        y = BOARD_Y + r * CELL
        rect = pygame.Rect(x + 1, y + 1, CELL - 2, CELL - 2)

        if slot.type == SlotType.NO_SLOT:
            col = C_NOSLOT
        elif slot.type == SlotType.BORDER:
            col = C_BORDER
        elif slot.type == SlotType.GEM:
            col = C_GEM
        else:
            col = C_NORMAL

        in_valid = any(vr == r and vc == c for vr, vc, _, _ in self.valid_moves)
        if in_valid:
            pulse = abs((self.anim_tick % 60) - 30) / 30
            col = tuple(int(a + (b - a) * pulse) for a, b in zip(col, C_VALID))

        pygame.draw.rect(self.screen, col, rect, border_radius=7)
        pygame.draw.rect(self.screen, (70, 70, 110), rect, 1, border_radius=7)

        if slot.type == SlotType.GEM:
            cx, cy = x + CELL // 2, y + CELL // 2
            pts = [(cx, cy - 14), (cx + 12, cy), (cx, cy + 14), (cx - 12, cy)]
            pygame.draw.polygon(self.screen, C_GOLD, pts)
            pygame.draw.polygon(self.screen, (255, 240, 100), pts, 1)

        if slot.card:
            self._draw_board_card(slot.card, x, y)

    def _draw_board_card(self, card: Card, x, y):
        p_col = C_P1 if card.player == "Jugador 1" else C_P2
        inner = pygame.Rect(x + 5, y + 5, CELL - 10, CELL - 10)
        pygame.draw.rect(self.screen, p_col, inner, border_radius=5)
        arrows = "".join(DIR_SYM[tuple(d)] for d in card.directions if d is not None)
        surf = self.f_sm.render(arrows or "·", True, (240, 240, 240))
        self.screen.blit(surf, (x + (CELL - surf.get_width()) // 2,
                                y + (CELL - surf.get_height()) // 2))

    def _draw_board(self):
        if not self.matrix:
            return
        for r in range(5):
            for c in range(5):
                self._draw_cell(r, c, self.matrix[r][c])

    def _draw_hand_card(self, i: int, card: Card, y: int):
        x = 30 + i * (CW + 18)
        rect = pygame.Rect(x, y, CW, CH)
        selected = (self.sel == i and self.state == St.MY_TURN)

        bg  = C_SEL if selected else (20, 20, 45)
        bdr = C_CYAN if selected else C_P1
        pygame.draw.rect(self.screen, bg, rect, border_radius=10)
        pygame.draw.rect(self.screen, bdr, rect, 3 if selected else 1, border_radius=10)

        tag = self.f_sm.render("Tu carta", True, C_DIM)
        self.screen.blit(tag, (x + (CW - tag.get_width()) // 2, y + 8))

        arrows = " ".join(DIR_SYM[tuple(d)] for d in card.directions if d is not None) or "·"
        surf = self.f_lg.render(arrows, True, C_TEXT)
        self.screen.blit(surf, (x + (CW - surf.get_width()) // 2, y + 35))

    def _draw_player_hand(self):
        hand_y = H - 110
        pygame.draw.line(self.screen, (50, 50, 90), (0, hand_y - 14), (W, hand_y - 14), 1)
        lbl = self.f_sm.render("TU MANO  (clic para seleccionar)", True, C_DIM)
        self.screen.blit(lbl, (30, hand_y - 12))
        for i, card in enumerate(self.hand):
            self._draw_hand_card(i, card, hand_y + 2)

    def _draw_rhand(self):
        rx = BOARD_X + 5 * CELL + 28
        lbl = self.f_sm.render("MANO RIVAL", True, C_DIM)
        self.screen.blit(lbl, (rx, BOARD_Y - 20))
        for i, card in enumerate(self.rhand):
            ry = BOARD_Y + i * (80 + 10)
            rect = pygame.Rect(rx, ry, 160, 74)
            pygame.draw.rect(self.screen, (40, 18, 18), rect, border_radius=8)
            pygame.draw.rect(self.screen, C_P2, rect, 1, border_radius=8)
            arrows = " ".join(DIR_SYM[tuple(d)] for d in card.directions if d is not None) or "·"
            surf = self.f_md.render(arrows, True, (240, 170, 170))
            self.screen.blit(surf, (rx + (160 - surf.get_width()) // 2, ry + 26))

    def _draw_legend(self):
        lx = BOARD_X + 5 * CELL + 28
        ly = BOARD_Y + 290
        items = [
            (C_NORMAL, "Celda libre"),
            (C_GEM,    "Gema (+1 pt)"),
            (C_BORDER, "Descarte"),
            (C_VALID,  "Mov. válido"),
            (C_P1,     "Jugador 1"),
            (C_P2,     "Jugador 2"),
        ]
        self.screen.blit(self.f_sm.render("LEYENDA", True, C_DIM), (lx, ly - 18))
        for k, (col, label) in enumerate(items):
            ry = ly + k * 24
            pygame.draw.rect(self.screen, col, (lx, ry + 2, 14, 14), border_radius=3)
            self.screen.blit(self.f_sm.render(label, True, C_TEXT), (lx + 20, ry))

    def _draw_instructions(self):
        lines = ["ESC → deseleccionar", "① clic carta  ② clic celda verde"]
        iy = H - 38
        for line in lines:
            t = self.f_sm.render(line, True, C_DIM)
            self.screen.blit(t, (W - t.get_width() - 16, iy))
            iy += 17

    def _draw_overlay(self):
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 180))
        self.screen.blit(surf, (0, 0))
        
        msg = self.f_xl.render(self.message, True, C_GOLD)
        self.screen.blit(msg, (W // 2 - msg.get_width() // 2, H // 2 - 50))

        # Dibujo del botón "Volver a jugar"
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.btn_replay_rect.collidepoint(mouse_pos)
        btn_col = (40, 160, 90) if is_hover else (30, 120, 70)
        
        pygame.draw.rect(self.screen, btn_col, self.btn_replay_rect, border_radius=8)
        pygame.draw.rect(self.screen, C_CYAN if is_hover else C_TEXT, self.btn_replay_rect, 2, border_radius=8)
        
        btn_txt = self.f_lg.render("Volver a jugar", True, (255, 255, 255))
        self.screen.blit(btn_txt, (self.btn_replay_rect.x + (self.btn_replay_rect.width - btn_txt.get_width()) // 2,
                                   self.btn_replay_rect.y + (self.btn_replay_rect.height - btn_txt.get_height()) // 2))

    def _draw_waiting(self):
        t1 = self.f_xl.render(self.message, True, C_GOLD)
        t2 = self.f_md.render("Esperá que un segundo jugador se conecte al servidor.", True, C_DIM)
        self.screen.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 30))
        self.screen.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 20))

    def _draw_reconnecting(self):
        import time
        remaining = max(0.0, self._recon_at - time.monotonic())
        t1 = self.f_xl.render(self.message, True, (230, 120, 60))
        t2 = self.f_md.render(f"Buscando nueva partida en {int(remaining) + 1}s…", True, C_DIM)
        self.screen.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 30))
        self.screen.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 20))

    # ── Loop principal ───────────────────────────────────────────────────────

    def run(self, host="127.0.0.1", port=8091):
        self.connect(host, port)

        running = True
        while running:
            self.screen.fill(BG)
            self.anim_tick += 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._on_click(event.pos)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.sel, self.valid_moves = None, []

            if not running:
                break

            self._flush()

            import time
            if self.state == St.RECONNECTING and time.monotonic() >= self._recon_at:
                self.connect(self._host, self._port)

            self._draw_hud()

            if self.state in (St.CONNECTING, St.WAITING):
                self._draw_waiting()
            elif self.state == St.RECONNECTING:
                self._draw_reconnecting()
            else:
                self._draw_board()
                self._draw_player_hand()
                self._draw_rhand()
                self._draw_legend()
                self._draw_instructions()

            if self.state == St.GAME_OVER:
                self._draw_overlay()

            pygame.display.flip()
            self.clock.tick(FPS)

        self.client.disconnect()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8091
    JoustusGUI().run(host, port)