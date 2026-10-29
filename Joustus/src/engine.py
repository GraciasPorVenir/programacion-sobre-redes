import random
from models import Slot, SlotType, TurnReq, Matrix

class GameEngine:
    @staticmethod
    # Added extended mode parameters
    def create_matrix(extra_row: int = 0, extra_col: int = 0, extra_gem: int = 0) -> Matrix:
        rows = 5 + extra_row
        cols = 5 + extra_col
        gems = 3 + extra_gem
        
        # Dynamic matrix generation based on rows and cols
        matrix = [[Slot(SlotType.BORDER) for _ in range(cols)] for _ in range(rows)]
        for row, col in ((0, 0), (0, cols - 1), (rows - 1, cols - 1), (rows - 1, 0)):
            matrix[row][col].type = SlotType.NO_SLOT
            
        normal_coords = []
        for row in range(1, rows - 1):
            for col in range(1, cols - 1):
                matrix[row][col].type = SlotType.NORMAL
                normal_coords.append((row, col))
                
        for row, col in random.sample(normal_coords, k=gems):
            matrix[row][col].type = SlotType.GEM
            
        return matrix

    @staticmethod
    def check_movement(mv: TurnReq) -> bool:
        def _check_pos(x: int, y: int) -> bool:
            return 0 <= x < len(mv.matrix) and 0 <= y < len(mv.matrix[0])

        if not _check_pos(mv.x, mv.y):
            return False
            
        slot: Slot = mv.matrix[mv.x][mv.y]
        
        if slot.card is not None or slot.type != SlotType.NORMAL:
            return False
            
        if mv.vx == 0 and mv.vy == 0:
            return True
            
        cx, cy = mv.x + mv.vx, mv.y + mv.vy
        while _check_pos(cx, cy):
            n_slot = mv.matrix[cx][cy]
            
            if n_slot.card is None:
                if n_slot.type == SlotType.NO_SLOT:
                    return False
                return True
                
            opp_list = [-mv.vx, -mv.vy]
            opp_tuple = (-mv.vx, -mv.vy)
            if opp_list in n_slot.card.directions or opp_tuple in n_slot.card.directions:
                return False
                
            cx += mv.vx
            cy += mv.vy
            
        return False

    @staticmethod
    def valid_movements(matrix: Matrix) -> bool:
        # Dynamic boundaries check
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        
        for x in range(1, rows - 1):
            for y in range(1, cols - 1):
                slot: Slot = matrix[x][y]
                if slot.card is None and slot.type == SlotType.NORMAL:
                    return True
                if slot.card is not None:
                    for d in slot.card.directions:
                        if d != None:
                            nx, ny = (x + d[0], y + d[1])
                            mv = TurnReq(card=slot.card, matrix=matrix, x=nx, y=ny, vx=d[0], vy=d[1])
                            if GameEngine.check_movement(mv):
                                return True
        return False

    @staticmethod
    def execute_movement(mv: TurnReq, history: list[Matrix] | None = None) -> tuple[Matrix, list[Matrix]]:
        if history is None:
            history = []
            
        import copy
        history.append(copy.deepcopy(mv.matrix))
        
        mv.card.directions.clear()
        if mv.vx != 0 or mv.vy != 0:
            mv.card.directions.append((mv.vx, mv.vy))
        mv.matrix[mv.x][mv.y].card = mv.card
        history.append(copy.deepcopy(mv.matrix))
        
        if mv.vx != 0 or mv.vy != 0:
            train = []
            cx, cy = mv.x, mv.y
            while 0 <= cx < len(mv.matrix) and 0 <= cy < len(mv.matrix[0]):
                card = mv.matrix[cx][cy].card
                if not card:
                    break
                train.append(card)
                cx += mv.vx
                cy += mv.vy
            
            cx, cy = mv.x, mv.y
            mv.matrix[cx][cy].card = None
            
            for card in train:
                cx += mv.vx
                cy += mv.vy
                if 0 <= cx < len(mv.matrix) and 0 <= cy < len(mv.matrix[0]):
                    mv.matrix[cx][cy].card = card
                    
            history.append(copy.deepcopy(mv.matrix))
            
        return mv.matrix, history

    @staticmethod
    def handle_endgame(matrix: Matrix) -> tuple[str, dict]:
        p = {}
        # Dynamic boundaries check
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        
        for row in range(rows):
            for col in range(cols):
                slot: Slot = matrix[row][col]
                if slot.type == SlotType.GEM and slot.card:
                    idx = slot.card.player
                    if idx not in p:
                        p[idx] = 0
                    p[idx] += 1
                elif slot.card:
                    idx = slot.card.player
                    if idx not in p:
                        p[idx] = 0

        if "Jugador 1" not in p: p["Jugador 1"] = 0
        if "Jugador 2" not in p: p["Jugador 2"] = 0

        if p["Jugador 1"] == p["Jugador 2"]:
            return "EMP", p
        return max(p, key=lambda k: p.get(k, 0)), p