import pygame
import sys
import random

from .assets import load_image, load_sprite, load_sound, load_font, play_music
from .settings import SETTINGS, load_settings
from .ui import overlay_menu, draw_court, draw_shadow, draw_scoreboard, draw_serve_text, Particles

WIDTH, HEIGHT = 800, 600


def play_game(screen=None):
    """Player 1 (WASD) vs Player 2 (arrows). Returns when the user chooses 'Main Menu'."""
    pygame.init()

    # Screen setup (reuse the menu's window when called from the menu)
    if screen is None:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Beach Volleyball Mini - Multiplayer")

    # Load background image
    background = load_image(SETTINGS["court"], (WIDTH, HEIGHT), alpha=False)

    # Colors
    SCORE_COLOR_P1 = (255, 255, 0)
    SCORE_COLOR_P2 = (255, 100, 100)
    GROUND_HEIGHT = 50
    GROUND_Y = HEIGHT - GROUND_HEIGHT


    # --- Players setup (P1 left, P2 right) ---
    PLAYER_WIDTH = 150
    PLAYER_HALF = PLAYER_WIDTH // 2
    PLAYER_SPEED = 6
    JUMP_STRENGTH = -8
    p1_image = load_sprite(SETTINGS["p1_skin"], PLAYER_WIDTH)
    p2_image = load_sprite(SETTINGS["p2_skin"], PLAYER_WIDTH)
    P1_HEIGHT = p1_image.get_height()
    P2_HEIGHT = p2_image.get_height()

    # Masks for pixel-perfect collision
    p1_mask = pygame.mask.from_surface(p1_image)
    p2_mask = pygame.mask.from_surface(p2_image)

    # --- Ball setup ---
    BALL_RADIUS = 36
    GRAVITY = 0.2
    BOUNCE = -0.8
    MAX_VX = 7
    MAX_VY = 10
    SERVE_DELAY = 60      # frames the ball waits before each serve
    HIT_COOLDOWN = 12     # frames before the same player can hit again

    ball_image = load_image("ball.png", (BALL_RADIUS * 2, BALL_RADIUS * 2), crop=True)
    ball_mask = pygame.mask.from_surface(ball_image)

    # Net
    NET_WIDTH = 15
    NET_HEIGHT = 170
    net_rect = pygame.Rect(WIDTH // 2 - NET_WIDTH // 2, GROUND_Y - NET_HEIGHT, NET_WIDTH, NET_HEIGHT)

    # Load sounds
    sfx_volume = 1 if SETTINGS["sfx"] else 0
    point_sound = load_sound("point.wav", 0.7 * sfx_volume)
    hit_sound = load_sound("jump.wav", 0.5 * sfx_volume)
    win_sound = load_sound("win.wav", 0.7 * sfx_volume)

    # Fonts
    font = pygame.font.SysFont(None, 40)
    win_font = load_font("1.ttf", 80)
    button_font = pygame.font.SysFont(None, 40)
    hint_font = pygame.font.SysFont(None, 24)
    name_font = pygame.font.SysFont("arial", 20, bold=True)
    big_score_font = pygame.font.SysFont("arial", 40, bold=True)
    small_font = pygame.font.SysFont("arial", 14, bold=True)
    serve_font = load_font("1.ttf", 70)
    WIN_SCORE = SETTINGS["win_score"]

    play_music("background2.mp3", 0.35, SETTINGS["music"])

    def reset_match():
        nonlocal p1_score, p2_score
        nonlocal p1_x, p1_y, p1_vy, p1_on_ground
        nonlocal p2_x, p2_y, p2_vy, p2_on_ground
        p1_score = p2_score = 0
        p1_x, p1_y, p1_vy, p1_on_ground = WIDTH // 4, GROUND_Y - P1_HEIGHT, 0, True
        p2_x, p2_y, p2_vy, p2_on_ground = 3 * WIDTH // 4, GROUND_Y - P2_HEIGHT, 0, True
        floating_points.clear()
        particles.clear()
        reset_ball()

    def reset_ball():
        nonlocal ball_x, ball_y, ball_vx, ball_vy, serve_timer
        ball_x, ball_y = WIDTH // 2, 100
        ball_vx, ball_vy = 4 * random.choice([-1, 1]), 0
        serve_timer = SERVE_DELAY

    # Game state (filled in by reset_match)
    p1_score = p2_score = 0
    p1_x = p1_y = p1_vy = 0
    p2_x = p2_y = p2_vy = 0
    p1_on_ground = p2_on_ground = True
    ball_x = ball_y = ball_vx = ball_vy = 0
    serve_timer = 0
    p1_cooldown = p2_cooldown = 0
    floating_points = []  # Each element: [x, y, surface, alpha]
    particles = Particles()
    ball_angle = 0
    reset_match()

    # Game loop
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_p, pygame.K_ESCAPE):
                choice = overlay_menu(screen, "Paused", ["Resume", "Restart", "Main Menu"],
                                      win_font, button_font, cancel="Resume")
                if choice == "Restart":
                    reset_match()
                elif choice == "Main Menu":
                    return

        # --- PLAYER CONTROLS ---
        keys = pygame.key.get_pressed()

        # Player 1 (WASD)
        p1_vx = 0
        if keys[pygame.K_a]:
            p1_vx = -PLAYER_SPEED
        if keys[pygame.K_d]:
            p1_vx = PLAYER_SPEED
        if keys[pygame.K_w] and p1_on_ground:
            p1_vy = JUMP_STRENGTH
            p1_on_ground = False

        # Player 2 (Arrows)
        p2_vx = 0
        if keys[pygame.K_LEFT]:
            p2_vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            p2_vx = PLAYER_SPEED
        if keys[pygame.K_UP] and p2_on_ground:
            p2_vy = JUMP_STRENGTH
            p2_on_ground = False

        # Apply gravity + movement
        p1_vy += GRAVITY
        p1_y += p1_vy
        p1_x += p1_vx

        p2_vy += GRAVITY
        p2_y += p2_vy
        p2_x += p2_vx

        # Ground collisions
        if p1_y + P1_HEIGHT >= GROUND_Y:
            p1_y = GROUND_Y - P1_HEIGHT
            p1_vy = 0
            p1_on_ground = True
        if p2_y + P2_HEIGHT >= GROUND_Y:
            p2_y = GROUND_Y - P2_HEIGHT
            p2_vy = 0
            p2_on_ground = True

        # Keep players inside their halves
        p1_x = max(PLAYER_HALF, min(p1_x, net_rect.left - PLAYER_HALF))
        p2_x = max(net_rect.right + PLAYER_HALF, min(p2_x, WIDTH - PLAYER_HALF))

        # --- BALL PHYSICS ---
        if serve_timer > 0:
            serve_timer -= 1
        else:
            prev_ball_bottom = ball_y + BALL_RADIUS
            ball_vy += GRAVITY
            ball_vx = max(min(ball_vx, MAX_VX), -MAX_VX)
            ball_vy = max(min(ball_vy, MAX_VY), -MAX_VY)
            ball_x += ball_vx
            ball_y += ball_vy

            # Ground collision for ball -> point for the other side
            if ball_y + BALL_RADIUS >= GROUND_Y:
                if ball_x < WIDTH // 2:
                    p2_score += 1
                    text_surf = font.render("+1", True, SCORE_COLOR_P2)
                    floating_points.append([WIDTH * 3 // 4, HEIGHT // 2 - 100, text_surf, 255])
                else:
                    p1_score += 1
                    text_surf = font.render("+1", True, SCORE_COLOR_P1)
                    floating_points.append([WIDTH // 4, HEIGHT // 2 - 100, text_surf, 255])
                particles.burst(ball_x, GROUND_Y, (240, 210, 150), count=25, speed=5, upward=True)
                point_sound.play()
                reset_ball()

            # Wall collisions
            if ball_x - BALL_RADIUS < 0:
                ball_x = BALL_RADIUS
                ball_vx = abs(ball_vx)
            if ball_x + BALL_RADIUS > WIDTH:
                ball_x = WIDTH - BALL_RADIUS
                ball_vx = -abs(ball_vx)
            if ball_y - BALL_RADIUS < 0:
                ball_y = BALL_RADIUS
                ball_vy = abs(ball_vy)

            # Net collision: bounce off the top, or get pushed back to the side it came from
            ball_rect = pygame.Rect(ball_x - BALL_RADIUS, ball_y - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
            if ball_rect.colliderect(net_rect):
                if prev_ball_bottom <= net_rect.top:
                    ball_y = net_rect.top - BALL_RADIUS
                    ball_vy = BOUNCE * abs(ball_vy) - 1
                    if abs(ball_vx) < 1.5:
                        ball_vx = random.choice([-1.5, 1.5])
                elif ball_x < WIDTH // 2:
                    ball_x = net_rect.left - BALL_RADIUS
                    ball_vx = -abs(ball_vx)
                else:
                    ball_x = net_rect.right + BALL_RADIUS
                    ball_vx = abs(ball_vx)

        # Pixel-perfect collision
        p1_pos = (int(p1_x - PLAYER_HALF), int(p1_y))
        p2_pos = (int(p2_x - PLAYER_HALF), int(p2_y))
        ball_pos = (int(ball_x - BALL_RADIUS), int(ball_y - BALL_RADIUS))

        offset_p1 = (ball_pos[0] - p1_pos[0], ball_pos[1] - p1_pos[1])
        offset_p2 = (ball_pos[0] - p2_pos[0], ball_pos[1] - p2_pos[1])

        p1_cooldown = max(0, p1_cooldown - 1)
        p2_cooldown = max(0, p2_cooldown - 1)
        if serve_timer == 0 and p1_cooldown == 0 and p1_mask.overlap(ball_mask, offset_p1):
            ball_vy = -abs(ball_vy) - 3
            ball_vx += (ball_x - p1_x) / PLAYER_HALF * 3
            p1_cooldown = HIT_COOLDOWN
            hit_sound.play()
            particles.burst(ball_x, ball_y, (255, 255, 255), count=10, speed=3)
        if serve_timer == 0 and p2_cooldown == 0 and p2_mask.overlap(ball_mask, offset_p2):
            ball_vy = -abs(ball_vy) - 3
            ball_vx += (ball_x - p2_x) / PLAYER_HALF * 3
            p2_cooldown = HIT_COOLDOWN
            hit_sound.play()
            particles.burst(ball_x, ball_y, (255, 255, 255), count=10, speed=3)

        # --- DRAW ---
        screen.blit(background, (0, 0))
        draw_court(screen, net_rect, GROUND_Y)
        draw_shadow(screen, p1_x, GROUND_Y, PLAYER_WIDTH * 0.8, GROUND_Y - (p1_y + P1_HEIGHT))
        draw_shadow(screen, p2_x, GROUND_Y, PLAYER_WIDTH * 0.8, GROUND_Y - (p2_y + P2_HEIGHT))
        draw_shadow(screen, ball_x, GROUND_Y, BALL_RADIUS * 1.6, GROUND_Y - (ball_y + BALL_RADIUS))
        screen.blit(p1_image, p1_pos)
        screen.blit(p2_image, p2_pos)
        if serve_timer == 0:
            ball_angle = (ball_angle - ball_vx * 2.5) % 360
        spun_ball = pygame.transform.rotozoom(ball_image, ball_angle, 1)
        screen.blit(spun_ball, spun_ball.get_rect(center=(int(ball_x), int(ball_y))))
        particles.update_and_draw(screen)

        # Draw floating points
        for fp in floating_points[:]:
            x, y, surf, alpha = fp
            surf.set_alpha(alpha)
            screen.blit(surf, (x - surf.get_width() // 2, y))
            fp[1] -= 1
            fp[3] -= 5
            if fp[3] <= 0:
                floating_points.remove(fp)

        # Scoreboard
        draw_scoreboard(screen, "PLAYER 1", p1_score, "PLAYER 2", p2_score, WIN_SCORE,
                        SCORE_COLOR_P1, SCORE_COLOR_P2, name_font, big_score_font, small_font)
        draw_serve_text(screen, serve_timer, SERVE_DELAY, serve_font)
        hint = hint_font.render("P / Esc: pause", True, (255, 255, 255))
        screen.blit(hint, (10, HEIGHT - 22))

        # --- WIN CONDITION POPUP ---
        winner = None
        if p1_score >= WIN_SCORE:
            winner = "Player 1"
        elif p2_score >= WIN_SCORE:
            winner = "Player 2"

        if winner:
            pygame.display.flip()
            win_sound.play()
            choice = overlay_menu(screen, f"{winner} Wins!", ["Play Again", "Main Menu"],
                                  win_font, button_font)
            if choice == "Main Menu":
                return
            reset_match()
            continue

        pygame.display.flip()


if __name__ == "__main__":
    load_settings()
    play_game()
