# Joustus - Informe Técnico de Arquitectura

Este documento describe la arquitectura técnica del proyecto Joustus tras su refactorización para mejorar la segmentación y separación de responsabilidades.

## Estructura del Proyecto

```text
Joustus/
├── Joustus.md          # Documentación de reglas del juego
├── README.md           # Informe técnico y arquitectura (este archivo)
├── pyproject.toml      # Configuración del entorno (Poetry)
└── src/
    ├── client.py       # Capa de red del lado del cliente
    ├── engine.py       # Lógica central del juego (Game Engine)
    ├── gui.py          # Interfaz gráfica y bucle principal (Frontend)
    ├── models.py       # Modelos de datos y DTOs (Data Transfer Objects)
    └── server.py       # Servidor TCP y coordinador de red
```

## Módulos y Responsabilidades

### 1. `src/models.py` (Módulo de Datos)
Contiene las estructuras de datos fundamentales (`Card`, `Slot`, `Matrix`) y las clases de transferencia de red (`TurnReq`, `TurnRes`, `Hand`).
- **Objetivo**: Estandarizar la forma en que los datos se guardan en memoria y cómo se serializan/deserializan (a formato JSON) para viajar por sockets TCP.
- **Cambios**: Anteriormente se llamaba `classes.py`. Fue renombrado a `models.py` para seguir los estándares de la industria (Modelo-Vista-Controlador).

### 2. `src/engine.py` (Motor del Juego)
Contiene la clase `GameEngine` que expone métodos estáticos puros para manipular el estado del tablero.
- **Objetivo**: Aislar la lógica dura del juego de la capa de red.
- **Funcionalidades**:
  - `create_matrix()`: Inicializa el tablero 5x5 con sus bordes, casillas normales y gemas.
  - `check_movement()`: Valida si un empuje en cascada respeta la regla de no-oposición.
  - `execute_movement()`: Desplaza toda la fila de cartas en la dirección indicada y genera el "history" (los cuadros de animación).
  - `handle_endgame()`: Cuenta las gemas y determina el ganador al agotar movimientos.

### 3. `src/server.py` (Servidor de Red)
Actúa como la autoridad de la red y el coordinador central.
- **Objetivo**: Recibir conexiones TCP, emparejar a los jugadores (`Jugador 1` y `Jugador 2`) y reenviar el estado del juego.
- **Flujo**: Extrae la petición JSON enviada por el cliente (`client.py`), delega la validación de la jugada al `GameEngine` (`engine.py`), y si es válida, actualiza el estado y transmite el nuevo `TurnRes` a ambos clientes.

### 4. `src/client.py` (Cliente TCP)
- **Objetivo**: Proveer una interfaz asíncrona entre el servidor y la interfaz gráfica.
- **Flujo**: Levanta un hilo (`network_thread`) que bloquea en `receive()`. Cuando llega un paquete del servidor, lo parsea y lo inserta en una cola de eventos (`queue.Queue()`) de modo que la GUI no se congele esperando a la red.

### 5. `src/gui.py` (Frontend)
- **Objetivo**: Dibujar el menú, gestionar las opciones de configuración, dibujar el tablero usando Pygame y reproducir las animaciones dictadas por el historial del `GameEngine`.
- **Diseño**: Es un bucle "while loop" clásico de videojuegos que consume la cola de red asíncrona de `client.py` y repinta la pantalla a 30 FPS.

## Regla de la Cascada (Implementación)
El motor (`engine.py`) fue diseñado para cumplir estrictamente con la dinámica de empuje en bloque. Al colocar una carta:
1. La carta se apoya en una celda vacía.
2. Si el jugador eligió empujar, toda la línea en esa dirección salta una casilla de forma simultánea.
3. Esto permite que una carta cambie de posición desde donde fue inicialmente soltada, abriendo ventanas de oportunidad (o exponiendo cartas rivales a nuevos ángulos) de manera dinámica.

## Video tutorial
<video src=""C:programacion-sobre-redes\Joustus\src\1030.mp4"" controls width="100%"></video>
