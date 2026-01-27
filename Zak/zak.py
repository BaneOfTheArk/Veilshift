import pygame
import sys
import math

pygame.init()

# ---------------- SETTINGS ----------------
FPS = 60
clock = pygame.time.Clock()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)

DEBUG = False

# ---------------- COLORS ----------------
AMBIENT_DARK = (18, 18, 22)

MASK_INFO = {
    0: {"color": (90, 140, 220)},   # Physical
    1: {"color": (200, 80, 80)},    # Spectral
    2: {"color": (90, 200, 130)},   # Puzzle
}

# ---------------- PLAYER ----------------
CUBE_SIZE = 36
player = pygame.Rect(150, 550, CUBE_SIZE, CUBE_SIZE)

player_img = pygame.image.load(
    "Q:\Veilshift(UPDATED)\Veilshift\Charlotte\PlayerIdleNoMask.png"
).convert_alpha()
player_img = pygame.transform.scale(player_img, (CUBE_SIZE, CUBE_SIZE))

vel_x = 0
vel_y = 0
SPEED = 6
JUMP = 14
GRAVITY = 0.7
on_ground = False
facing_right = True
facing_angle = 0.0
target_angle = 0.0

# ---------------- MASK ----------------
current_mask = 0

# ---------------- ENEMY CONSTANTS ----------------
ENEMY_SPEED = 2
ENEMY_CHASE_SPEED = 4
ENEMY_GRAVITY = 0.7
ENEMY_MAX_FALL = 18
ENEMY_VISION_RADIUS = 235
ENEMY_FOV = 160

EYE_MAX_DISTANCE = 400
EYE_MIN_ALPHA = 40
EYE_MAX_ALPHA = 255

ENEMY_DEBUG_COLOR_IDLE = (255, 255, 0, 60)   # yellow
ENEMY_DEBUG_COLOR_ALERT = (255, 80, 80, 80) # red

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
        Platform((0, 680, 1280, 40), [0, 1, 2]),
        Platform((200, 580, 200, 25), [0]),
        Platform((460, 500, 180, 25), [0]),
        Platform((700, 420, 180, 25), [0]),
        Platform((960, 340, 160, 25), [0]),
        Platform((320, 360, 160, 25), [0]),
        Platform((120, 280, 160, 25), [0]),
        Platform((0, 0, 40, 720), [0]),
        Platform((1240, 0, 40, 720), [0]),
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

# ---------------- LIGHT ----------------
LIGHT_RADIUS = 280
FOV_ANGLE = 90
light_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

RAY_COUNT = 50
RAY_STEP = 4

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

def cast_ray_enemy(origin, angle):
    ox, oy = origin
    rad = math.radians(angle)
    dx = math.cos(rad)
    dy = math.sin(rad)

    for i in range(0, ENEMY_VISION_RADIUS, RAY_STEP):
        px = ox + dx * i
        py = oy + dy * i

        for p in platforms:
            if p.active() and p.rect.collidepoint(px, py):
                return (px, py)

    return (ox + dx * ENEMY_VISION_RADIUS, oy + dy * ENEMY_VISION_RADIUS)

def get_vision_polygon(origin):
    points = [origin]
    start = facing_angle - FOV_ANGLE / 2
    step = FOV_ANGLE / RAY_COUNT
    for i in range(RAY_COUNT + 1):
        points.append(cast_ray(origin, start + i * step))
    return points

def get_enemy_vision_polygon(enemy):
    origin = enemy.rect.center
    points = [origin]

    start_angle = -ENEMY_FOV / 2 if enemy.facing_right else 180 - ENEMY_FOV / 2

    for i in range(int(ENEMY_FOV) + 1):
        angle = start_angle + i
        end_point = cast_ray_enemy(origin, angle)
        points.append(end_point)

    return points

def point_in_polygon(point, poly):
    x, y = point
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[i - 1]
        if ((y1 > y) != (y2 > y)) and \
           (x < (x2 - x1) * (y - y1) / (y2 - y1 + 0.0001) + x1):
            inside = not inside
    return inside

