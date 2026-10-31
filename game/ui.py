import math
import random
import sys
import pygame

# Default button colors (violet)
BUTTON_COLOR = (124, 77, 255)
BUTTON_HOVER = (167, 139, 250)
BUTTON_SHADOW = (55, 25, 125)
BORDER_COLOR = (255, 255, 255)
TITLE_COLOR = (120, 255, 214)
OUTLINE_COLOR = (40, 15, 75)
ACCENT_COLOR = (255, 110, 180)
PANEL_TOP = (70, 35, 120)
PANEL_BOTTOM = (28, 10, 55)

# Colour for each CPU difficulty (settings screen and in-game badge)
DIFFICULTY_COLORS = {"easy": (20, 184, 166), "normal": (99, 102, 241), "hard": (236, 72, 153)}

_button_cache = {}
_panel_cache = {}


def _shade(color, amount):
    return tuple(max(0, min(255, int(c + amount))) for c in color[:3])


def _lerp(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def _rounded(surface, radius):
    """Cut a surface down to a rounded rectangle."""
    mask = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return surface


def _button_face(size, color):
    """Gradient button body with a glossy top half (built once per size/colour)."""
    key = (size, color)
    if key not in _button_cache:
        w, h = size
        radius = min(18, h // 2)
        face = pygame.Surface(size, pygame.SRCALPHA)
        top, bottom = _shade(color, 55), _shade(color, -40)
        for y in range(h):
            pygame.draw.line(face, _lerp(top, bottom, y / max(1, h - 1)), (0, y), (w, y))
        gloss = pygame.Surface((max(1, w - 12), max(1, h // 2 - 3)), pygame.SRCALPHA)
        pygame.draw.rect(gloss, (255, 255, 255, 55), gloss.get_rect(), border_radius=radius)
        face.blit(gloss, (6, 3))
        _rounded(face, radius)
        pygame.draw.rect(face, BORDER_COLOR, face.get_rect(), 2, border_radius=radius)
        _button_cache[key] = face
    return _button_cache[key]


def draw_text(screen, text, font, color, center, outline=0, shadow=0, outline_color=OUTLINE_COLOR):
    """Text centred on a point, with an optional outline and drop shadow."""
    if outline or shadow:
        back = font.render(text, True, outline_color)
        if shadow:
            screen.blit(back, back.get_rect(center=(center[0] + shadow, center[1] + shadow)))
        for dx in range(-outline, outline + 1, max(1, outline)):
            for dy in range(-outline, outline + 1, max(1, outline)):
                if dx or dy:
                    screen.blit(back, back.get_rect(center=(center[0] + dx, center[1] + dy)))
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    screen.blit(surf, rect)
    return rect


def draw_title(screen, text, font, center, color=TITLE_COLOR):
    """Big outlined title that gently bobs up and down."""
    bob = math.sin(pygame.time.get_ticks() / 500) * 4
    return draw_text(screen, text, font, color, (center[0], center[1] + bob), outline=3, shadow=6)


def draw_panel(screen, rect, alpha=210):
    """Dark glass panel with a soft border."""
    rect = pygame.Rect(rect)
    key = (rect.size, alpha)
    if key not in _panel_cache:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(rect.h):
            color = _lerp(PANEL_TOP, PANEL_BOTTOM, y / max(1, rect.h - 1))
            pygame.draw.line(panel, (*color, alpha), (0, y), (rect.w, y))
        _rounded(panel, 22)
        border = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(border, (255, 255, 255, 110), border.get_rect(), 2, border_radius=22)
        panel.blit(border, (0, 0))
        _panel_cache[key] = panel
    screen.blit(_panel_cache[key], rect)


def draw_top_shade(screen, height=200, alpha=150):
    """Darken the top of the screen so titles stand out."""
    key = ("shade", screen.get_width(), height, alpha)
    if key not in _panel_cache:
        shade = pygame.Surface((screen.get_width(), height), pygame.SRCALPHA)
        for y in range(height):
            pygame.draw.line(shade, (*PANEL_BOTTOM, int(alpha * (1 - y / height))), (0, y), (shade.get_width(), y))
        _panel_cache[key] = shade
    screen.blit(_panel_cache[key], (0, 0))


def draw_badge(screen, text, font, color, center):
    """Small coloured pill with white text. Returns its rect."""
    label = font.render(text, True, BORDER_COLOR)
    rect = label.get_rect(center=center).inflate(26, 10)
    pygame.draw.rect(screen, _shade(color, -60), rect.move(0, 3), border_radius=rect.h // 2)
    pygame.draw.rect(screen, color, rect, border_radius=rect.h // 2)
    pygame.draw.rect(screen, BORDER_COLOR, rect, 2, border_radius=rect.h // 2)
    screen.blit(label, label.get_rect(center=rect.center))
    return rect


def draw_button(screen, rect, text, font, colors=None):
    color, hover, shadow_color = colors or (BUTTON_COLOR, BUTTON_HOVER, BUTTON_SHADOW)
    hovered = rect.collidepoint(pygame.mouse.get_pos())
    radius = min(18, rect.h // 2)
    body = rect.move(0, -3) if hovered else rect
    if hovered:
        glow = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*hover[:3], 80), glow.get_rect(), border_radius=radius + 10)
        screen.blit(glow, glow.get_rect(center=body.center))
    pygame.draw.rect(screen, shadow_color, rect.move(0, 6), border_radius=radius)
    screen.blit(_button_face(rect.size, tuple(hover if hovered else color)), body)
    draw_text(screen, text, font, BORDER_COLOR, body.center, shadow=2, outline_color=_shade(color, -90))
    return hovered


class Button:
    """Menu button that slides up into place; `pulse` makes it glow to draw attention."""

    def __init__(self, text, rect, action=None, delay=0.0, pulse=False, colors=None):
        self.text = text
        self.final_rect = pygame.Rect(rect)
        self.rect = self.final_rect.copy()
        self.action = action
        self.delay = delay
        self.pulse = pulse
        self.colors = colors or (BUTTON_COLOR, BUTTON_HOVER, BUTTON_SHADOW)
        self.hovered = False
        self.start = pygame.time.get_ticks()

    def draw(self, screen, font):
        elapsed = (pygame.time.get_ticks() - self.start) / 1000 - self.delay
        t = max(0.0, min(1.0, elapsed / 0.45))
        ease = 1 - (1 - t) ** 3
        self.rect = self.final_rect.move(0, int((1 - ease) * (screen.get_height() - self.final_rect.y + 60)))
        color, hover, shadow = self.colors
        if self.pulse:
            pulse = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2
            color = _lerp(color, ACCENT_COLOR, pulse)
        self.hovered = draw_button(screen, self.rect, self.text, font, (color, hover, shadow)) and t >= 1
        return self.hovered

    def click(self):
        return self.action() if self.action else None


class Bubbles:
    """Bubbles drifting up behind the menus."""

    def __init__(self, size, count=22):
        self.width, self.height = size
        self.items = [self._new(random.uniform(0, self.height)) for _ in range(count)]
        self.sprites = {}

    def _new(self, y):
        # [x, y, radius, speed, wobble phase]
        return [random.uniform(0, self.width), y, random.randint(4, 14), random.uniform(0.4, 1.4),
                random.uniform(0, math.tau)]

    def _sprite(self, r):
        if r not in self.sprites:
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, 40), (r + 1, r + 1), r)
            pygame.draw.circle(s, (255, 255, 255, 140), (r + 1, r + 1), r, 1)
            pygame.draw.circle(s, (255, 255, 255, 170), (int(r * 0.6) + 1, int(r * 0.6) + 1), max(1, r // 4))
            self.sprites[r] = s
        return self.sprites[r]

    def update_and_draw(self, screen):
        t = pygame.time.get_ticks() / 700
        for i, b in enumerate(self.items):
            b[1] -= b[3]
            if b[1] < -b[2] * 2:
                self.items[i] = b = self._new(self.height + 20)
            x = b[0] + math.sin(t + b[4]) * 8
            screen.blit(self._sprite(b[2]), (int(x - b[2]), int(b[1] - b[2])))


def overlay_menu(screen, title, options, title_font, button_font, colors=None, cancel=None):
    """Dim the current frame and show a title with a column of buttons on a panel.

    Blocks until a button is clicked and returns its text.
    Pressing ESC / P returns `cancel` (if given).
    """
    width, height = screen.get_size()
    frozen = screen.copy()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((*PANEL_BOTTOM, 160))

    panel = pygame.Rect(0, 0, max(380, title_font.size(title)[0] + 70), 135 + len(options) * 75)
    panel.center = (width // 2, height // 2)
    rects = {}
    for i, text in enumerate(options):
        rects[text] = pygame.Rect(width // 2 - 120, panel.top + 110 + i * 75, 240, 55)

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and cancel and event.key in (pygame.K_ESCAPE, pygame.K_p):
                return cancel
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for text, rect in rects.items():
                    if rect.collidepoint(event.pos):
                        return text

        screen.blit(frozen, (0, 0))
        screen.blit(overlay, (0, 0))
        draw_panel(screen, panel)
        draw_title(screen, title, title_font, (width // 2, panel.top + 55))
        for text, rect in rects.items():
            draw_button(screen, rect, text, button_font, colors)
        pygame.display.flip()
        clock.tick(60)


# ---------------------------------------------------------------------------
# In-game drawing helpers (shared by single player and multiplayer)
# ---------------------------------------------------------------------------
_court_cache = {}


def _build_ground(width, height):
    """Sand strip with a light top edge and grain dots (built once and cached)."""
    ground = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        color = (int(232 - 40 * t), int(200 - 45 * t), int(140 - 40 * t))
        pygame.draw.line(ground, color, (0, y), (width, y))
    rng = random.Random(7)
    for _ in range(width * height // 40):
        x, y = rng.randrange(width), rng.randrange(height)
        shade = rng.randint(-35, 25)
        base = ground.get_at((x, y))
        ground.set_at((x, y), (max(0, min(255, base.r + shade)), max(0, min(255, base.g + shade)),
                               max(0, min(255, base.b + shade))))
    pygame.draw.line(ground, (250, 230, 180), (0, 0), (width, 0), 3)
    return ground


def draw_court(screen, net_rect, ground_y):
    """Sand ground, court line and a net with posts and mesh."""
    width, height = screen.get_size()
    key = (width, height - ground_y)
    if key not in _court_cache:
        _court_cache[key] = _build_ground(width, height - ground_y)
    screen.blit(_court_cache[key], (0, ground_y))
    pygame.draw.line(screen, (255, 255, 255), (20, ground_y + 6), (width - 20, ground_y + 6), 3)

    # Post shadow on the sand
    shadow = pygame.Surface((60, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
    screen.blit(shadow, shadow.get_rect(center=(net_rect.centerx, ground_y + 4)))

    # Mesh: a white-edged net hanging from the top of the post
    mesh_w, mesh_h = 44, net_rect.height // 2
    mesh = pygame.Surface((mesh_w, mesh_h), pygame.SRCALPHA)
    mesh.fill((0, 0, 0, 40))
    for y in range(0, mesh_h, 8):
        pygame.draw.line(mesh, (30, 30, 30, 200), (0, y), (mesh_w, y), 1)
    for x in range(0, mesh_w + 1, 8):
        pygame.draw.line(mesh, (30, 30, 30, 200), (x, 0), (x, mesh_h), 1)
    pygame.draw.rect(mesh, (255, 255, 255), (0, mesh_h - 4, mesh_w, 4))
    screen.blit(mesh, (net_rect.centerx - mesh_w // 2, net_rect.top + 4))

    # Post with highlight + white top band
    pygame.draw.rect(screen, (90, 60, 40), net_rect, border_radius=4)
    pygame.draw.rect(screen, (140, 100, 70), (net_rect.x + 3, net_rect.y, 4, net_rect.height), border_radius=2)
    pygame.draw.rect(screen, (255, 255, 255), (net_rect.centerx - 24, net_rect.top, 48, 7), border_radius=3)


def draw_shadow(screen, center_x, ground_y, width, height_above):
    """Soft ellipse under a sprite; shrinks and fades the higher it is."""
    scale = max(0.35, 1 - height_above / 350)
    w, h = int(width * scale), int(18 * scale)
    shadow = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, int(90 * scale)), shadow.get_rect())
    screen.blit(shadow, shadow.get_rect(center=(int(center_x), ground_y + 2)))


def draw_scoreboard(screen, left_name, left_score, right_name, right_score, win_score,
                    left_color, right_color, name_font, score_font, small_font):
    """Rounded scoreboard panel at the top centre."""
    width = screen.get_width()
    panel = pygame.Rect(0, 0, 420, 78)
    panel.midtop = (width // 2, 10)
    bg = pygame.Surface(panel.size, pygame.SRCALPHA)
    pygame.draw.rect(bg, (10, 20, 40, 190), bg.get_rect(), border_radius=18)
    pygame.draw.rect(bg, (255, 255, 255, 90), bg.get_rect(), 2, border_radius=18)
    screen.blit(bg, panel)

    for name, score, color, cx in ((left_name, left_score, left_color, panel.left + 95),
                                   (right_name, right_score, right_color, panel.right - 95)):
        label = name_font.render(name, True, (230, 230, 230))
        screen.blit(label, label.get_rect(center=(cx, panel.top + 18)))
        value = score_font.render(str(score), True, color)
        screen.blit(value, value.get_rect(center=(cx, panel.top + 50)))

    goal = small_font.render(f"FIRST TO {win_score}", True, (255, 255, 255))
    screen.blit(goal, goal.get_rect(center=(panel.centerx, panel.top + 18)))
    dash = score_font.render("-", True, (255, 255, 255))
    screen.blit(dash, dash.get_rect(center=(panel.centerx, panel.top + 48)))


def draw_serve_text(screen, serve_timer, serve_delay, font):
    """'READY' then 'GO!' with a pop-in scale while the ball waits to be served."""
    if serve_timer <= 0:
        return
    text = "GO!" if serve_timer < serve_delay // 3 else "READY"
    phase = (serve_delay - serve_timer) % (serve_delay // 3 * 2 or 1)
    scale = 1 + 0.25 * math.exp(-phase / 6)
    surf = font.render(text, True, (255, 255, 255))
    outline = font.render(text, True, (20, 30, 60))
    w, h = int(surf.get_width() * scale), int(surf.get_height() * scale)
    surf = pygame.transform.smoothscale(surf, (w, h))
    outline = pygame.transform.smoothscale(outline, (w, h))
    cx, cy = screen.get_width() // 2, 230
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (3, 3)):
        screen.blit(outline, outline.get_rect(center=(cx + dx, cy + dy)))
    screen.blit(surf, surf.get_rect(center=(cx, cy)))


class Particles:
    """Small sand/spark bursts for hits and points."""

    def __init__(self):
        self.items = []  # [x, y, vx, vy, life, color, size]

    def burst(self, x, y, color, count=14, speed=4, upward=False):
        for _ in range(count):
            angle = random.uniform(math.pi, 2 * math.pi) if upward else random.uniform(0, 2 * math.pi)
            v = random.uniform(1, speed)
            self.items.append([x, y, math.cos(angle) * v, math.sin(angle) * v,
                               random.randint(20, 35), color, random.randint(2, 5)])

    def update_and_draw(self, screen):
        for p in self.items[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.15
            p[4] -= 1
            if p[4] <= 0:
                self.items.remove(p)
                continue
            pygame.draw.circle(screen, p[5], (int(p[0]), int(p[1])), max(1, int(p[6] * p[4] / 35) + 1))

    def clear(self):
        self.items.clear()
