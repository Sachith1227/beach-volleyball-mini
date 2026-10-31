import os
import pygame

# All asset paths are resolved relative to the project folder, so the game runs from any folder / any PC
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def asset_path(*parts):
    return os.path.join(ASSETS_DIR, *parts)


def load_image(name, size=None, crop=False, alpha=True):
    """Load an image from assets/images/. crop=True trims transparent padding so sprites sit on the ground."""
    image = pygame.image.load(asset_path("images", name))
    image = image.convert_alpha() if alpha else image.convert()
    if crop:
        image = image.subsurface(image.get_bounding_rect()).copy()
    if size:
        image = pygame.transform.smoothscale(image, size)
    return image


def load_sprite(name, width):
    """Load a cropped sprite scaled to the given width, keeping its aspect ratio."""
    image = load_image(name, crop=True)
    w, h = image.get_size()
    return pygame.transform.smoothscale(image, (width, int(h * width / w)))


class _SilentSound:
    # Used when there is no audio device, so the game still runs
    def play(self, *args, **kwargs):
        pass

    def set_volume(self, *args):
        pass


def load_sound(name, volume=1.0):
    if not pygame.mixer.get_init():
        return _SilentSound()
    try:
        sound = pygame.mixer.Sound(asset_path("sounds", name))
    except pygame.error:
        return _SilentSound()
    sound.set_volume(volume)
    return sound


def load_font(name, size):
    try:
        return pygame.font.Font(asset_path("fonts", name), size)
    except (FileNotFoundError, pygame.error):
        return pygame.font.SysFont(None, size)


_current_music = None


def play_music(name, volume=0.5, enabled=True):
    """Loop a music track. Does nothing if the same track is already playing."""
    global _current_music
    if not pygame.mixer.get_init():
        return
    if not enabled:
        stop_music()
        return
    if _current_music == name and pygame.mixer.music.get_busy():
        return
    try:
        pygame.mixer.music.load(asset_path("sounds", name))
    except pygame.error:
        return
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)
    _current_music = name


def stop_music():
    global _current_music
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
    _current_music = None
