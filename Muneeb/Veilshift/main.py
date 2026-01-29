# main.py
import pygame
import sys
from settings import *
from player import Player
from platform import Platform, HookPlatform
from light_system import LightSystem
from ui import draw_hud
from level_handler import LevelHandler

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
clock = pygame.time.Clock()

# ---------------- PLAYER ----------------
player_img = pygame.image.load("assets/PlayerIdleNoMask.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (CUBE_SIZE, CUBE_SIZE))
player = Player((150, 550, CUBE_SIZE, CUBE_SIZE), player_img)
player.current_mask = 1
player.health = player.max_health

# ---------------- LEVEL HANDLER ----------------
level_handler = LevelHandler(WIDTH, HEIGHT)
platforms, exit_rect = level_handler.load_level(0)

# ---------------- LIGHT SYSTEM ----------------
light_system = LightSystem(WIDTH, HEIGHT)

# ---------------- TRANSITION ----------------
transition_active = False
transition_progress = 0.0  # 0.0 -> 1.0

def draw_exit_transition(surface, progress):
    """Swipe down + exit door closing + fade vision"""
    h = int(HEIGHT * progress)
    # top swipe
    pygame.draw.rect(surface, (0, 0, 0), (0, 0, WIDTH, h))
    # closing exit door from top
    pygame.draw.rect(surface, (0, 0, 0), (exit_rect.x, exit_rect.y, exit_rect.width, exit_rect.height * progress))

# ---------------- GAME LOOP ----------------
running = True
while running:
    dt = clock.tick(FPS) / 1000
    keys = pygame.key.get_pressed()
    holding_shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
    t = pygame.time.get_ticks() * 0.001  # for HUD animation

    # ---------------- EVENTS ----------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            # ---- MASK SWITCHING ----
            if event.key == pygame.K_1:
                player.current_mask = 0
            if event.key == pygame.K_2:
                player.current_mask = 1
            if event.key == pygame.K_3:
                player.current_mask = 2

            # ---- GRAPPLE / INTERACTION ----
            if event.key == pygame.K_e:
                if player.current_mask == 1:
                    if player.grapple_active:
                        player.grapple_active = False
                        player.grapple_target = None
                    else:
                        px, py = player.rect.center
                        for p_obj in platforms:
                            if isinstance(p_obj, HookPlatform):
                                hx, hy = p_obj.center
                                dx, dy = hx - px, hy - py
                                if (dx**2 + dy**2)**0.5 <= p_obj.radius + 4:
                                    player.grapple_active = True
                                    player.grapple_target = p_obj
                                    break

    # ---------------- PLAYER UPDATE ----------------
    if not transition_active:
        player.update(dt, platforms, keys, holding_shift)

    # ---------------- CHECK EXIT ----------------
    if not transition_active and level_handler.is_player_at_exit(player.rect):
        transition_active = True
        transition_progress = 0.0

    # ---------------- DRAW WORLD ----------------
    screen.fill((0, 0, 0))
    for p in platforms:
        p.draw(screen, player.current_mask)
    player.draw(screen)

    # ---------------- LIGHT ----------------
    # Fade vision cone during transition
    focus_ratio = player.focus_ratio()
    if transition_active:
        # cinematic fade: vision reduces with transition
        focus_ratio *= max(0, 1.0 - transition_progress)
    light_surface = light_system.draw_light(
        origin=player.rect.center,
        focus_ratio=focus_ratio,
        platforms=platforms,
        current_mask=player.current_mask,
        facing_angle=player.facing_angle,
        cone_radius=player.current_cone_radius
    )
    screen.blit(light_surface, (0, 0))

    # ---------------- HUD ----------------
    draw_hud(screen, player, t)

    # ---------------- TRANSITION EFFECT ----------------
    if transition_active:
        transition_speed = 0.5  # seconds, fast like the gate
        transition_progress += dt / transition_speed
        draw_exit_transition(screen, min(transition_progress, 1.0))
        if transition_progress >= 1.0:
            # load next level
            result = level_handler.next_level()
            if result:
                platforms, exit_rect = result
                player.rect.topleft = (150, 550)
                transition_active = False
            else:
                running = False  # no more levels

    pygame.display.flip()

pygame.quit()
sys.exit()
