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
    0: {"color": (200, 80, 80)},
    1: {"color": (90, 140, 220)},
    2: {"color": (90, 200, 130)},
}

# ---------------- PLAYER ----------------
CUBE_SIZE = 36
player = pygame.Rect(150, 550, CUBE_SIZE, CUBE_SIZE)

player_img = pygame.image.load(
    "Charlotte/PlayerIdleNoMask.png"
).convert_alpha()
player_img = pygame.transform.scale(player_img, (CUBE_SIZE, CUBE_SIZE))

vel_x = 0.0
vel_y = 0.0

SPEED = 6
ACCEL = 0.9
FRICTION = 0.82

JUMP = 14
GRAVITY = 0.7
on_ground = False

# Facing / vision
facing_angle = 0.0       # current angle (degrees)
target_angle = 0.0       # target angle

# Jump handling
jump_held = False

# ---------------- MASK ----------------
current_mask = 0

# ---------------- LIGHT ----------------
LIGHT_RADIUS = 280
FOV_ANGLE = 90
RAY_COUNT = 45
RAY_STEP = 4

light_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
dark_surface = pygame.Surface((WIDTH, HEIGHT))  # background darkness

# ---------------- PLATFORM ----------------
class Platform:
    def __init__(self, rect, masks):
        self.rect = pygame.Rect(rect)
        self.masks = masks

    def active(self):
        return current_mask in self.masks

    def draw(self, target_surface=None):
        if not self.active():
            return
        base = MASK_INFO[current_mask]["color"]
        color = tuple(min(255, c + 20) for c in base)
        if target_surface:
            pygame.draw.rect(target_surface, color, self.rect, border_radius=4)
        else:
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

    rect.x += int(dx)
    for p in platforms:
        if p.active() and rect.colliderect(p.rect):
            if dx > 0:
                rect.right = p.rect.left
            elif dx < 0:
                rect.left = p.rect.right

    rect.y += int(dy)
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

# ---------------- LIGHT ----------------
def cast_ray(origin, angle):
    ox, oy = origin
    rad = math.radians(angle)
    dx = math.cos(rad)
    dy = math.sin(rad)

    for i in range(0, LIGHT_RADIUS, RAY_STEP):
        px = ox + dx * i
        py = oy + dy * i
        for p in platforms:
            if p.active() and p.rect.collidepoint(px, py):
                return (px, py)
    return (ox + dx * LIGHT_RADIUS, oy + dy * LIGHT_RADIUS)

def get_vision_polygon(origin):
    points = [origin]
    start = facing_angle - FOV_ANGLE / 2
    step = FOV_ANGLE / RAY_COUNT
    for i in range(RAY_COUNT + 1):
        points.append(cast_ray(origin, start + i * step))
    return points

def draw_light(origin):
    # Fill dark surface with ambient darkness
    dark_surface.fill(AMBIENT_DARK)

    # Draw platforms for mask effect
    for p in platforms:
        p.draw(dark_surface)

    # Clear light surface
    light_surface.fill((0,0,0,0))

    # Draw gradient spotlight polygon
    polygon = get_vision_polygon(origin)
    # Draw solid polygon first
    pygame.draw.polygon(light_surface, (255,255,180,180), polygon)

    # Apply radial gradient fade along the cone
    # Create radial mask
    gradient = pygame.Surface((LIGHT_RADIUS*2, LIGHT_RADIUS*2), pygame.SRCALPHA)
    center = LIGHT_RADIUS
    for r in range(LIGHT_RADIUS, 0, -1):
        alpha = int(180 * (r / LIGHT_RADIUS))
        pygame.draw.circle(gradient, (255,255,180,alpha), (center,center), r)
    gradient_rot = pygame.transform.rotate(gradient, -facing_angle)
    gradient_rect = gradient_rot.get_rect(center=origin)

    light_surface.blit(gradient_rot, gradient_rect.topleft, special_flags=pygame.BLEND_RGBA_MULT)

    # Multiply light onto dark_surface
    dark_surface.blit(light_surface, (0,0), special_flags=pygame.BLEND_RGBA_MULT)

    # Draw final combined surface
    screen.blit(dark_surface, (0,0))

# ---------------- GAME LOOP ----------------
running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            # ESC to quit
            if event.key == pygame.K_ESCAPE:
                running = False
            # Mask switching
            if event.key == pygame.K_1:
                current_mask = 0
            if event.key == pygame.K_2:
                current_mask = 1
            if event.key == pygame.K_3:
                current_mask = 2

    keys = pygame.key.get_pressed()

    # -------- MOVEMENT --------
    if keys[pygame.K_a]:
        vel_x -= ACCEL
    elif keys[pygame.K_d]:
        vel_x += ACCEL
    else:
        vel_x *= FRICTION
    vel_x = max(-SPEED, min(SPEED, vel_x))

    # -------- AIMING --------
    if keys[pygame.K_w]:
        if keys[pygame.K_a]:
            target_angle = -135
        elif keys[pygame.K_d]:
            target_angle = -45
        else:
            target_angle = -90
    elif keys[pygame.K_s]:
        if keys[pygame.K_a]:
            target_angle = 135
        elif keys[pygame.K_d]:
            target_angle = 45
        else:
            target_angle = 90
    else:
        if keys[pygame.K_a]:
            target_angle = 180
        elif keys[pygame.K_d]:
            target_angle = 0

    facing_angle += (target_angle - facing_angle) * 0.25

    # -------- JUMP --------
    if keys[pygame.K_SPACE]:
        if on_ground and not jump_held:
            vel_y = -JUMP
            jump_held = True
    else:
        jump_held = False

    # -------- PHYSICS --------
    vel_y += GRAVITY
    vel_y = min(vel_y, 18)

    player, vel_y = move_and_collide(player, vel_x, vel_y)

    # -------- DRAW --------
    draw_light(player.center)
    screen.blit(player_img, player.topleft)

    pygame.display.flip()

pygame.quit()
sys.exit()
