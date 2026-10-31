import json
import os
import sys
import pygame

from .assets import BASE_DIR, load_image, load_sprite, load_font, play_music, stop_music
from .ui import draw_button, draw_panel, draw_title, draw_badge, draw_text, Bubbles, DIFFICULTY_COLORS, TITLE_COLOR

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# Choices shown on the settings screen: (label, value)
DIFFICULTIES = [("Easy", "easy"), ("Normal", "normal"), ("Hard", "hard")]
WIN_SCORES = [(str(n), n) for n in (3, 5, 7, 11, 15)]
COURTS = [("Beach", "background2.jpg"), ("Palm Beach", "background.jpg"), ("Ocean", "background4.jpg")]
SKINS = [("Purple", "player.png"), ("Galaxy", "cpu.png"), ("Green", "1.png"),
         ("Orange", "2.png"), ("Yellow", "3.png"), ("Ghost", "new.png")]
ON_OFF = [("On", True), ("Off", False)]

# CPU behaviour for each difficulty
#   speed    - how fast the CPU walks
#   reaction - frames between CPU decisions (higher = reacts later)
#   error    - how far (px) the CPU may misjudge where the ball is
#   jump     - chance the CPU jumps for a high ball
#   power    - strength of CPU hits (1 = same as the player)
CPU_LEVELS = {
    "easy":   {"speed": 2.0, "reaction": 24, "error": 70, "jump": 0.3, "power": 0.8},
    "normal": {"speed": 3.0, "reaction": 12, "error": 35, "jump": 0.6, "power": 0.9},
    "hard":   {"speed": 4.2, "reaction": 5, "error": 12, "jump": 0.9, "power": 1.0},
}
DIFFICULTY_INFO = {
    "easy": "Slow CPU that reacts late and often misjudges the ball",
    "normal": "Balanced CPU that still makes some mistakes",
    "hard": "Quick CPU with sharp reactions and strong hits",
}

DEFAULTS = {
    "difficulty": "normal",
    "win_score": 7,
    "court": "background2.jpg",
    "p1_skin": "player.png",
    "p2_skin": "cpu.png",
    "music": True,
    "sfx": True,
}

# Shared settings used by every screen
SETTINGS = dict(DEFAULTS)


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        for key, value in saved.items():
            if key in DEFAULTS:
                SETTINGS[key] = value
    except (OSError, ValueError):
        pass


def save_settings():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(SETTINGS, f, indent=2)
    except OSError:
        print("Could not save settings")


def _cycle(choices, current, step):
    values = [v for _, v in choices]
    index = values.index(current) if current in values else 0
    return values[(index + step) % len(values)]


def _label(choices, current):
    for label, value in choices:
        if value == current:
            return label
    return str(current)


def run_settings_screen(screen):
    width, height = screen.get_size()
    title_font = load_font("1.ttf", 56)
    font = pygame.font.SysFont("comicsansms", 24)
    value_font = pygame.font.SysFont("comicsansms", 22, bold=True)
    small_font = pygame.font.SysFont("comicsansms", 16)

    background = load_image("menu1.jpg", (width, height), alpha=False)
    panel_rect = pygame.Rect(50, 15, width - 100, 570)
    stripe = pygame.Surface((width - 140, 46), pygame.SRCALPHA)
    pygame.draw.rect(stripe, (255, 255, 255, 22), stripe.get_rect(), border_radius=12)
    bubbles = Bubbles((width, height), count=15)

    rows = [
        ("CPU Difficulty", "difficulty", DIFFICULTIES),
        ("Points to Win", "win_score", WIN_SCORES),
        ("Court", "court", COURTS),
        ("Player 1 Skin", "p1_skin", SKINS),
        ("Player 2 / CPU Skin", "p2_skin", SKINS),
        ("Music", "music", ON_OFF),
        ("Sound Effects", "sfx", ON_OFF),
    ]
    row_y = [125 + i * 50 for i in range(len(rows))]
    left_arrows = [pygame.Rect(430, y, 40, 40) for y in row_y]
    right_arrows = [pygame.Rect(680, y, 40, 40) for y in row_y]
    back_button = pygame.Rect(width // 2 - 120, 507, 240, 50)

    skin_cache = {}

    def skin_preview(name):
        if name not in skin_cache:
            skin_cache[name] = load_sprite(name, 44)
        return skin_cache[name]

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_settings()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                save_settings()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(event.pos):
                    save_settings()
                    return
                for i, (_, key, choices) in enumerate(rows):
                    step = -1 if left_arrows[i].collidepoint(event.pos) else 1 if right_arrows[i].collidepoint(event.pos) else 0
                    if step:
                        SETTINGS[key] = _cycle(choices, SETTINGS[key], step)
                        if key == "music":
                            if SETTINGS["music"]:
                                play_music("background.mp3")
                            else:
                                stop_music()

        screen.blit(background, (0, 0))
        bubbles.update_and_draw(screen)
        draw_panel(screen, panel_rect)
        draw_title(screen, "Game Settings", title_font, (width // 2, 65))

        for i, (name, key, choices) in enumerate(rows):
            y = row_y[i]
            if i % 2 == 0:
                screen.blit(stripe, (70, y - 3))
            label = font.render(name, True, (235, 240, 255))
            screen.blit(label, (85, y + 20 - label.get_height() // 2))
            draw_button(screen, left_arrows[i], "<", font)
            draw_button(screen, right_arrows[i], ">", font)
            text = _label(choices, SETTINGS[key])
            if key == "difficulty":
                draw_badge(screen, text, value_font, DIFFICULTY_COLORS[SETTINGS[key]], (575, y + 20))
                continue
            if key in ("music", "sfx"):
                draw_badge(screen, text, value_font, DIFFICULTY_COLORS["easy"] if SETTINGS[key] else (120, 110, 140),
                           (575, y + 20))
                continue
            value = value_font.render(text, True, TITLE_COLOR)
            value_rect = value.get_rect(center=(575, y + 20))
            if key in ("p1_skin", "p2_skin"):
                preview = skin_preview(SETTINGS[key])
                value_rect.centerx += 20
                screen.blit(preview, preview.get_rect(midright=(value_rect.left - 6, y + 20)))
            screen.blit(value, value_rect)

        info = DIFFICULTY_INFO.get(SETTINGS["difficulty"], "")
        draw_text(screen, info, small_font, DIFFICULTY_COLORS[SETTINGS["difficulty"]], (width // 2, 484), shadow=1)
        draw_button(screen, back_button, "Back", font)
        hint = small_font.render("Settings are saved automatically", True, (205, 190, 240))
        screen.blit(hint, hint.get_rect(center=(width // 2, 572)))

        pygame.display.flip()
        clock.tick(60)
