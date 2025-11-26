"""Plantilla del juego Arkanoid para el hito M2.

Completa los métodos marcados con TODO respetando las anotaciones de tipo y la
estructura de la clase. El objetivo es construir un prototipo jugable usando
pygame que cargue bloques desde un fichero de nivel basado en caracteres.
"""
from arkanoid_core import *
import os
import math


# --------------------------------------------------------------------- #
# MÉTODOS DEL ALUMNADO
# --------------------------------------------------------------------- #


@arkanoid_method
def cargar_nivel(self) -> list[str]:
    """
    Lee el archivo de nivel y devuelve la lista de filas.
    También verifica que todas las líneas tengan la misma longitud.
    """
    ruta = self.level_path

    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de nivel: {ruta}")

    contenido = ruta.read_text().splitlines()

    # Filtramos líneas vacías
    filas = [linea for linea in contenido if linea.strip()]

    # Validación del ancho
    ancho = len(filas[0])
    for fila in filas:
        if len(fila) != ancho:
            raise ValueError("Todas las filas del nivel deben tener el mismo ancho.")

    self.layout = filas
    return filas


@arkanoid_method
def preparar_entidades(self) -> None:
    """
    Coloca paleta y bola en posición inicial.
    Reinicia puntuación, vidas y mensaje final.
    """

    # Paleta centrada en la parte inferior
    paddle_x = (self.SCREEN_WIDTH - self.PADDLE_SIZE[0]) // 2
    paddle_y = self.SCREEN_HEIGHT - self.PADDLE_OFFSET
    self.paddle = self.crear_rect(paddle_x, paddle_y, *self.PADDLE_SIZE)

    # Estado del juego
    self.score = 0
    self.lives = 3
    self.end_message = ""

    # La bola se coloca justo sobre la paleta
    self.reiniciar_bola()


@arkanoid_method
def crear_bloques(self) -> None:
    """
    Genera los rectángulos de los bloques a partir de la cuadrícula del nivel.
    """
    self.blocks.clear()
    self.block_colors.clear()
    self.block_symbols.clear()

    for fila, linea in enumerate(self.layout):
        for col, simbolo in enumerate(linea):

            if simbolo in self.BLOCK_COLORS:
                rect = self.calcular_posicion_bloque(fila, col)
                self.blocks.append(rect)
                self.block_colors.append(self.BLOCK_COLORS[simbolo])
                self.block_symbols.append(simbolo)


@arkanoid_method
def procesar_input(self) -> None:
    """
    Mover la paleta usando teclas:
    ← →  o  A D
    """
    keys = self.obtener_estado_teclas()

    if keys[self.KEY_LEFT] or keys[self.KEY_A]:
        self.paddle.x -= self.PADDLE_SPEED

    if keys[self.KEY_RIGHT] or keys[self.KEY_D]:
        self.paddle.x += self.PADDLE_SPEED

    # Limitar paleta a pantalla
    if self.paddle.left < 0:
        self.paddle.left = 0
    if self.paddle.right > self.SCREEN_WIDTH:
        self.paddle.right = self.SCREEN_WIDTH


@arkanoid_method
def actualizar_bola(self) -> None:
    """
    Movimiento de la bola y gestión de colisiones.
    """
    self.ball_pos += self.ball_velocity
    ball_rect = self.obtener_rect_bola()

    # Rebote laterales
    if ball_rect.left <= 0 or ball_rect.right >= self.SCREEN_WIDTH:
        self.ball_velocity.x *= -1

    # Rebote techo
    if ball_rect.top <= 0:
        self.ball_velocity.y *= -1

    # La bola cae = pérdida de vida
    if ball_rect.top > self.SCREEN_HEIGHT:
        self.lives -= 1
        self.reiniciar_bola()
        return

    # Colisión con paleta
    if ball_rect.colliderect(self.paddle):
        offset = (ball_rect.centerx - self.paddle.centerx) / (self.PADDLE_SIZE[0] / 2)
        angle = offset * (math.pi / 3)  # Máximo 60 grados
        speed = self.ball_velocity.length()
        self.ball_velocity.x = speed * math.sin(angle)
        self.ball_velocity.y = -abs(speed * math.cos(angle))

    # Colisión con bloques
    for i, rect in enumerate(self.blocks):
        if ball_rect.colliderect(rect):

            simbolo = self.block_symbols[i]
            puntos = self.BLOCK_POINTS[simbolo]
            self.score += puntos

            # Eliminar bloque y sus datos paralelos
            del self.blocks[i]
            del self.block_colors[i]
            del self.block_symbols[i]

            # Rebote simple: invertir eje Y
            self.ball_velocity.y *= -1
            break  # Salimos para evitar dobles colisiones

    # Fin de nivel
    if not self.blocks:
        self.end_message = "¡Nivel completado!"


@arkanoid_method
def dibujar_escena(self) -> None:
    """
    Dibuja fondo, bloques, paleta, bola, HUD.
    """
    self.screen.fill(self.BACKGROUND_COLOR)

    # Bloques
    for rect, color in zip(self.blocks, self.block_colors):
        self.dibujar_rectangulo(rect, color)

    # Paleta
    self.dibujar_rectangulo(self.paddle, self.PADDLE_COLOR)

    # Bola (como círculo)
    self.dibujar_circulo(
        (int(self.ball_pos.x), int(self.ball_pos.y)),
        self.BALL_RADIUS,
        self.BALL_COLOR,
    )

    # HUD: puntuación y vidas
    self.dibujar_texto(f"Puntuación: {self.score}", (20, 20))
    self.dibujar_texto(f"Vidas: {self.lives}", (20, 50))

    # Mensaje final
    if self.end_message:
        self.dibujar_texto(self.end_message, (260, 280), grande=True)


@arkanoid_method
def run(self) -> None:
    """ Bucle principal del juego."""

    self.inicializar_pygame()
    print("Pygame inicializado")
    self.cargar_nivel()
    print(f"Nivel cargado: {self.layout}")
    self.preparar_entidades()
    print("Entidades preparadas")
    self.crear_bloques()
    print(f"Bloques creados: {len(self.blocks)}")
    self.running = True

    while self.running:

        # Eventos
        for event in self.iterar_eventos():
            if event.type == self.EVENT_QUIT:
                self.running = False
            elif event.type == self.EVENT_KEYDOWN:
                if event.key == self.KEY_ESCAPE:
                    self.running = False

        # Lógica
        self.procesar_input()
        self.actualizar_bola()

        # Dibujado
        self.dibujar_escena()
        self.actualizar_pantalla()

        self.clock.tick(self.FPS)

        # Fin de partida
        if self.lives <= 0:
            self.end_message = "GAME OVER"
            self.dibujar_escena()
            self.actualizar_pantalla()
            self.esperar(1500)
            self.running = False

    self.finalizar_pygame()

if __name__ == "__main__":
    import sys

    # Si el usuario pasa un nivel por terminal, úsalo.
    # Si no, carga demo.txt por defecto.
    level_path = sys.argv[1] if len(sys.argv) > 1 else "niveles/demo.txt"

    juego = ArkanoidGame(level_path)
    juego.run()
