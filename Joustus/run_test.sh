#!/usr/bin/env bash
# run_test.sh — Levanta el servidor Joustus y dos clientes para una partida de prueba
# Uso: ./run_test.sh [host] [port]

HOST="${1:-127.0.0.1}"
PORT="${2:-8091}"
SRC="$(dirname "$(realpath "$0")")/src"
PY="/home/ernesg/venv/bin/python"

echo "================================================"
echo "  Joustus – Prueba local"
echo "  Servidor: $HOST:$PORT"
echo "  Intérprete: $PY"
echo "================================================"

# 1. Iniciar servidor en segundo plano
echo "[1/3] Iniciando servidor..."
"$PY" "$SRC/server.py" &
SERVER_PID=$!
sleep 1.2

# 2. Iniciar cliente 1 (Jugador 1)
echo "[2/3] Abriendo cliente 1 (Jugador 1)..."
"$PY" "$SRC/game.py" "$HOST" "$PORT" &
C1_PID=$!
sleep 0.6

# 3. Iniciar cliente 2 (Jugador 2)
echo "[3/3] Abriendo cliente 2 (Jugador 2)..."
"$PY" "$SRC/game.py" "$HOST" "$PORT" &
C2_PID=$!

echo ""
echo "  Servidor PID: $SERVER_PID"
echo "  Cliente 1 PID: $C1_PID"
echo "  Cliente 2 PID: $C2_PID"
echo ""
echo "  Cerrá las ventanas del juego para terminar."
echo "================================================"

# Esperar a que ambos clientes terminen
wait $C1_PID $C2_PID

# Apagar servidor
kill $SERVER_PID 2>/dev/null
echo "[✓] Partida finalizada. Servidor detenido."
