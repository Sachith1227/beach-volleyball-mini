import pygame
import sys
from .single_player import play_game as single_game
from .multiplayer import play_game as multi_game
from .assets import load_image, load_font, play_music, stop_music
from .settings import SETTINGS, load_settings, save_settings, run_settings_screen
from .ui import Button, Bubbles, draw_title, draw_top_shade

WIDTH, HEIGHT = 800, 600

# -------------------------
# Actions
# -------------------------
def start_game_action(mode, screen):
    stop_music()
    if mode == "single":
        single_game(screen)
    else:
        multi_game(screen)
    # Back from the game -> restore the menu
    stop_music()
    pygame.display.set_caption("Volleyball Game - Menu")
    play_music("background.mp3", 0.5, SETTINGS["music"])

def game_settings(screen):
    run_settings_screen(screen)
    pygame.display.set_caption("Volleyball Game - Menu")

def mute_sound():
    SETTINGS["music"] = not SETTINGS["music"]
    save_settings()
    if SETTINGS["music"]:
        play_music("background.mp3", 0.5)
    else:
        stop_music()

def back_to_home():
    return "back"

def quit_game():
    pygame.quit()
    sys.exit()

# -------------------------
# Function to run menu in same window
# -------------------------
def run_menu_screen(mode, screen):
    pygame.font.init()
    button_font = pygame.font.SysFont("comicsansms", 28, bold=True)
    title_font = load_font("1.ttf", 70)

    pygame.display.set_caption("Volleyball Game - Menu")

    # Load menu background
    menu_background = load_image("menu.jpg", (WIDTH, HEIGHT), alpha=False)
    bubbles = Bubbles((WIDTH, HEIGHT))

    # Load and play background music
    play_music("background.mp3", 0.5, SETTINGS["music"])

    # Setup buttons
    clock = pygame.time.Clock()
    buttons = [
        Button("Start", (WIDTH//2 - 130, 222, 260, 52), lambda: start_game_action(mode, screen), delay=0.1, pulse=True),
        Button("Game Settings", (WIDTH//2 - 130, 292, 260, 52), lambda: game_settings(screen), delay=0.2),
        Button("Mute", (WIDTH//2 - 130, 362, 260, 52), mute_sound, delay=0.3),
        Button("Back", (WIDTH//2 - 130, 432, 260, 52), back_to_home, delay=0.4),
        Button("Quit", (WIDTH//2 - 130, 502, 260, 52), quit_game, delay=0.5)
    ]
    title = "Single Player" if mode == "single" else "Multiplayer"

    # Menu loop
    running = True
    while running:
        screen.blit(menu_background, (0, 0))
        bubbles.update_and_draw(screen)
        draw_top_shade(screen, 220)
        draw_title(screen, title, title_font, (WIDTH // 2, 85))

        buttons[2].text = "Mute" if SETTINGS["music"] else "Unmute"
        for button in buttons:
            button.draw(screen, button_font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.hovered:
                        result = button.click()
                        if result == "back":
                            running = False  # exit menu loop, return to home
                        break

        pygame.display.flip()
        clock.tick(60)

# -------------------------
# Optional: run standalone
# -------------------------
if __name__ == "__main__":
    pygame.init()
    load_settings()
    run_menu_screen("single", pygame.display.set_mode((WIDTH, HEIGHT)))
