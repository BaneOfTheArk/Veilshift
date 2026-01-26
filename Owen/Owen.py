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

MASK_INFO = {
    0: {"color": (200, 80, 80)},    # Physical
    1: {"color": (90, 140, 220)},   # Spectral
    2: {"color": (90, 200, 130)},   # Truth
}

# ---------------- PLAYER ----------------
CUBE_SIZE = 36
player = pygame.Rect(150, 550, CUBE_SIZE, CUBE_SIZE)

# Load player image
player_img = pygame.image.load("Charlotte/PlayerIdleNoMask.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (CUBE_SIZE, CUBE_SIZE))

vel_x = 0
vel_y = 0
SPEED = 6
JUMP = 14
GRAVITY = 0.7
on_ground = False

# Track facing
facing_right = True

# ---------------- MASK ----------------
current_mask = 0
MASK_COUNT = 3

# ---------------- LIGHT ----------------
LIGHT_RADIUS = 280  # slightly longer for edge visibility
FOV_ANGLE = 90  # vision cone in degrees
light_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

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

# ---------------- LIGHT FUNCTIONS ----------------
def cast_ray(origin, angle, blocks, max_distance):
    x, y = origin
    radians = math.radians(angle)
    dx = math.cos(radians)
    dy = math.sin(radians)

    for i in range(max_distance):
        px = x + dx * i
        py = y + dy * i
        for p in blocks:
            if p.active() and p.rect.collidepoint(px, py):
                return (px, py)
    return (x + dx * max_distance, y + dy * max_distance)

def get_vision_polygon(origin, facing_right, blocks):
    points = [origin]
    start_angle = -FOV_ANGLE / 2 if facing_right else 180 - FOV_ANGLE / 2
    for i in range(int(FOV_ANGLE)+1):
        angle = start_angle + i
        end_point = cast_ray(origin, angle, blocks, LIGHT_RADIUS)
        points.append(end_point)
    return points

def draw_light(origin, facing_right):
    # Fill darkness
    light_surface.fill((0, 0, 0, 255))

    # Vision polygon
    vision_poly = get_vision_polygon(origin, facing_right, platforms)

    # Draw polygon of light
    pygame.draw.polygon(light_surface, (255, 255, 180, 200), vision_poly)

    # Blit light on screen (player drawn on top)
    screen.blit(light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

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
        facing_right = False
    if keys[pygame.K_d]:
        vel_x = SPEED
        facing_right = True

    # -------- PHYSICS --------
    vel_y += GRAVITY
    vel_y = min(vel_y, 18)

    player, vel_y = move_and_collide(player, vel_x, vel_y)

    # -------- DRAW --------
    screen.fill(AMBIENT_DARK)

    # Draw platforms normally
    for p in platforms:
        p.draw()

    # Draw realistic vision cone
    draw_light(player.center, facing_right)

    # Draw player ON TOP
    screen.blit(player_img, player.topleft)

    pygame.display.flip()

pygame.quit()
sys.exit()
