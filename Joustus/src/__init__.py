"""
Joustus – Paquete src
Garantiza que el directorio /src esté en sys.path para que
game.py, server.py, client.py y classes.py puedan importarse
entre sí sin importar el directorio de trabajo.
"""
import os
import sys

_src = os.path.dirname(os.path.abspath(__file__))
if _src not in sys.path:
    sys.path.insert(0, _src)
