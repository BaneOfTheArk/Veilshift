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

MASKLESS = -1
MASKLESS_COLOR = (255, 255, 255)

box_spawned = False
boxes = []

trolleys = []
trolley_spawned = False



def get_mask_color():
    if current_mask == MASKLESS:
        return MASKLESS_COLOR
    return MASK_INFO[current_mask]["color"]


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

# ---------------- PLAYER SPRITES ----------------

PLAYER_SPRITES = {
    MASKLESS: {
        "idle": pygame.transform.scale(
            pygame.image.load(
                "Q:\Global game Jam\Veilshift\Charlotte\PlayerSprites\PlayerIdleNoMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
        "run": pygame.transform.scale(
            pygame.image.load(
                "Q:\Global game Jam\Veilshift\Charlotte\PlayerSprites\PlayerRunningNoMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
    },

    0: {  # Spectral mask
        "idle": pygame.transform.scale(
            pygame.image.load(
                "Q:\Global game Jam\Veilshift\Charlotte\PlayerSprites\PlayerIdlePlatformMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
        "run": pygame.transform.scale(
            pygame.image.load(
                "Q:\Global game Jam\Veilshift\Charlotte\PlayerSprites\PlayerRunningPlatformMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
    },

    1: {  # Physical mask
        "idle": pygame.transform.scale(
            pygame.image.load(
                "Q:\Global game Jam\Veilshift\Charlotte\PlayerSprites\PlayerIdleAttackMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
        "run": pygame.transform.scale(
            pygame.image.load(
                "Q:\Global game Jam\Veilshift\Charlotte\PlayerSprites\PlayerRunningAttackMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
    },

    2: {  # Puzzle mask
        "idle": pygame.transform.scale(
            pygame.image.load(
                "Q:\Global game Jam\Veilshift\Charlotte\PlayerSprites\PlayerIdlePuzzleMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
        "run": pygame.transform.scale(
            pygame.image.load(
                "Q:\Global game Jam\Veilshift\Charlotte\PlayerSprites\PlayerRunningPuzzleMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
    },
}

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
last_safe_pos = player.topleft
was_on_box_or_trolley = False


# Pulsing mini spotlight
pulse_timer = 0.0
MIN_PULSE_RADIUS = 20
MAX_PULSE_RADIUS = 20
PULSE_SPEED = 0.0

# Enemy image
enemy1_img = pygame.image.load("Q:\Global game Jam\Veilshift\Charlotte\ShadowMonster.png"
).convert_alpha()
enemy1_img = pygame.transform.scale(enemy1_img, (CUBE_SIZE, CUBE_SIZE))

# ---------------- MASK ----------------
current_mask = MASKLESS

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
        if current_mask == MASKLESS:
            return self.masks is None  # only walls & floor
        if self.masks is None:
            return True
        return current_mask in self.masks

    def draw(self):
        if not self.active():
            return
        base = get_mask_color()
        color = tuple(min(255, c + 20) for c in base)
        pygame.draw.rect(screen, color, self.rect, border_radius=4)




class Box:
    def __init__(self, x, y, width, height, image_path=None, hit_offset_x=46, hit_offset_y=50, hitbox_size=35):
        self.rect = pygame.Rect(x, y, width, height)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.saved_pos = self.rect.topleft
        self.active_in_game = True  

        if image_path:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (width, height))
        else:
            self.image = None

        self.hit_offset_x = hit_offset_x
        self.hit_offset_y = hit_offset_y
        self.hitbox_size = hitbox_size

        self.hit_rect = pygame.Rect(
            self.rect.x + self.hit_offset_x,
            self.rect.y + self.hit_offset_y,
            self.hitbox_size,
            self.hitbox_size
        )

    def apply_gravity(self, gravity=0.7, max_fall=18):
        if not self.active_in_game:
            return
        self.vel_y = min(self.vel_y + gravity, max_fall)

    def move_and_collide(self, platforms):
        if not self.active_in_game:
            return

        # Horizontal collisions
        self.hit_rect.x += self.vel_x
        for p in platforms:
            if self.hit_rect.colliderect(p.rect):
                if self.vel_x > 0:
                    self.hit_rect.right = p.rect.left
                    self.vel_x = 0
                elif self.vel_x < 0:
                    self.hit_rect.left = p.rect.right
                    self.vel_x = 0

        # Vertical collisions
        self.hit_rect.y += self.vel_y
        self.on_ground = False
        for p in platforms:
            if self.hit_rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.hit_rect.bottom = p.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.hit_rect.top = p.rect.bottom
                    self.vel_y = 0

        self.rect.topleft = (self.hit_rect.x - self.hit_offset_x,
                             self.hit_rect.y - self.hit_offset_y)
        self.saved_pos = self.rect.topleft

    def update(self, platforms):
        # Only active in puzzle mask
        if current_mask == 2:
            self.active_in_game = True
        else:
            # Save last position, disable collisions
            if self.active_in_game:
                self.saved_pos = self.rect.topleft
            self.active_in_game = False
            return  # skip update if not puzzle mask

        self.apply_gravity()
        self.move_and_collide(platforms)
        self.vel_x *= 0.8
        if abs(self.vel_x) < 0.1:
            self.vel_x = 0


    def draw(self, surface):
        if not self.active_in_game:
            return
        if self.image:
            surface.blit(self.image, self.rect.topleft)
        else:
            pygame.draw.rect(surface, (200, 100, 50), self.rect)
        if DEBUG:
            pygame.draw.rect(surface, (255, 0, 0), self.hit_rect, 2)


class Trolley(Box):
    def __init__(self, x, y, width, height, image_path, hit_shrink_x=0, hit_shrink_y=25):
        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            image_path=image_path
        )

        self.hit_offset_x += hit_shrink_x // 2
        self.hit_offset_y += hit_shrink_y // 1
        self.hitbox_size = self.hitbox_size - hit_shrink_x
        self.hit_rect = pygame.Rect(
            self.rect.x + self.hit_offset_x,
            self.rect.y + self.hit_offset_y,
            self.hitbox_size,
            self.hitbox_size - hit_shrink_y
        )

    def blocked_horizontally(self, platforms, direction):
        if not self.active_in_game:
            return False
        test = self.hit_rect.copy()
        test.x += direction
        for p in platforms:
            if test.colliderect(p.rect):
                return True
        return False













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
        # Always check collision, even if platform is not active
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
    global pulse_timer
    if DEBUG:
        return

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

    # --- Draw light on screen ---
    screen.fill(AMBIENT_DARK)  # Base ambient dark
    for p in platforms:
        if p.active():  # only draw visible platforms
            p.draw()
    screen.blit(light_surface, (0,0), special_flags=pygame.BLEND_RGBA_MULT)

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
        if current_mask == 3:
            return
        if current_mask == 1 and point_in_polygon(self.rect.center, vision_poly):
            img = enemy1_img
            if not self.facing_right:
                img = pygame.transform.flip(enemy1_img, True, False)
            screen.blit(img, self.rect.topleft)

    def draw_eyes(self):
        if current_mask in (1,3):
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



def player_on_real_ground(player_rect, platforms):
    for p in platforms:
        # must be standing ON TOP, not inside
        if (
            player_rect.bottom == p.rect.top and
            player_rect.right > p.rect.left and
            player_rect.left < p.rect.right
        ):
            return True
    return False





















# --- Cone check helper ---
def point_in_cone(point, cone_origin, cone_angle, cone_length=250, cone_width=60):
    dx = point[0] - cone_origin[0]
    dy = point[1] - cone_origin[1]
    distance = math.hypot(dx, dy)
    if distance > cone_length:
        return False

    angle_to_point = math.degrees(math.atan2(dy, dx))

    # Normalize angles between -180 and 180
    def normalize_angle(a):
        while a <= -180: a += 360
        while a > 180: a -= 360
        return a

    diff = normalize_angle(angle_to_point - cone_angle)
    return abs(diff) <= cone_width / 2


# --- Object in light check ---
def is_in_light(obj_rect, player_center, player_angle):
    return point_in_cone(obj_rect.center, player_center, player_angle)































# -------- GAME LOOP --------
running = True
last_safe_pos = player.topleft
boxes = []
trolleys = []
box_spawned = False
trolley_spawned = False

player_on_box = None
player_on_trolley = None

# --- Cone check helper ---
import math

def point_in_cone(point, cone_origin, cone_angle, cone_length=250, cone_width=60):
    dx = point[0] - cone_origin[0]
    dy = point[1] - cone_origin[1]
    distance = math.hypot(dx, dy)
    if distance > cone_length:
        return False

    angle_to_point = math.degrees(math.atan2(dy, dx))

    # Normalize angles between -180 and 180
    def normalize_angle(a):
        while a <= -180: a += 360
        while a > 180: a -= 360
        return a

    diff = normalize_angle(angle_to_point - cone_angle)
    return abs(diff) <= cone_width / 2

def is_in_light(obj_rect, player_center, player_angle):
    return point_in_cone(obj_rect.center, player_center, player_angle)

# -------- GAME LOOP START --------
while running:
    
    clock.tick(FPS)
    keys = pygame.key.get_pressed()

    # --- AIMING / CONE ROTATION ---
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

    # --- EVENTS ---
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE: running = False
            if e.key == pygame.K_1: current_mask = MASKLESS
            if e.key == pygame.K_2: current_mask = 0
            if e.key == pygame.K_3: current_mask = 1
            if e.key == pygame.K_4: current_mask = 2
            if e.key == pygame.K_F3: DEBUG = not DEBUG

    # --- INPUT / MOVEMENT ---
    vel_x = (-SPEED if keys[pygame.K_a] else SPEED if keys[pygame.K_d] else 0)
    if vel_x != 0: facing_right = vel_x > 0

    state = "run" if vel_x != 0 else "idle"
    sprites = PLAYER_SPRITES.get(current_mask, PLAYER_SPRITES[MASKLESS])
    current_player_img = sprites[state]

    # --- PLAYER PHYSICS ---
    vel_y = min(vel_y + GRAVITY, 18)
    player, vel_y = move_and_collide(player, vel_x, vel_y)

    # --- PLAYER COLLISION WITH BOXES AND TROLLEYS (ONLY PUZZLE MASK) ---
    player_on_box = None
    player_on_trolley = None

    if current_mask == 2:  # Only collide in puzzle mask
        for box in boxes:
            # Horizontal push
            if player.colliderect(box.hit_rect) and vel_x != 0:
                if vel_x > 0: player.right = box.hit_rect.left
                elif vel_x < 0: player.left = box.hit_rect.right
                box.vel_x += vel_x * 0.35

            # Vertical collision (standing on box)
            if vel_y >= 0 and player.bottom <= box.hit_rect.bottom:
                if player.colliderect(box.hit_rect):
                    player.bottom = box.hit_rect.top
                    vel_y = 0
                    on_ground = True
                    player_on_box = box

        for trolley in trolleys:
            # Horizontal push
            if player.colliderect(trolley.hit_rect) and vel_x != 0:
                if vel_x > 0: player.right = trolley.hit_rect.left
                elif vel_x < 0: player.left = trolley.hit_rect.right
                trolley.vel_x += vel_x * 0.35

            # Vertical collision (standing on trolley)
            if vel_y >= 0 and player.bottom <= trolley.hit_rect.bottom:
                if player.colliderect(trolley.hit_rect):
                    player.bottom = trolley.hit_rect.top
                    vel_y = 0
                    on_ground = True
                    player_on_trolley = trolley

    # --- BOX + TROLLEY MERGE INTO BOX WITH WHEELS ---
    if current_mask == 2:
        new_boxes = []
        new_trolleys = []
        for box in boxes:
            merged = False
            for trolley in trolleys:
                if box.hit_rect.colliderect(trolley.hit_rect):
                    box_with_wheels_image = "Q:/Global game Jam/Veilshift/Charlotte/BackgroundAssets/BoxWithWheels.png"
                    merged_box = Box(box.hit_rect.x - box.hit_offset_x,
                                     box.hit_rect.y - box.hit_offset_y,
                                     box.rect.width,
                                     box.rect.height,
                                     box_with_wheels_image)
                    new_boxes.append(merged_box)
                    merged = True
                    break
            if not merged:
                new_boxes.append(box)
        for trolley in trolleys:
            if not any(box.hit_rect.colliderect(trolley.hit_rect) for box in boxes):
                new_trolleys.append(trolley)
        boxes = new_boxes
        trolleys = new_trolleys

    # --- UPDATE LAST SAFE POSITION ---
    inside_screen = 0 <= player.left <= WIDTH - player.width and 0 <= player.top <= HEIGHT - player.height
    on_platform_top = any(player.bottom == p.rect.top and player.right > p.rect.left and player.left < p.rect.right for p in platforms)

    if inside_screen and on_platform_top:
        last_safe_pos = player.topleft

    # --- TELEPORT BACK IF OUT OF SCREEN OR INSIDE WALL ---
    colliding_with_wall = any(player.colliderect(p.rect) for p in platforms)
    if player.left < 0 or player.right > WIDTH or player.top < 0 or player.bottom > HEIGHT or colliding_with_wall:
        if last_safe_pos:
            player.topleft = last_safe_pos
            vel_x = 0
            vel_y = 0

    # --- JUMP ---
    if keys[pygame.K_SPACE] and on_ground and not jump_held:
        vel_y = -JUMP
        jump_held = True
    else:
        jump_held = False

    # --- ENEMY UPDATE ---
    enemy.update(player)

    # --- BOX SPAWN ---
    if not box_spawned:
        box_image_path = "Q:/Global game Jam/Veilshift/Charlotte/BackgroundAssets/BigBoxLevel1 .png"
        boxes.append(Box(600, -100, 128, 128, box_image_path))
        box_spawned = True

    # --- TROLLEY SPAWN ---
    if not trolley_spawned:
        trolley_image_path = "Q:/Global game Jam/Veilshift/Charlotte/BackgroundAssets/BoxTrolly.png"
        trolleys.append(Trolley(800, -100, 128, 128, trolley_image_path))
        trolley_spawned = True

    # --- UPDATE BOXES / TROLLEYS (ONLY IN PUZZLE MASK) ---
    if current_mask == 2:
        for box in boxes: box.update(platforms)
        for trolley in trolleys: trolley.update(platforms)

    # --- DRAW ---
    screen.fill(AMBIENT_DARK)
    for p in platforms: p.draw()

    if DEBUG:
        enemy_vision = get_enemy_vision_polygon(enemy)
        color = ENEMY_DEBUG_COLOR_ALERT if enemy.alerted else ENEMY_DEBUG_COLOR_IDLE
        pygame.draw.polygon(screen, color, enemy_vision, width=2)

    vision_poly = get_vision_polygon(player.center)
    draw_light(player.center)
    enemy.draw_body(vision_poly)
    enemy.draw_eyes()

    # --- DRAW BOXES/TROLLEYS ONLY IF IN LIGHT ---
    if current_mask == 2:
        for box in boxes:
            if DEBUG or is_in_light(box.rect, player.center, facing_angle):
                box.draw(screen)
        for trolley in trolleys:
            if DEBUG or is_in_light(trolley.rect, player.center, facing_angle):
                trolley.draw(screen)

    img_to_draw = current_player_img
    if not facing_right: img_to_draw = pygame.transform.flip(current_player_img, True, False)
    screen.blit(img_to_draw, player.topleft)

    if DEBUG:
        hitbox_rect = pygame.Rect(player.x + 5, player.y, player.width - 10, player.height)
        pygame.draw.rect(screen, (0, 255, 0), hitbox_rect, 2)

    pygame.display.flip()







pygame.quit()
sys.exit()