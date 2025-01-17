# Poker 1vs1 Bot
El repositorio de GitHub [poker-engine-py](https://github.com/Hakai69/poker-engine-py) 
contiene la versión inicial de una librería diseñada para jugar al Texas Hold'em Poker 
en un formato 1 vs 1 contra un bot.

## Funcionalidad Actual
En esta primera versión, el bot juega basándose en reglas que consideran la equity de su mano, 
es decir, la probabilidad de ganar según las cartas visibles. Aunque funcional, esta lógica 
básica será significativamente mejorada en la versión final, donde se integrarán redes neuronales 
y modelos probabilísticos para abordar cada etapa del juego (pre-flop, flop, turn y river), 
permitiendo al bot tomar decisiones más sofisticadas sobre las acciones y las apuestas.

## Módulos Implementados
El repositorio incluye los siguientes componentes totalmente funcionales:
- Carpeta `game_objects`: Define el entorno necesario para las implementaciones del juego.
- Archivos `player.py` y `game.py`: Proveen las clases y funciones para crear partidas y gestionar jugadores.
- Archivo `equity.py` (ubicado en la carpeta `stats`): Sirve como base para calcular la probabilidad 
    de ganar, que sustenta las decisiones del bot.
- Archivo `basic_decider.py`: Implementa una lógica básica que controla el comportamiento del bot durante el juego.

Además, el archivo `demo.ipynb` incluye un test interactivo que permite probar el rendimiento del bot jugando directamente contra él.

## Consideraciones
Aunque el bot actual toma decisiones razonables, su comportamiento es predecible para quienes conocen su lógica. 
En la versión final, este aspecto se transformará con una implementación más profunda que combinará algoritmos 
avanzados de aprendizaje automático y teoría de juegos para optimizar su desempeño.

## Autores
- Daniel Moraleda Sánchez  
- Daniel Navarro Puche

