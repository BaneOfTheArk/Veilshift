import pygame
import sys
import math

pygame.init()

# ---------------- SETTINGS ----------------
FPS = 60
clock = pygame.time.Clock()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.SCALED | pygame.FULLSCREEN
)

# ---------------- COLORS ----------------
AMBIENT_DARK = (18, 18, 22)
PLAYER_COLOR = (230, 230, 230)

MASK_INFO = {
    0: {"color": (200, 80, 80)},    # Physical
    1: {"color": (90, 140, 220)},   # Spectral
    2: {"color": (90, 200, 130)},   # Truth
}

# ---------------- PLAYER ----------------
CUBE_SIZE = 36
player = pygame.Rect(150, 550, CUBE_SIZE, CUBE_SIZE)

vel_x = 0
vel_y = 0
SPEED = 6
JUMP = 14
GRAVITY = 0.7
on_ground = False

# ---------------- MASK ----------------
current_mask = 0
MASK_COUNT = 3

# ---------------- LIGHT ----------------
LIGHT_RADIUS = 260
light_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

def draw_light(center):
    light_surface.fill((0, 0, 0, 255))
    for r in range(LIGHT_RADIUS, 0, -4):
        alpha = int(190 * (r / LIGHT_RADIUS))
        pygame.draw.circle(
            light_surface,
            (255, 255, 180, alpha),
            center,
            r
        )

# ---------------- PLATFORM ----------------
class Platform:
    def __init__(self, rect, masks):
        self.rect = pygame.Rect(rect)
        self.masks = masks

    def active(self):
        return current_mask in self.masks

    def draw(self):
        if not self.active():
            return
        base = MASK_INFO[current_mask]["color"]
        color = tuple(min(255, c + 20) for c in base)
        pygame.draw.rect(screen, color, self.rect, border_radius=4)

# ---------------- LEVEL ----------------
def load_level():
    return [
        Platform((0, 680, 1280, 40), [0,1,2]),

        Platform((200, 580, 200, 25), [0]),
        Platform((460, 500, 180, 25), [1]),
        Platform((700, 420, 180, 25), [2]),

        Platform((960, 340, 160, 25), [0,2]),

        Platform((320, 360, 160, 25), [1,2]),
        Platform((120, 280, 160, 25), [0]),

        Platform((0, 0, 40, 720), [0,1,2]),
        Platform((1240, 0, 40, 720), [0,1,2]),
    ]

platforms = load_level()

# ---------------- COLLISION ----------------
def move_and_collide(rect, dx, dy):
    global on_ground

    rect.x += dx
    for p in platforms:
        if p.active() and rect.colliderect(p.rect):
            if dx > 0:
                rect.right = p.rect.left
            elif dx < 0:
                rect.left = p.rect.right

    rect.y += dy
    on_ground = False
    for p in platforms:
        if p.active() and rect.colliderect(p.rect):
            if dy > 0:
                rect.bottom = p.rect.top
                on_ground = True
                return rect, 0
            elif dy < 0:
                rect.top = p.rect.bottom
                return rect, 0

    return rect, dy

# ---------------- GAME LOOP ----------------
running = True
while running:
    clock.tick(FPS)

    # -------- EVENTS --------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_1:
                current_mask = 0
            if event.key == pygame.K_2:
                current_mask = 1
            if event.key == pygame.K_3:
                current_mask = 2

            if event.key == pygame.K_SPACE and on_ground:
                vel_y = -JUMP

    # -------- INPUT --------
    keys = pygame.key.get_pressed()
    vel_x = 0
    if keys[pygame.K_a]:
        vel_x = -SPEED
    if keys[pygame.K_d]:
        vel_x = SPEED

    # -------- PHYSICS --------
    vel_y += GRAVITY
    vel_y = min(vel_y, 18)

    player, vel_y = move_and_collide(player, vel_x, vel_y)

    # -------- DRAW --------
    screen.fill(AMBIENT_DARK)

    for p in platforms:
        p.draw()

    # Player cube
    pygame.draw.rect(screen, PLAYER_COLOR, player, border_radius=6)

    # Mask indicator (small circle)
    indicator_color = MASK_INFO[current_mask]["color"]
    pygame.draw.circle(
        screen,
        indicator_color,
        (player.centerx + 8, player.centery - 8),
        6
    )

    draw_light(player.center)
    screen.blit(light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    pygame.display.flip()

pygame.quit()
sys.exit()
