# ui.py
import pygame
import math

def draw_hud(screen, player, t):
    """
    Draws the player HUD including focus bar and health bar.
    player: should have player.focus and player.health attributes
    t: time in seconds for pulsing effects
    """

    # HUD positions
    margin = 20
    bar_width = 200
    bar_height = 16
    spacing = 6

    x = margin
    y = margin

    # ---------------- FOCUS BAR ----------------
    focus_ratio = max(0.0, min(1.0, player.focus_ratio()))
    focus_width = int(bar_width * focus_ratio)  # static width

    # subtle color pulse for life
    pulse = 0.05 * (1 + math.sin(t * 3.0))
    glow_color = (120 + int(50 * pulse), 180, 255)

    # background
    pygame.draw.rect(screen, (30, 30, 35), (x, y, bar_width, bar_height), border_radius=4)
    # foreground (glow)
    pygame.draw.rect(screen, glow_color, (x, y, focus_width, bar_height), border_radius=4)
    # inner gradient overlay for depth
    overlay = pygame.Surface((focus_width, bar_height), pygame.SRCALPHA)
    for i in range(bar_height):
        alpha = int(100 * (1 - i / bar_height))
        pygame.draw.line(overlay, (255, 255, 255, alpha), (0, i), (focus_width, i))
    screen.blit(overlay, (x, y))
    # outline
    pygame.draw.rect(screen, (80, 80, 90), (x, y, bar_width, bar_height), 2, border_radius=4)

    # ---------------- HEALTH BAR ----------------
    y += bar_height + spacing
    health_ratio = max(0.0, min(1.0, player.health / player.max_health))
    health_width = int(bar_width * health_ratio)

    # dynamic color: green → yellow → red
    if health_ratio > 0.5:
        green = 200
        red = int(255 * (1 - health_ratio) * 2)
    else:
        red = 255
        green = int(200 * health_ratio * 2)
    health_color = (red, green, 50)

    # background
    pygame.draw.rect(screen, (20, 20, 25), (x, y, bar_width, bar_height), border_radius=4)
    # foreground
    pygame.draw.rect(screen, health_color, (x, y, health_width, bar_height), border_radius=4)
    # inner gradient overlay
    overlay = pygame.Surface((health_width, bar_height), pygame.SRCALPHA)
    for i in range(bar_height):
        alpha = int(80 * (1 - i / bar_height))
        pygame.draw.line(overlay, (255, 255, 255, alpha), (0, i), (health_width, i))
    screen.blit(overlay, (x, y))
    # outline
    pygame.draw.rect(screen, (60, 60, 70), (x, y, bar_width, bar_height), 2, border_radius=4)
