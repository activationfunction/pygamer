# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pygamer is a collection of standalone educational games built with **Pygame** in Python. Each game lives in its own directory with associated assets (sounds, images).

## Running Games

Each game is a standalone script — run directly from its directory:

```bash
python captain_paws_ai/captain_paws.py
python celestial_siege_ai/celestial_siege_ai.py
python dragon_ai/dragon.py
python happy_plane_ai/happy_plane_ai.py
python pacman_ai/pacman_ai.py
python cool_effects/rotating_3d_sponge.py
```

No build system, no package manager, no test framework. Dependencies: `pygame`, and `PyOpenGL` for the cool_effects module.

## Architecture

**Each game module is independent** — no shared code between games. A typical game follows this pattern:

1. Module-level Pygame/mixer initialization and constants (`WIDTH`, `HEIGHT`, colors as RGB tuples)
2. Entity classes (Player, Dragon, Laser, etc.) with position, state, and rendering logic
3. Main game class with `update()` and `draw()` methods running in a standard game loop
4. Game objects often stored as **dictionaries** with `x`, `y`, `z`, `color`, `state` keys

**3D rendering** (captain_paws, cool_effects): Manual perspective projection with FOV-based calculations; cool_effects uses OpenGL directly.

## Code Conventions

- **snake_case** for files, functions, variables; **PascalCase** for classes; **UPPER_CASE** for constants
- Collision detection via distance calculations
- Cooldown counters for timed actions (shooting, animations)
- Depth-sorted rendering for layered visuals
- Procedural generation with `random` for entity placement and shape creation