def draw_light(origin):
    if DEBUG:
        return
    light_surface.fill((0, 0, 0, 255))
    poly = get_vision_polygon(origin)
    pygame.draw.polygon(light_surface, (255, 255, 180, 200), poly)
    screen.blit(light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

# ---------------- ENEMY ----------------
class Enemy:
    def __init__(self, x, y, patrol_width=200):
        self.rect = pygame.Rect(x, y, CUBE_SIZE, CUBE_SIZE)
        self.start_x = x
        self.patrol_width = patrol_width
        self.vel_x = ENEMY_SPEED
        self.vel_y = 0
        self.facing_right = True
        self.alerted = False

    def can_see_player(self, pos):
        dx, dy = pos[0] - self.rect.centerx, pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > ENEMY_VISION_RADIUS:
            return False
        angle = math.degrees(math.atan2(dy, dx))
        facing = 0 if self.facing_right else 180
        delta = (angle - facing + 180) % 360 - 180
        return abs(delta) < ENEMY_FOV / 2

    def patrol(self):
        self.vel_x = ENEMY_SPEED if self.facing_right else -ENEMY_SPEED
        if self.rect.x > self.start_x + self.patrol_width:
            self.facing_right = False
        elif self.rect.x < self.start_x:
            self.facing_right = True

    def chase(self):
        self.vel_x = ENEMY_CHASE_SPEED if self.facing_right else -ENEMY_CHASE_SPEED

    def update(self, player):
        self.alerted = self.can_see_player(player.center)
        self.facing_right = player.centerx > self.rect.centerx if self.alerted else self.facing_right
        self.chase() if self.alerted else self.patrol()

        self.vel_y = min(self.vel_y + ENEMY_GRAVITY, ENEMY_MAX_FALL)
        self.rect, self.vel_y = move_and_collide(self.rect, self.vel_x, self.vel_y)

    def draw_body(self, vision_poly):
        if current_mask == 1 and point_in_polygon(self.rect.center, vision_poly):
            screen.blit(player_img, self.rect.topleft)

    def draw_eyes(self):
        if current_mask == 1:
            return
        dx = player.centerx - self.rect.centerx
        dy = player.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist >= EYE_MAX_DISTANCE:
            return
        alpha = max(EYE_MIN_ALPHA, int(EYE_MAX_ALPHA * (1 - dist / EYE_MAX_DISTANCE)))
        surf = pygame.Surface((20, 10), pygame.SRCALPHA)
        for i in range(2):
            pygame.draw.circle(surf, (255, 255, 255, alpha), (5 + i * 10, 5), 3)
        screen.blit(surf, (self.rect.x + (10 if self.facing_right else 4), self.rect.y + 10))

enemy = Enemy(600, 384)

# -------- GAME LOOP --------
running = True
while running:
    clock.tick(FPS)

    # -------- EVENTS --------
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            if e.key == pygame.K_1: current_mask = 0
            if e.key == pygame.K_2: current_mask = 1
            if e.key == pygame.K_3: current_mask = 2
            if e.key == pygame.K_F3: DEBUG = not DEBUG
            if e.key == pygame.K_SPACE and on_ground:
                vel_y = -JUMP

    # -------- INPUT / MOVEMENT --------
    keys = pygame.key.get_pressed()
    vel_x = (-SPEED if keys[pygame.K_a] else SPEED if keys[pygame.K_d] else 0)
    if vel_x != 0:
        facing_right = vel_x > 0

    # -------- AIMING / CONE ROTATION --------
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

    # -------- PHYSICS --------
    vel_y = min(vel_y + GRAVITY, 18)
    player, vel_y = move_and_collide(player, vel_x, vel_y)
    enemy.update(player)

    # -------- DRAW --------
    screen.fill(AMBIENT_DARK)

    # Draw platforms
    for p in platforms:
        p.draw()

    # Draw enemy vision outline in debug mode
    if DEBUG:
        enemy_vision = get_enemy_vision_polygon(enemy)
        color = ENEMY_DEBUG_COLOR_ALERT if enemy.alerted else ENEMY_DEBUG_COLOR_IDLE
        pygame.draw.polygon(screen, color, enemy_vision, width=2)


    vision_poly = get_vision_polygon(player.center)
    draw_light(player.center)

    # Draw enemies
    enemy.draw_body(vision_poly)
    enemy.draw_eyes()

    # Draw player on top
    screen.blit(player_img, player.topleft)

    pygame.display.flip()

pygame.quit()
sys.exit()