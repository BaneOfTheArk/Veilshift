import pygame
import sys
import math

pygame.init()

# ---------------- SETTINGS ----------------
FPS = 60
clock = pygame.time.Clock()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)

debug_light = False

# ---------------- COLORS ----------------
AMBIENT_DARK = (15, 15, 20)

MASK_INFO = {
    0: {"name": "Physical", "color": (200, 80, 80)},
    1: {"name": "Spectral", "color": (90, 140, 220)},
    2: {"name": "Puzzle", "color": (90, 200, 130)},
}

# ---------------- PLAYER ----------------
CUBE_SIZE = 36
player = pygame.Rect(150, 550, CUBE_SIZE, CUBE_SIZE)

player_img = pygame.image.load("Charlotte/PlayerIdleNoMask.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (CUBE_SIZE, CUBE_SIZE))

vel_x = 0.0
vel_y = 0.0

SPEED = 6
ACCEL = 0.9
FRICTION = 0.82

JUMP = 12
GRAVITY = 0.7
on_ground = False

facing_angle = 0.0
target_angle = 0.0
jump_held = False
jump_timer = 0.0
MAX_JUMP_HOLD = 0.25  # seconds max jump hold

# ---------------- MASK ----------------
current_mask = 0

# ---------------- PULSING SPOTLIGHT ----------------
pulse_timer = 0.0
MIN_PULSE_RADIUS = 20   # smallest radius of the mini spotlight
MAX_PULSE_RADIUS = 25   # largest radius
PULSE_SPEED = 0.1       # speed of pulsing

# ---------------- LIGHT ----------------
LIGHT_RADIUS = 300
FOV_ANGLE = 90
RAY_COUNT = 50
RAY_STEP = 4

light_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
dark_surface = pygame.Surface((WIDTH, HEIGHT))

# ---------------- PLATFORM ----------------
class Platform:
    def __init__(self, rect, visible_masks=None):
        self.rect = pygame.Rect(rect)
        self.visible_masks = visible_masks  # None = always visible

    def visible(self):
        if self.visible_masks is None:
            return True
        return current_mask in self.visible_masks

    def draw(self, surface):
        if not self.visible():
            return
        base = MASK_INFO[current_mask]["color"]
        color = tuple(min(255, c + 20) for c in base)
        pygame.draw.rect(surface, color, self.rect, border_radius=4)

# ---------------- LEVEL ----------------
platforms = [
    # Floor (platform-only)
    Platform((200, 580, 200, 25), [0]),
    Platform((460, 500, 180, 25), [0]),
    Platform((700, 420, 180, 25), [0]),
    Platform((960, 340, 160, 25), [0]),
    Platform((320, 360, 160, 25), [0]),
    Platform((120, 280, 160, 25), [0]),

    # Walls (always visible)
    Platform((0, 0, 40, 720), None),
    Platform((1240, 0, 40, 720), None),
    Platform((0, 680, 1280, 40), None),
]

# ---------------- COLLISION ----------------
def move_and_collide(rect, dx, dy):
    global on_ground
    rect.x += int(dx)
    for p in platforms:
        if rect.colliderect(p.rect):
            if dx > 0:
                rect.right = p.rect.left
            elif dx < 0:
                rect.left = p.rect.right

    rect.y += int(dy)
    on_ground = False
    for p in platforms:
        if rect.colliderect(p.rect):
            if dy > 0:
                rect.bottom = p.rect.top
                on_ground = True
                return rect, 0
            elif dy < 0:
                rect.top = p.rect.bottom
                return rect, 0

    return rect, dy

# ---------------- LIGHT ----------------
def cast_ray(origin, angle):
    ox, oy = origin
    rad = math.radians(angle)
    dx = math.cos(rad)
    dy = math.sin(rad)

    last_point = (ox + dx * LIGHT_RADIUS, oy + dy * LIGHT_RADIUS)

    for i in range(0, LIGHT_RADIUS, RAY_STEP):
        px = ox + dx * i
        py = oy + dy * i
        for p in platforms:
            if p.visible() and p.rect.collidepoint(px, py):
                return (px, py)

    return last_point

def get_vision_polygon(origin):
    points = [origin]
    start = facing_angle - FOV_ANGLE / 2
    step = FOV_ANGLE / RAY_COUNT
    for i in range(RAY_COUNT + 1):
        points.append(cast_ray(origin, start + i * step))
    return points

def draw_light(origin):
    global pulse_timer
    if debug_light:
        screen.fill((255, 255, 255))
        for p in platforms:
            p.draw(screen)
        return

    dark_surface.fill(AMBIENT_DARK)
    for p in platforms:
        p.draw(dark_surface)

    light_surface.fill((0,0,0,0))

    # --- Mini pulsing spotlight around player ---
    pulse_timer += 1 / FPS
    pulse_radius = MIN_PULSE_RADIUS + (MAX_PULSE_RADIUS - MIN_PULSE_RADIUS) * (0.5 + 0.5 * math.sin(pulse_timer * PULSE_SPEED * math.pi))
    mini_spot = pygame.Surface((pulse_radius*2, pulse_radius*2), pygame.SRCALPHA)
    pygame.draw.circle(mini_spot, (255, 255, 200, 100), (pulse_radius, pulse_radius), int(pulse_radius))
    light_surface.blit(mini_spot, (origin[0]-pulse_radius, origin[1]-pulse_radius), special_flags=pygame.BLEND_RGBA_ADD)

    # --- Main cone light ---
    poly = get_vision_polygon(origin)
    pygame.draw.polygon(light_surface, (255,255,220,200), poly)

    # --- Cone gradient ---
    gradient = pygame.Surface((LIGHT_RADIUS*2, LIGHT_RADIUS*2), pygame.SRCALPHA)
    center = LIGHT_RADIUS
    for r in range(LIGHT_RADIUS, 0, -1):
        alpha = int(200 * (r / LIGHT_RADIUS))
        pygame.draw.circle(gradient, (255,255,220,alpha), (center,center), r)
    rot = pygame.transform.rotate(gradient, -facing_angle)
    rect = rot.get_rect(center=origin)
    light_surface.blit(rot, rect.topleft, special_flags=pygame.BLEND_RGBA_MULT)

    # Apply lighting
    dark_surface.blit(light_surface, (0,0), special_flags=pygame.BLEND_RGBA_MULT)

    screen.blit(dark_surface, (0,0))
    screen.blit(player_img, player.topleft)


# ---------------- GAME LOOP ----------------
running = True
while running:
    dt = clock.tick(FPS) / 1000  # seconds passed

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_1: current_mask = 0
            if event.key == pygame.K_2: current_mask = 1
            if event.key == pygame.K_3: current_mask = 2
            if event.key == pygame.K_F3: debug_light = not debug_light

    keys = pygame.key.get_pressed()

    # -------- HORIZONTAL MOVEMENT --------
    if keys[pygame.K_a]:
        vel_x -= ACCEL
    elif keys[pygame.K_d]:
        vel_x += ACCEL
    else:
        vel_x *= FRICTION
    vel_x = max(-SPEED, min(SPEED, vel_x))

    # -------- AIMING --------
    if keys[pygame.K_w]:
        target_angle = -90
        if keys[pygame.K_a]: target_angle = -135
        if keys[pygame.K_d]: target_angle = -45
    elif keys[pygame.K_s]:
        target_angle = 90
        if keys[pygame.K_a]: target_angle = 135
        if keys[pygame.K_d]: target_angle = 45
    else:
        if keys[pygame.K_a]: target_angle = 180
        if keys[pygame.K_d]: target_angle = 0

    facing_angle += (target_angle - facing_angle) * 0.25

    # -------- JUMP --------
    if keys[pygame.K_SPACE]:
        if on_ground and not jump_held:
            vel_y = -JUMP
            jump_held = True
            jump_timer = 0.0
    else:
        jump_held = False
        jump_timer = 0.0

    # If jump is being held, reduce gravity for higher jump
    if jump_held:
        jump_timer += dt
        if jump_timer < MAX_JUMP_HOLD:
            vel_y -= GRAVITY * 0.5
        else:
            jump_held = False

    vel_y += GRAVITY
    vel_y = min(vel_y, 18)

    player, vel_y = move_and_collide(player, vel_x, vel_y)

    # -------- DRAW --------
    draw_light(player.center)
    screen.blit(player_img, player.topleft)

    pygame.display.flip()

pygame.quit()
sys.exit()
