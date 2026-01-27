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
    "Q:\\Global game Jam\\Veilshift\\Charlotte\\PlayerSprites\\PlayerIdleNoMask.png"
).convert_alpha()
# Slightly bigger sprite
player_img = pygame.transform.scale(
    player_img,
    (int(CUBE_SIZE * 1.1), int(CUBE_SIZE * 1.1))
)

vel_x = 0
vel_y = 0
SPEED = 6
JUMP = 14
GRAVITY = 0.7
on_ground = False
facing_right = True
facing_angle = 0.0
target_angle = 0.0
jump_held = False

# Pulsing mini spotlight
pulse_timer = 0.0
MIN_PULSE_RADIUS = 20
MAX_PULSE_RADIUS = 20
PULSE_SPEED = 0.0

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
    def __init__(self, rect, masks=None):
        self.rect = pygame.Rect(rect)
        self.masks = masks  # None = always visible

    def active(self):
        if self.masks is None:
            return True
        return current_mask in self.masks

    def draw(self):
        if not self.active():
            return
        base = MASK_INFO[current_mask]["color"]
        color = tuple(min(255, c + 20) for c in base)
        pygame.draw.rect(screen, color, self.rect, border_radius=4)

# ---------------- PUSHABLE BOX ----------------
class PushableBox:
    def __init__(self, x, y):
        # Visual size (BIG box)
        self.width = 140
        self.height = 100

        # Physics hitbox (tiny core)
        self.hit_width = 20
        self.hit_height = 20
        self.hit_rect = pygame.Rect(0, 0, self.hit_width, self.hit_height)
        self.hit_rect.midbottom = (x + self.width // 2, y + self.height)

        # Visual rect (follows hitbox)
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.rect.midbottom = self.hit_rect.midbottom

        self.vel_y = 0

        # Load box image
        self.image = pygame.image.load(
            "Q:\\Global game Jam\\Veilshift\\Charlotte\\BackgroundAssets\\BigBoxLevel1 .png"
        ).convert_alpha()
        # Slightly bigger than visual rect if needed
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def update(self):
        # Gravity
        self.vel_y += GRAVITY
        self.vel_y = min(self.vel_y, 18)

        # Vertical physics only for hitbox
        self.hit_rect, self.vel_y = move_and_collide(self.hit_rect, 0, self.vel_y)

        # Sync visual rect with hitbox
        self.rect.midbottom = self.hit_rect.midbottom

    def draw(self):
        # Center image over hitbox
        img_rect = self.image.get_rect(center=self.hit_rect.center)
        screen.blit(self.image, img_rect.topleft)

# ---------------- LEVEL ----------------
def load_level():
    return [
        Platform((0, 680, 1280, 40), None),     # Floor always visible
        Platform((0, 0, 40, 720), None),        # Left wall always visible
        Platform((1240, 0, 40, 720), None),     # Right wall always visible
        Platform((200, 580, 200, 25), [0]),     # Mask-specific platforms
        Platform((460, 500, 180, 25), [0]),
        Platform((700, 420, 180, 25), [0]),
        Platform((960, 340, 160, 25), [0]),
        Platform((320, 360, 160, 25), [0]),
        Platform((120, 280, 160, 25), [0]),
    ]

platforms = load_level()

# ---------------- COLLISION ----------------
def move_and_collide(rect, dx, dy):
    global on_ground
    rect.x += dx
    for p in platforms:
        if rect.colliderect(p.rect):
            if dx > 0:
                rect.right = p.rect.left
            elif dx < 0:
                rect.left = p.rect.right
    rect.y += dy
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
        points.append(cast_ray_enemy(origin, angle))
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
    global pulse_timer
    if DEBUG:
        return

    # --- Prepare darkness surface ---
    light_surface.fill((0, 0, 0, 255))

    # --- Mini pulsing spotlight around player ---
    pulse_timer += 1 / FPS
    pulse_radius = MIN_PULSE_RADIUS + (MAX_PULSE_RADIUS - MIN_PULSE_RADIUS) * (
        0.5 + 0.5 * math.sin(pulse_timer * PULSE_SPEED * math.pi)
    )
    mini_spot = pygame.Surface((pulse_radius*2, pulse_radius*2), pygame.SRCALPHA)
    pygame.draw.circle(mini_spot, (255, 255, 200, 100), (pulse_radius, pulse_radius), int(pulse_radius))
    light_surface.blit(mini_spot, (origin[0]-pulse_radius, origin[1]-pulse_radius), special_flags=pygame.BLEND_RGBA_ADD)

    # --- Main cone light ---
    poly = get_vision_polygon(origin)
    pygame.draw.polygon(light_surface, (255, 255, 180, 200), poly)

    # --- Cone gradient ---
    gradient = pygame.Surface((LIGHT_RADIUS*2, LIGHT_RADIUS*2), pygame.SRCALPHA)
    center = LIGHT_RADIUS
    for r in range(LIGHT_RADIUS, 0, -1):
        alpha = int(200 * (r / LIGHT_RADIUS))
        pygame.draw.circle(gradient, (255, 255, 220, alpha), (center, center), r)
    rot = pygame.transform.rotate(gradient, -facing_angle)
    rect = rot.get_rect(center=origin)
    light_surface.blit(rot, rect.topleft, special_flags=pygame.BLEND_RGBA_MULT)

    # --- Draw everything to screen ---
    screen.fill(AMBIENT_DARK)  # Base ambient darkness

    # Draw platforms
    for p in platforms:
        if p.active():
            p.draw()

    # Draw box ALWAYS
    box.draw()

    # Apply light surface on top
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
box = PushableBox(400, 500)  # starting position

# -------- GAME LOOP --------
running = True
while running:
    clock.tick(FPS)

    # -------- AIMING / CONE ROTATION --------
    keys = pygame.key.get_pressed()

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

    # -------- INPUT / MOVEMENT --------
    vel_x = (-SPEED if keys[pygame.K_a] else SPEED if keys[pygame.K_d] else 0)
    if vel_x != 0:
        facing_right = vel_x > 0

    # -------- PHYSICS --------
    vel_y = min(vel_y + GRAVITY, 18)
    player, vel_y = move_and_collide(player, vel_x, vel_y)

    # -------- JUMP --------
    if keys[pygame.K_SPACE]:
        if on_ground and not jump_held:
            vel_y = -JUMP
            jump_held = True
    else:
        jump_held = False

    # -------- PUSHABLE BOX UPDATE --------
    box.update()

    # -------- PLAYER ↔ BOX INTERACTION --------
    if player.colliderect(box.hit_rect):

        # --- HORIZONTAL PUSH ---
        if vel_x > 0:
            box.hit_rect.x += vel_x
            box.rect.midbottom = box.hit_rect.midbottom
            player.right = box.hit_rect.left
        elif vel_x < 0:
            box.hit_rect.x += vel_x
            box.rect.midbottom = box.hit_rect.midbottom
            player.left = box.hit_rect.right

        # --- STANDING ON BOX ---
        if vel_y > 0 and player.bottom <= box.hit_rect.top + 10:
            player.bottom = box.hit_rect.top
            vel_y = 0
            on_ground = True

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

    # -------- ENEMY UPDATE --------
    enemy.update(player)

    # -------- DRAW --------
    screen.fill(AMBIENT_DARK)

    # Draw platforms
    for p in platforms:
        p.draw()

    # Draw pushable box (always visible)
    box.draw()

    # Debug visuals
    if DEBUG:
        enemy_vision = get_enemy_vision_polygon(enemy)
        color = ENEMY_DEBUG_COLOR_ALERT if enemy.alerted else ENEMY_DEBUG_COLOR_IDLE
        pygame.draw.polygon(screen, color, enemy_vision, width=2)
        # Draw hitbox
        pygame.draw.rect(screen, (255, 0, 0), box.hit_rect, 1)

    # Draw light
    vision_poly = get_vision_polygon(player.center)
    draw_light(player.center)

    # Draw enemies
    enemy.draw_body(vision_poly)
    enemy.draw_eyes()

    # Draw player on top
    img_rect = player_img.get_rect(center=player.center)
    screen.blit(player_img, img_rect.topleft)

    pygame.display.flip()

pygame.quit()
sys.exit()
