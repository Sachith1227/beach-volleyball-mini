import pygame
import sys
import random

from .assets import load_image, load_sprite, load_sound, load_font, play_music
from .settings import SETTINGS, CPU_LEVELS, load_settings
from .ui import (overlay_menu, draw_court, draw_shadow, draw_scoreboard, draw_serve_text, draw_badge,
                Particles, DIFFICULTY_COLORS)

WIDTH, HEIGHT = 800, 600


def play_game(screen=None):
    """Player vs CPU. Returns when the user chooses 'Main Menu'."""
    pygame.init()

    # Screen setup (reuse the menu's window when called from the menu)
    if screen is None:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Beach Volleyball Mini - Single Player")

    # Load background image
    background = load_image(SETTINGS["court"], (WIDTH, HEIGHT), alpha=False)

    # Colors
    SCORE_COLOR_PLAYER = (255, 255, 0)
    SCORE_COLOR_CPU = (255, 100, 100)
    GROUND_HEIGHT = 50
    GROUND_Y = HEIGHT - GROUND_HEIGHT

    # --- Player setup ---
    PLAYER_WIDTH = 150
    player_image = load_sprite(SETTINGS["p1_skin"], PLAYER_WIDTH)
    PLAYER_HALF = PLAYER_WIDTH // 2
    PLAYER_HEIGHT = player_image.get_height()
    PLAYER_SPEED = 6
    JUMP_STRENGTH = -8

    # --- CPU setup ---
    cpu_image = load_sprite(SETTINGS["p2_skin"], PLAYER_WIDTH)
    CPU_HEIGHT = cpu_image.get_height()
    difficulty = SETTINGS["difficulty"] if SETTINGS["difficulty"] in CPU_LEVELS else "normal"
    cpu_level = CPU_LEVELS[difficulty]
    CPU_SPEED = cpu_level["speed"]
    CPU_REACH = 110
    CPU_JUMP_STRENGTH = -8

    # Masks for pixel-perfect collision
    player_mask = pygame.mask.from_surface(player_image)
    cpu_mask = pygame.mask.from_surface(cpu_image)

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
        nonlocal player_score, cpu_score
        nonlocal player_x, player_y, player_vy, on_ground
        nonlocal cpu_x, cpu_y, cpu_vy, cpu_on_ground
        player_score = cpu_score = 0
        player_x, player_y, player_vy, on_ground = WIDTH // 4, GROUND_Y - PLAYER_HEIGHT, 0, True
        cpu_x, cpu_y, cpu_vy, cpu_on_ground = 3 * WIDTH // 4, GROUND_Y - CPU_HEIGHT, 0, True
        floating_points.clear()
        particles.clear()
        reset_ball()

    def reset_ball():
        nonlocal ball_x, ball_y, ball_vx, ball_vy, serve_timer
        ball_x, ball_y = WIDTH // 2, 100
        ball_vx, ball_vy = 4 * random.choice([-1, 1]), 0
        serve_timer = SERVE_DELAY

    # Game state (filled in by reset_match)
    player_score = cpu_score = 0
    player_x = player_y = player_vy = 0
    cpu_x = cpu_y = cpu_vy = 0
    on_ground = cpu_on_ground = True
    ball_x = ball_y = ball_vx = ball_vy = 0
    serve_timer = 0
    player_cooldown = cpu_cooldown = 0
    cpu_think = 0
    cpu_target = 3 * WIDTH // 4
    cpu_wants_jump = False
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

        # --- PLAYER CONTROLS (arrows or A/D/W, Space also jumps) ---
        keys = pygame.key.get_pressed()
        player_vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player_vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player_vx = PLAYER_SPEED
        if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]) and on_ground:
            player_vy = JUMP_STRENGTH
            on_ground = False

        # Apply gravity
        player_vy += GRAVITY
        player_y += player_vy
        player_x += player_vx
        cpu_vy += GRAVITY
        cpu_y += cpu_vy

        # Ground collisions
        if player_y + PLAYER_HEIGHT >= GROUND_Y:
            player_y = GROUND_Y - PLAYER_HEIGHT
            player_vy = 0
            on_ground = True
        if cpu_y + CPU_HEIGHT >= GROUND_Y:
            cpu_y = GROUND_Y - CPU_HEIGHT
            cpu_vy = 0
            cpu_on_ground = True

        # Keep player inside left half
        player_x = max(PLAYER_HALF, min(player_x, net_rect.left - PLAYER_HALF))

        # CPU auto movement: it only re-thinks every few frames and may misjudge the ball,
        # so easier levels react late and miss more often
        ball_on_cpu_side = ball_x > WIDTH // 2 and serve_timer == 0
        cpu_think -= 1
        if cpu_think <= 0:
            cpu_think = cpu_level["reaction"]
            if ball_on_cpu_side:
                # stand slightly behind the ball so it is hit towards the player
                cpu_target = ball_x + 20 + random.uniform(-cpu_level["error"], cpu_level["error"])
                cpu_wants_jump = random.random() < cpu_level["jump"]
            else:
                cpu_target = 3 * WIDTH // 4
                cpu_wants_jump = False
        if (ball_on_cpu_side and cpu_wants_jump and cpu_on_ground and abs(ball_x - cpu_x) < CPU_REACH
                and ball_y < cpu_y and ball_vy > -2):
            cpu_vy = CPU_JUMP_STRENGTH
            cpu_on_ground = False
        if abs(cpu_target - cpu_x) > CPU_SPEED:
            cpu_x += CPU_SPEED if cpu_target > cpu_x else -CPU_SPEED
        cpu_x = max(net_rect.right + PLAYER_HALF, min(cpu_x, WIDTH - PLAYER_HALF))

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
                    cpu_score += 1
                    text_surf = font.render("+1", True, SCORE_COLOR_CPU)
                    floating_points.append([WIDTH * 3 // 4, HEIGHT // 2 - 100, text_surf, 255])
                else:
                    player_score += 1
                    text_surf = font.render("+1", True, SCORE_COLOR_PLAYER)
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
        player_pos = (int(player_x - PLAYER_HALF), int(player_y))
        cpu_pos = (int(cpu_x - PLAYER_HALF), int(cpu_y))
        ball_pos = (int(ball_x - BALL_RADIUS), int(ball_y - BALL_RADIUS))

        offset_player = (ball_pos[0] - player_pos[0], ball_pos[1] - player_pos[1])
        offset_cpu = (ball_pos[0] - cpu_pos[0], ball_pos[1] - cpu_pos[1])

        player_cooldown = max(0, player_cooldown - 1)
        cpu_cooldown = max(0, cpu_cooldown - 1)
        if serve_timer == 0 and player_cooldown == 0 and player_mask.overlap(ball_mask, offset_player):
            ball_vy = -abs(ball_vy) - 3
            ball_vx += (ball_x - player_x) / PLAYER_HALF * 3
            player_cooldown = HIT_COOLDOWN
            hit_sound.play()
            particles.burst(ball_x, ball_y, (255, 255, 255), count=10, speed=3)
        if serve_timer == 0 and cpu_cooldown == 0 and cpu_mask.overlap(ball_mask, offset_cpu):
            ball_vy = (-abs(ball_vy) - 3) * cpu_level["power"]
            ball_vx += (ball_x - cpu_x) / PLAYER_HALF * 3 * cpu_level["power"]
            cpu_cooldown = HIT_COOLDOWN
            hit_sound.play()
            particles.burst(ball_x, ball_y, (255, 255, 255), count=10, speed=3)

        # --- DRAW ---
        screen.blit(background, (0, 0))
        draw_court(screen, net_rect, GROUND_Y)
        draw_shadow(screen, player_x, GROUND_Y, PLAYER_WIDTH * 0.8, GROUND_Y - (player_y + PLAYER_HEIGHT))
        draw_shadow(screen, cpu_x, GROUND_Y, PLAYER_WIDTH * 0.8, GROUND_Y - (cpu_y + CPU_HEIGHT))
        draw_shadow(screen, ball_x, GROUND_Y, BALL_RADIUS * 1.6, GROUND_Y - (ball_y + BALL_RADIUS))
        screen.blit(player_image, player_pos)
        screen.blit(cpu_image, cpu_pos)
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
            fp[1] -= 1  # move up
            fp[3] -= 5  # fade out
            if fp[3] <= 0:
                floating_points.remove(fp)

        # Scoreboard
        draw_scoreboard(screen, "PLAYER", player_score, "CPU", cpu_score, WIN_SCORE,
                        SCORE_COLOR_PLAYER, SCORE_COLOR_CPU, name_font, big_score_font, small_font)
        draw_badge(screen, f"CPU: {difficulty.upper()}", small_font, DIFFICULTY_COLORS[difficulty], (WIDTH // 2, 104))
        draw_serve_text(screen, serve_timer, SERVE_DELAY, serve_font)
        hint = hint_font.render("P / Esc: pause", True, (255, 255, 255))
        screen.blit(hint, (10, HEIGHT - 22))

        # --- WIN CONDITION POPUP ---
        winner = None
        if player_score >= WIN_SCORE:
            winner = "Player"
        elif cpu_score >= WIN_SCORE:
            winner = "CPU"

        if winner:
            pygame.display.flip()
            win_sound.play()
            choice = overlay_menu(screen, f"{winner} Wins!", ["Play Again", "Main Menu"], win_font, button_font)
            if choice == "Main Menu":
                return
            reset_match()
            continue

        pygame.display.flip()


if __name__ == "__main__":
    load_settings()
    play_game()
