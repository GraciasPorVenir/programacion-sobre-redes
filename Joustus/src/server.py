from __future__ import annotations
import socket
import threading
from client import Client
from models import Card, TurnRes, TurnReq, Matrix, Hand
from engine import GameEngine


class Server:
    def __init__(self):
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.wp: Client | None = None
        self.lock: threading.Lock = threading.Lock()

    def start(self, host: str, port: int):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen()
        print(f"[+] Servidor listo en {host}:{port}")
        while True:
            try:
                client_socket, address = self.socket.accept()
                p = Client(client_socket, address)
                print(f"[+] Nueva conexión física desde {address}")
                threading.Thread(target=self.matchmake, args=(p,), daemon=True).start()
            except Exception as e:
                print(f"[-] Error en el bucle principal: {e}")

    def matchmake(self, p: Client):
        try:
            init_msg = p.receive()
            if init_msg and init_msg.get("type") == "INIT_MODE":
                p.mode_config = init_msg
            else:
                p.mode_config = {"extra_row": 0, "extra_col": 0, "extra_gem": 0}

            with self.lock:
                if self.wp:
                    p.name = "Jugador 2"
                    threading.Thread(
                        target=self._handle_game, args=(self.wp, p)
                    ).start()
                    self.wp = None
                else:
                    p.name = "Jugador 1"
                    self.wp = p
        except Exception as e:
            print(e)

    def _toggle_turns(
        self,
        ap: Client,
        wp: Client,
        matrix: Matrix,
        turn_hand: tuple[list[Card], list[Card]] | tuple[Card, Card],
        winner: str = "",
        scores: dict | None = None,
        last_move: TurnReq | None = None,
        history: list[Matrix] | None = None,
    ):
        for p in (ap, wp):
            if winner == "":
                msg = "Tu turno" if p == ap else "Turno del rival"
                if last_move and p == ap:
                    dirs = {(0, 1): "→", (0, -1): "←", (-1, 0): "↑", (1, 0): "↓"}
                    if last_move.vx == 0 and last_move.vy == 0:
                        move_str = f"El rival colocó su carta en la fila {last_move.x}, columna {last_move.y} sin empujar."
                    else:
                        d_str = dirs.get((last_move.vx, last_move.vy), "?")
                        move_str = f"El rival colocó su carta en la fila {last_move.x}, columna {last_move.y} empujando hacia {d_str}."
                    msg = f"{move_str}\n  {msg}"
                turn = p == ap
            else:
                if winner == "EMP":
                    msg = "Empate"
                else:
                    msg = "¡Ganaste!" if p.name == winner else "El rival ganó"
                if scores:
                    msg += f"\nJugador 1: {scores['Jugador 1']} gemas\nJugador 2: {scores['Jugador 2']} gemas"
                turn = False
            data = {"matrix": matrix, "turn": turn, "message": msg, "history": history}
            pos1, pos2 = turn_hand
            if isinstance(pos1, Card) and isinstance(pos2, Card):
                res = TurnRes(newcard=pos1, precard=pos2, **data)
            elif isinstance(pos1, list) and isinstance(pos2, list):
                # p != ap: el jugador en espera recibe sus cartas en orden inverso
                if p != ap:
                    pos1, pos2 = pos2, pos1
                res = Hand(hand=pos1, rhand=pos2, **data)
            else:
                return
            p.send(res.to_dict())

    def _handle_game(self, p1: Client, p2: Client):
        try:
            hands = ([Card.create(p1.name) for _ in range(3)], [Card.create(p2.name) for _ in range(3)])
            is_playing: bool = True
            
            e_row = max(p1.mode_config.get("extra_row", 0), p2.mode_config.get("extra_row", 0))
            e_col = max(p1.mode_config.get("extra_col", 0), p2.mode_config.get("extra_col", 0))
            e_gem = max(p1.mode_config.get("extra_gem", 0), p2.mode_config.get("extra_gem", 0))

            matrix: Matrix = GameEngine.create_matrix(extra_row=e_row, extra_col=e_col, extra_gem=e_gem)

            ap, wp = p1, p2
            self._toggle_turns(ap, wp, matrix, hands)
            while is_playing:
                data = ap.receive()
                if not data:
                    c = Card.create("[SYSTEM]")
                    data = {
                        "message": "Partida interrumpida",
                        "turn": False,
                        "newcard": c,
                        "precard": c,
                    }
                    wp.send(TurnRes(matrix=matrix, **data).to_dict())
                    break
                req: TurnReq = TurnReq.create(**data)
                req.matrix = matrix
                if not GameEngine.check_movement(req):
                    data = {
                        "message": "Movimiento inválido",
                        "turn": True,
                        "newcard": req.card,
                        "precard": req.card,
                    }
                    res = TurnRes(matrix=matrix, **data)
                    ap.send(res.to_dict())
                    continue
                matrix, history = GameEngine.execute_movement(req)
                winner = ""
                scores = None
                if not GameEngine.valid_movements(matrix):
                    winner, scores = GameEngine.handle_endgame(matrix)
                    is_playing = False
                new_card = Card.create(ap.name)
                ap, wp = wp, ap
                self._toggle_turns(ap, wp, matrix, (new_card, req.card), winner, scores, last_move=req, history=history)
        except Exception as e:
            import traceback
            traceback.print_exc()
        finally:
            import time
            time.sleep(1)
            p1.disconnect()
            p2.disconnect()

if __name__ == "__main__":
    Server().start("0.0.0.0", 8091)