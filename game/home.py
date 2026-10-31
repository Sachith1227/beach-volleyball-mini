import pygame
import sys

from .menu import run_menu_screen
from .assets import load_image, load_font
from .settings import load_settings
from .ui import Button, Bubbles, draw_title, draw_badge, draw_top_shade, ACCENT_COLOR

WIDTH, HEIGHT = 800, 600


def quit_action():
    pygame.quit()
    sys.exit()


def make_buttons(screen):
    return [
        Button("Single Player", (WIDTH//2 - 150, 300, 300, 60), lambda: run_menu_screen("single", screen),
               delay=0.1, pulse=True),
        Button("Multiplayer", (WIDTH//2 - 150, 390, 300, 60), lambda: run_menu_screen("multi", screen), delay=0.2),
        Button("Quit", (WIDTH//2 - 150, 480, 300, 60), quit_action, delay=0.3)
    ]


# Run home menu (the game's starting screen)
def run_home():
    load_settings()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # Fonts
    button_font = pygame.font.SysFont("comicsansms", 30, bold=True)
    title_font = load_font("1.ttf", 90)
    subtitle_font = pygame.font.SysFont("comicsansms", 22, bold=True)

    # Load home background
    home_background = load_image("menu.jpg", (WIDTH, HEIGHT), alpha=False)

    clock = pygame.time.Clock()
    bubbles = Bubbles((WIDTH, HEIGHT))
    buttons = make_buttons(screen)

    running = True
    while running:
        pygame.display.set_caption("Beach Volleyball Mini - Home")
        screen.blit(home_background, (0, 0))
        bubbles.update_and_draw(screen)
        draw_top_shade(screen, 260)
        draw_title(screen, "Beach", title_font, (WIDTH // 2, 95))
        draw_title(screen, "Volleyball", title_font, (WIDTH // 2, 175), (255, 255, 255))
        draw_badge(screen, "MINI", subtitle_font, ACCENT_COLOR, (WIDTH // 2, 245))

        for button in buttons:
            button.draw(screen, button_font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.hovered:
                        button.click()
                        buttons = make_buttons(screen)  # replay the slide-in when coming back
                        break

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_home()
