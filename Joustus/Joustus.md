# Joustus
## Integrantes
* Eduardo Vásquez
* Ernesto Gallego
* Lautaro Fortuna
* Federico Coronado

# Secuencia

## Paso 1
El jugador se conecta y espera a un rival.

## Paso 2

Una vez emparejado el jugador, se le entregan a ambos una matriz aletorio de 5x5 y una mano de 3 cartas. Ejemplo:

| X | - | - | - | X |
| :--- | :--- | :--- | :--- | :--- |
| - | O |   | O | - |
| - |   | O |   | - |
| - |   |   |   | - |
| X | - | - | - | X |

* X: Celda inhabilitada para movimientos
* -: Celda de descarte. El jugador no puede poner una carta aquí directamente, pero sí mediante __empuje__
* O: Celdas especial que suma puntos al jugador que tenga una carta puesta en ella. El jugador no puede poner una carta aquí directamente, pero sí mediante __empuje__
* Celdas vacías: El jugador puede poner cartas libremente en ellas.

Además, se entregará a cada jugador una mano de tres cartas. Cada carta puede tener una dirección (izquierda, derecha, arriba, abajo). Ejemplo:

| ↑ → | ↑ | ← ↑ → |
| :--- | :--- | :--- |

## Paso 3

En cada turno, el jugador debe poner una carta de su mano (respetando las reglas de celda anteriormente establecidas). Por ejemplo:

| X | - | - | - | X |
| :--- | :--- | :--- | :--- | :--- |
| - | O |   | O | - |
| - |   | O |   | - |
| - |   | ← ↑ → |   | - |
| X | - | - | - | X |

El jugador no solo puede poner cartas en celdas libres, sino que también puede desplazar otras cartas a las celdas condicionadas mediante empuje. El empuje precisa de las siguientes condiciones:

* Al ser colocada sobre una casilla libre, la carta se empuja a sí misma y a toda la fila de cartas en la dirección indicada. Todas las cartas involucradas en el tren de empuje saltan 1 casilla simultáneamente.
* La carta a poner debe tener entre sus direcciones la dirección a la que se pretende empujar (por ejemplo, | ← ↑ → | puede iniciar un empuje hacia la izquierda, derecha o arriba).
* Todas las cartas que se encuentren en la trayectoria del empuje **no** pueden tener la dirección opuesta al empuje (por ejemplo, si se empuja la fila hacia abajo, pero una de las cartas arrastradas tiene una flecha apuntando hacia arriba, el movimiento se considera inválido).
* La pila de la columna o fila de la trayectoria no puede estar saturada (es decir, mientras la celda final de la trayectoria no sobrepase los límites del tablero —como bordes o esquinas prohibidas—, el movimiento será válido).

Al final del movimiento, se repone una carta nueva a la mano.

## Paso 4

Luego de que se agoten los movimientos posibles, la partida termina. Se cuenta qué jugador tiene más cartas puestas en las celdas especiales y el que tenga más, gana. 
