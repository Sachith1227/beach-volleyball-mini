# Beach Volleyball Mini

A 2D beach volleyball game made with Python and pygame. Play against the computer or with a friend on the same keyboard.

## Requirements

- Python 3.9 or newer
- [pygame-ce](https://pyga.me/), the maintained fork of pygame. It uses the same `import pygame`, and unlike classic pygame it has wheels for the latest Python versions.

## Setup and run

```bash
# 1. (optional) create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

# 2. install dependencies
pip install -r requirements.txt

# 3. start the game
python main.py
```

> If you already have classic `pygame` installed, uninstall it first (`pip uninstall pygame`), because the two packages share the `pygame` module name.

## How to play

When the ball touches the ground on your side, the other side scores a point. The first side to reach the target score wins. The default is 7 points, and you can change it in **Game Settings**.

| Action | Single player | Multiplayer: Player 1 | Multiplayer: Player 2 |
|---|---|---|---|
| Move left / right | ← → (or A / D) | A / D | ← → |
| Jump | ↑ (or W / Space) | W | ↑ |
| Pause | P / Esc | P / Esc | P / Esc |

The pause menu lets you resume, restart the match, or go back to the main menu.

## Game settings

Open **Game Settings** from the menu. Your choices are saved to `settings.json`.

- **CPU difficulty**: Easy, Normal or Hard. Easier levels make the CPU slower, react later, misjudge the ball more often, jump less and hit more softly
- **Points to win**: 3, 5, 7, 11 or 15
- **Court**: three beach backgrounds
- **Player skins**: six octopus colours for each player
- **Music / sound effects**: turn each on or off

## Project structure

```
beach-volleyball-mini/
├── main.py               # Entry point: python main.py
├── game/                 # Game code (Python package)
│   ├── home.py           # Home screen: Single Player / Multiplayer / Quit
│   ├── menu.py           # Mode menu: Start, Game Settings, Mute, Back, Quit
│   ├── single_player.py  # Player vs CPU
│   ├── multiplayer.py    # Two players on one keyboard
│   ├── settings.py       # Saved settings, CPU difficulty levels and the settings screen
│   ├── ui.py             # Buttons, panels, titles, pause / game-over overlay, court drawing
│   └── assets.py         # Loads images, sounds, fonts and music from assets/
├── assets/
│   ├── images/           # Backgrounds, octopus skins and balls
│   ├── fonts/
│   ├── sounds/           # Music and sound effects
│   └── video/
├── requirements.txt
└── README.md
```

To test one screen on its own, run it as a module from the project folder:

```bash
python -m game.single_player
python -m game.multiplayer
python -m game.menu
```
