import pygame
import sys
import math
import random

pygame.init()

# Get full monitor resolution for fullscreen
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

# Create the screen in fullscreen mode
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)

# ---------------- SETTINGS ----------------
FPS = 60
clock = pygame.time.Clock()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)

DEBUG = False

MASKLESS = -1
MASKLESS_COLOR = (255, 255, 255)

# Helper Functions

def get_mask_color():
    if current_mask == MASKLESS:
        return MASKLESS_COLOR
    return MASK_INFO[current_mask]["color"]

def load_background(path):
    """Load background and scale to full screen."""
    img = pygame.image.load(path).convert()  # convert() for performance
    return pygame.transform.scale(img, (WIDTH, HEIGHT))

# ---------------- COLORS ----------------
MASK_INFO = {
    0: {"color": (90, 140, 220)},   # Physical
    1: {"color": (200, 80, 80)},    # Spectral
    2: {"color": (90, 200, 130)},   # Puzzle
}

# --------------- PUZZLE VARIABLES/CONSTANTS ----------------
PUZZLE_COLORS = [
    (200, 60, 60),   # Red
    (60, 200, 120),  # Green
    (80, 120, 220),  # Blue
]

PUZZLE_SOLUTION = [0, 2, 2, 1]  # R, B, B, R

puzzle_open = False
puzzle_values = [0, 0, 0, 0]  # indices into PUZZLE_COLORS

PUZZLE_SQUARE_SIZE = 100  # Bigger squares
PUZZLE_SPACING = 30       # Space between squares

PUZZLE_BASE_X = (WIDTH - (4 * PUZZLE_SQUARE_SIZE + 3 * PUZZLE_SPACING)) // 2
PUZZLE_BASE_Y = (HEIGHT - PUZZLE_SQUARE_SIZE) // 2

PUZZLE_OPEN_DISTANCE = 150

# ---------------- PLAYER ----------------
CUBE_SIZE = 36
player = pygame.Rect(150, 550, CUBE_SIZE, CUBE_SIZE)
MAX_HEALTH = 3
player_health = MAX_HEALTH
INVULN_TIME = 60  # frames
damage_timer = 0


# ---------------- PLAYER SPRITES ----------------

PLAYER_SPRITES = {
    MASKLESS: {
        "idle": pygame.transform.scale(
            pygame.image.load(
                "Veilshift/Charlotte/PlayerSprites/PlayerIdleNoMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
        "run": pygame.transform.scale(
            pygame.image.load(
                "Q:/Veilshift/Veilshift/Charlotte/PlayerSprites/PlayerRunningNoMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
    },

    0: {  # Spectral mask
        "idle": pygame.transform.scale(
            pygame.image.load(
                "Q:\Veilshift\Veilshift\Charlotte\PlayerSprites\PlayerIdlePlatformMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
        "run": pygame.transform.scale(
            pygame.image.load(
                "Veilshift/Charlotte/PlayerSprites/PlayerRunningPlatformMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
    },

    1: {  # Physical mask
        "idle": pygame.transform.scale(
            pygame.image.load(
                "Q:\Veilshift\Veilshift\Charlotte\PlayerSprites\PlayerIdleAttackMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
        "run": pygame.transform.scale(
            pygame.image.load(
                "Q:\Veilshift\Veilshift\Charlotte\PlayerSprites\PlayerRunningAttackMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
    },

    2: {  # Puzzle mask
        "idle": pygame.transform.scale(
            pygame.image.load(
                "Q:\Veilshift\Veilshift\Charlotte\PlayerSprites\PlayerIdlePuzzleMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
        "run": pygame.transform.scale(
            pygame.image.load(
                "Q:\Veilshift\Veilshift\Charlotte\PlayerSprites\PlayerRunningPuzzleMask.png"
            ).convert_alpha(),
            (CUBE_SIZE, CUBE_SIZE)
        ),
    },
}

# Backgrounds
BACKGROUND_1 = 0
BACKGROUND_2 = 1
BACKGROUND_3 = 2

def load_background(path):
    """Load and scale background to full screen."""
    return pygame.transform.scale(
        pygame.image.load(path).convert(),
        (WIDTH, HEIGHT)
    )

# Registry of backgrounds
BACKGROUNDS = {
    BACKGROUND_1: load_background("Q:\Veilshift\Veilshift\Charlotte\Backgrounds\BackgroundA.png")
    # BACKGROUND_2: load_background("Q:/Veilshift/Veilshift/Charlotte/BackgroundB.png"),
    # BACKGROUND_3: load_background("Q:/Veilshift/Veilshift/Charlotte/BackgroundC.png"),
}

current_background = BACKGROUND_1

def draw_background():
    """Draw the current background full-screen."""
    screen.blit(BACKGROUNDS[current_background], (0, 0))


# Player Variables/Constants
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

# Hints stuff
# Number of hints for each type
HINT_COUNTS = {
    "Red": 1,
    "Green": 1,
    "Blue": 2,
}

HINT_IMAGES = {
    "Red": pygame.image.load("Q:\Veilshift\Veilshift\Charlotte\Red.png").convert_alpha(),
    "Green": pygame.image.load("Q:\Veilshift\Veilshift\Charlotte\Green.png").convert_alpha(),
    "Blue": pygame.image.load("Q:\Veilshift\Veilshift\Charlotte\Blue.png").convert_alpha(),
}

HINT_POSITIONS = {
    "Red": [(200, 400)],
    "Green": [(800, 425)],
    "Blue": [(400, 415), (600, 455)],
}

# Enemy image
enemy1_img = pygame.image.load("Q:\Veilshift\Veilshift\Charlotte\ShadowMonster.png"
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

ENEMY_MAX_HEALTH = 2
ATTACK_DAMAGE = 1
ATTACK_RANGE = 80
ATTACK_COOLDOWN = 20  # frames

EYE_MAX_DISTANCE = 400
EYE_MIN_ALPHA = 40
EYE_MAX_ALPHA = 255

ENEMY_DEBUG_COLOR_IDLE = (255, 255, 0, 60)   # yellow
ENEMY_DEBUG_COLOR_ALERT = (255, 80, 80, 80) # red

# ---------------- PLAYER ATTACK ----------------
PLAYER_ATTACK_RANGE = 80
PLAYER_ATTACK_COOLDOWN = 20  # frames
player_attack_timer = 0

# ---------------- IN-GAME BOX/TROLLEY MANAGEMENT ----------------
boxes = []
trolleys = []
box_spawned = False
trolley_spawned = False
player_on_box = None
player_on_trolley = None

# ---------------- PLATFORM ----------------
class Platform:
    def __init__(self, rect, masks=None, visible=True):
        self.rect = pygame.Rect(rect)
        self.masks = masks  # None = always visible
        self.visible = visible  # Can hide walls/platforms

    def active(self):
        if current_mask == MASKLESS:
            return self.masks is None  # only walls & floor
        if self.masks is None:
            return True
        return current_mask in self.masks

    def draw(self):
        if not self.active() or not self.visible:
            return
        base = get_mask_color()
        color = tuple(min(255, c + 20) for c in base)
        pygame.draw.rect(screen, color, self.rect, border_radius=4)

# ---------------- BOX / TROLLEY ----------------
class Box:
    def __init__(self, x, y, width, height, image_path=None, hit_offset_x=46, hit_offset_y=50, hitbox_size=35):
        self.rect = pygame.Rect(x, y, width, height)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.saved_pos = self.rect.topleft
        self.active_in_game = True  # Only active in puzzle mask

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

        # Update main rect to follow hit_rect
        self.rect.topleft = (self.hit_rect.x - self.hit_offset_x,
                             self.hit_rect.y - self.hit_offset_y)
        self.saved_pos = self.rect.topleft

    def push(self, player_rect, player_vel_x):
        if not self.active_in_game:
            return

        # Only push if player is touching the sides (horizontal)
        if self.hit_rect.colliderect(player_rect):
            if player_rect.right > self.hit_rect.left and player_rect.left < self.hit_rect.left:
                # Player on left pushes right
                self.vel_x += player_vel_x
            elif player_rect.left < self.hit_rect.right and player_rect.right > self.hit_rect.right:
                # Player on right pushes left
                self.vel_x += player_vel_x

    def update(self, platforms):
        # Only active in puzzle mask
        if current_mask == 2:
            self.active_in_game = True
        else:
            if self.active_in_game:
                self.saved_pos = self.rect.topleft
            self.active_in_game = False
            return

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
        super().__init__(x, y, width, height, image_path)

        # Adjust hitbox for trolley
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

# ---------------- PUZZLE TRIGGER ----------------
class PuzzleTrigger:
    def __init__(self, x, y, size=40):
        self.rect = pygame.Rect(x, y, size, size)

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def draw(self):
        pygame.draw.rect(screen, (40, 40, 40), self.rect)
        pygame.draw.rect(screen, (90, 200, 130), self.rect, 2)

puzzle_trigger = PuzzleTrigger(180, 240)

# ---------------- LEVEL ----------------
def load_level():
    return [
        Platform((0, 680, 1280, -80), None, visible=True),     # Floor always visible
        Platform((0, 0, 40, 720), None, visible=True),        # Left wall always visible
        Platform((1240, 0, 40, 720), None, visible=True),     # Right wall always visible
        Platform((0, 120, 1280, 80), None, visible=True),     # Roof

        # Mask-specific platforms
        Platform((460, 500, 180, 25), [0]),
        Platform((700, 420, 180, 25), [0]),
        Platform((960, 340, 160, 25), [0]),
        Platform((320, 360, 160, 25), [0]),
        Platform((120, 280, 160, 25), [0,2]),
    ]

platforms = load_level()

# ---------------- COLLISION ----------------
def move_and_collide(rect, dx, dy):
    global on_ground

    rect.x += dx
    for p in platforms:
        # Only collide if platform is active for current mask
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

def get_player_attack_rect():
    if facing_right:
        return pygame.Rect(
            player.right,
            player.centery - 20,
            PLAYER_ATTACK_RANGE,
            40
        )
    else:
        return pygame.Rect(
            player.left - PLAYER_ATTACK_RANGE,
            player.centery - 20,
            PLAYER_ATTACK_RANGE,
            40
        )

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

def is_in_light(rect, light_origin, facing_angle):
    """
    Returns True if the center of rect is inside the player's light cone.
    """
    poly = get_vision_polygon(light_origin)
    return point_in_polygon(rect.center, poly)

def draw_light(origin):
    global pulse_timer

    # Clear the light surface every frame
    light_surface.fill((0, 0, 0, 180))

    if DEBUG:
        # Clear the screen for debug mode too
        screen.fill((30, 30, 30))  # simple dark grey for debug
        for p in platforms:
            if p.active():
                p.draw()
        # Skip lighting entirely in debug
        return

    # --- Mini pulsing spotlight ---
    pulse_timer += 1 / FPS
    pulse_radius = MIN_PULSE_RADIUS + (MAX_PULSE_RADIUS - MIN_PULSE_RADIUS) * (
        0.5 + 0.5 * math.sin(pulse_timer * PULSE_SPEED * math.pi)
    )
    mini_spot = pygame.Surface((pulse_radius * 2, pulse_radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(
        mini_spot,
        (255, 255, 200, 100),
        (pulse_radius, pulse_radius),
        int(pulse_radius)
    )
    light_surface.blit(
        mini_spot,
        (origin[0] - pulse_radius, origin[1] - pulse_radius),
        special_flags=pygame.BLEND_RGBA_ADD
    )

    # --- Main cone light ---
    poly = get_vision_polygon(origin)
    pygame.draw.polygon(light_surface, (255, 255, 180, 200), poly)

    # --- Draw background and platforms ---
    draw_background()
    for p in platforms:
        p.draw()

    # --- Apply lighting ---
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
        self.health = ENEMY_MAX_HEALTH
        self.dead = False

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

    def take_damage(self, dmg):
        if self.dead:
            return
        self.health -= dmg
        if self.health <= 0:
            self.dead = True

    def update(self, player):
        if self.dead:
            return
        global player_health, damage_timer

        self.alerted = self.can_see_player(player.center)
        self.facing_right = player.centerx > self.rect.centerx if self.alerted else self.facing_right
        self.chase() if self.alerted else self.patrol()

        self.vel_y = min(self.vel_y + ENEMY_GRAVITY, ENEMY_MAX_FALL)
        self.rect, self.vel_y = move_and_collide(self.rect, self.vel_x, self.vel_y)

        # -------- ATTACK PLAYER --------
        if self.rect.colliderect(player) and damage_timer <= 0:
            player_health -= 1
            damage_timer = INVULN_TIME

    def draw_body(self, vision_poly):
        if self.dead:
            return
        if current_mask == 3:
            return
        if current_mask == 1 and point_in_polygon(self.rect.center, vision_poly):
            img = enemy1_img
            if not self.facing_right:
                img = pygame.transform.flip(enemy1_img, True, False)
            screen.blit(img, self.rect.topleft)

    def draw_eyes(self):
        if self.dead:
            return
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

class Ghost:
    def __init__(self, x, y):
        # existing stuff...
        self.rect = pygame.Rect(x, y, CUBE_SIZE, CUBE_SIZE)
        self.visible = True
        self.stun_duration = 5 * FPS
        self.stunned_timer = 0

        # Vision cone
        self.vision_radius = 250
        self.vision_angle = 90  # cone width
        self.facing_right = True  # direction ghost is looking

        # Load a ghost image (or fallback to white rectangle)
        try:
            self.image = pygame.image.load("Q:\Veilshift\Veilshift\Charlotte\GhostSprite.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (CUBE_SIZE, CUBE_SIZE))
        except:
            self.image = None

        # Screen shake settings
        self.shake_intensity = 8
        self.shake_duration = 10  # frames
        self.shake_timer = 0

    def update(self, player):
        if not self.visible:
            return

        if self.stunned_timer > 0:
            self.stunned_timer -= 1
            return

        # Determine direction the ghost is facing based on player position
        self.facing_right = player.centerx > self.rect.centerx

        # Check if player is in vision
        vision_poly = self.get_vision_polygon()
        player_in_sight = point_in_polygon(player.center, vision_poly)

        if player_in_sight:
            # Move toward player
            dx = player.centerx - self.rect.centerx
            dy = player.centery - self.rect.centery
            distance = math.hypot(dx, dy)
            if distance > 0:
                dx /= distance
                dy /= distance
                speed = 3
                self.rect.x += int(dx * speed)
                self.rect.y += int(dy * speed)

            # Collision with player triggers stun and shake
            if self.rect.colliderect(player):
                self.visible = False
                self.shake_timer = self.shake_duration
                self.stunned_timer = self.stun_duration

    def get_vision_polygon(self):
        """Return a polygon representing the ghost's vision cone."""
        origin = self.rect.center
        points = [origin]

        start_angle = -self.vision_angle / 2 if self.facing_right else 180 - self.vision_angle / 2
        step = self.vision_angle / 10  # fewer rays for simplicity

        for i in range(11):
            angle = start_angle + i * step
            rad = math.radians(angle)
            dx = math.cos(rad) * self.vision_radius
            dy = math.sin(rad) * self.vision_radius
            points.append((origin[0] + dx, origin[1] + dy))

        return points

    def draw(self, shake_offset=(0,0)):
        if self.visible and current_mask == 0:
            pos = (self.rect.x + shake_offset[0], self.rect.y + shake_offset[1])
            if self.image:
                screen.blit(self.image, pos)
            else:
                pygame.draw.rect(screen, (200,200,255), (*pos, self.rect.width, self.rect.height))

    def apply_shake(self):
        """Return an offset tuple (x, y) for screen shake."""
        if self.shake_timer > 0:
            self.shake_timer -= 1
            offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            offset_y = random.randint(-self.shake_intensity, self.shake_intensity)
            return offset_x, offset_y
        return 0, 0
    
enemy = Enemy(600, 384)

ghost = Ghost(400, 300)
player_stunned_timer = 0

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

    # -------- EVENTS --------
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            if e.key == pygame.K_1: current_mask = MASKLESS
            if e.key == pygame.K_2: current_mask = 0
            if e.key == pygame.K_3: current_mask = 1
            if e.key == pygame.K_4: current_mask = 2
            if e.key == pygame.K_F3: DEBUG = not DEBUG
            # -------- PLAYER ATTACK --------
            if e.key == pygame.K_q and player_attack_timer <= 0 and player_stunned_timer <= 0:
                if current_mask ==1:
                    attack_rect = get_player_attack_rect()

                    if attack_rect.colliderect(enemy.rect) and not enemy.dead:
                        enemy.take_damage(enemy.health)  # one-hit kill

                    player_attack_timer = PLAYER_ATTACK_COOLDOWN

            # TAP E to open puzzle only if close and has puzzle mask
            if e.key == pygame.K_e:
                dx = player.centerx - puzzle_trigger.rect.centerx
                dy = player.centery - puzzle_trigger.rect.centery
                distance = math.hypot(dx, dy)
                if distance <= PUZZLE_OPEN_DISTANCE and current_mask == 2:
                    puzzle_open = True

                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_F1:
                        current_background = BACKGROUND_1
                    # if e.key == pygame.K_F2:
                    #     current_background = BACKGROUND_2
                    # if e.key == pygame.K_F3:
                    #     current_background = BACKGROUND_3

        # Handle puzzle clicks
        if e.type == pygame.MOUSEBUTTONDOWN and puzzle_open and current_mask == 2:
            mx, my = pygame.mouse.get_pos()
            for i in range(4):
                rect = pygame.Rect(
                    PUZZLE_BASE_X + i * (PUZZLE_SQUARE_SIZE + PUZZLE_SPACING),
                    PUZZLE_BASE_Y,
                    PUZZLE_SQUARE_SIZE,
                    PUZZLE_SQUARE_SIZE
                )
                if rect.collidepoint(mx, my):
                    puzzle_values[i] = (puzzle_values[i] + 1) % len(PUZZLE_COLORS)

    # -------- PLAYER STUN --------
    if ghost.stunned_timer > 0:
        ghost.stunned_timer -= 1
        player_stunned_timer = ghost.stunned_timer

    # -------- INPUT / MOVEMENT --------
    if player_stunned_timer <= 0:
        vel_x = (-SPEED if keys[pygame.K_a] else SPEED if keys[pygame.K_d] else 0)
        if vel_x != 0:
            facing_right = vel_x > 0
    else:
        vel_x = 0

    # Auto-close puzzle if player moves too far
    dx = player.centerx - puzzle_trigger.rect.centerx
    dy = player.centery - puzzle_trigger.rect.centery
    distance = math.hypot(dx, dy)

    if distance > PUZZLE_OPEN_DISTANCE:
        puzzle_open = False

    # -------- SPRITE SELECTION --------
    state = "run" if vel_x != 0 else "idle"

    # Fallback safety (prevents crashes)
    sprites = PLAYER_SPRITES.get(current_mask, PLAYER_SPRITES[MASKLESS])
    current_player_img = sprites[state]

    # -------- PHYSICS --------
    vel_y = min(vel_y + GRAVITY, 18)
    player, vel_y = move_and_collide(player, vel_x, vel_y)

    # --- BOX SPAWN ---
    if not box_spawned and puzzle_values == PUZZLE_SOLUTION:
        box_image_path = "Veilshift/Charlotte/BackgroundAssets/BigBoxLevel1 .png"
        box_x = 600
        box_y = 200  # underneath roof
        boxes.append(Box(box_x, box_y, 128, 128, box_image_path))
        box_spawned = True

    # --- TROLLEY SPAWN ---
    if not trolley_spawned:
        trolley_image_path = "Veilshift/Charlotte/BackgroundAssets/BoxTrolly.png"
        trolley_y = 680 - 128  # sit on floor
        trolleys.append(Trolley(600, trolley_y, 128, 128, trolley_image_path))
        trolley_spawned = True

    # --- BOX + TROLLEY MERGE INTO BOX WITH WHEELS ---
    if current_mask == 2:
        new_boxes = []
        new_trolleys = []
        for box in boxes:
            merged = False
            for trolley in trolleys:
                if box.hit_rect.colliderect(trolley.hit_rect):
                    box_with_wheels_image = "Veilshift/Charlotte/BackgroundAssets/BoxWithWheels.png"
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

    # --- UPDATE BOXES / TROLLEYS (ONLY IN PUZZLE MASK) ---
    if current_mask == 2:
        for box in boxes:
            box.push(player, vel_x)
        for trolley in trolleys:
            trolley.push(player, vel_x)

    if current_mask == 2:
        for box in boxes: box.update(platforms)
        for trolley in trolleys: trolley.update(platforms)

        # -------- JUMP --------
    keys = pygame.key.get_pressed()

    if keys[pygame.K_SPACE] and player_stunned_timer <= 0:
        if on_ground and not jump_held:
            vel_y = -JUMP
            jump_held = True
    else:
        jump_held = False

    # -------- DAMAGE COOLDOWN --------
    if damage_timer > 0:
        damage_timer -= 1

    # Player attack cd
    if player_attack_timer > 0:
        player_attack_timer -= 1

    # -------- PLAYER DEATH --------
    if player_health <= 0:
        print("Player died")
        running = False

    enemy.update(player)
    ghost.update(player)

    # -------- SCREEN SHAKE --------
    shake_offset_x, shake_offset_y = ghost.apply_shake()

    # -------- DRAW --------
    # Draw background
    screen.blit(BACKGROUNDS[current_background], (0 + shake_offset_x, 0 + shake_offset_y))

    # Draw platforms
    for p in platforms:
        if p.active():
            rect = p.rect.move(shake_offset_x, shake_offset_y)
            base = get_mask_color()
            color = tuple(min(255, c + 20) for c in base)
            pygame.draw.rect(screen, color, rect, border_radius=4)

# --- DEBUG OVERLAYS ---
    if DEBUG:
        pygame.draw.polygon(screen, (0, 255, 255), vision_poly, width=2)
        pygame.draw.rect(screen, (255, 0, 0), player, width=2)
        pygame.draw.rect(screen, (255, 0, 255), enemy.rect, width=2)
        enemy_vision = get_enemy_vision_polygon(enemy)
        color = ENEMY_DEBUG_COLOR_ALERT if enemy.alerted else ENEMY_DEBUG_COLOR_IDLE
        pygame.draw.polygon(screen, color, enemy_vision, width=2)

        if DEBUG and player_attack_timer > PLAYER_ATTACK_COOLDOWN - 2:
            pygame.draw.rect(screen, (255, 255, 0), get_player_attack_rect(), 2)

    vision_poly = get_vision_polygon(player.center)
    draw_light(player.center)

    # Only show hints if Maskless
    if current_mask == MASKLESS:
        for hint_type, positions in HINT_POSITIONS.items():
            img = HINT_IMAGES[hint_type]
            for pos in positions[:HINT_COUNTS[hint_type]]:
                # Check if the center of the hint is inside the vision polygon
                hint_rect = img.get_rect(topleft=pos)
                hint_center = hint_rect.center
                if point_in_polygon(hint_center, vision_poly):
                    screen.blit(img, pos)

    # --- DRAW BOXES/TROLLEYS ONLY IF IN LIGHT ---
    if current_mask == 2:
        for box in boxes:
            if DEBUG or is_in_light(box.rect, player.center, facing_angle):
                box.draw(screen)
        for trolley in trolleys:
            if DEBUG or is_in_light(trolley.rect, player.center, facing_angle):
                trolley.draw(screen)

    # Draw enemies
    enemy.draw_body(vision_poly)
    enemy.draw_eyes()

    ghost.draw(shake_offset=(shake_offset_x, shake_offset_y))

    # Draw puzzle trigger (white box) only if close and has puzzle mask
    dx = player.centerx - puzzle_trigger.rect.centerx
    dy = player.centery - puzzle_trigger.rect.centery
    distance = math.hypot(dx, dy)

    if distance <= PUZZLE_OPEN_DISTANCE and current_mask == 2:
        pygame.draw.rect(screen, (40, 40, 40), puzzle_trigger.rect)
        pygame.draw.rect(screen, (90, 200, 130), puzzle_trigger.rect, 2)

    # Draw puzzle UI if open AND player has puzzle mask
    if puzzle_open and current_mask == 2:
        for i in range(4):
            rect = pygame.Rect(
                PUZZLE_BASE_X + i * (PUZZLE_SQUARE_SIZE + PUZZLE_SPACING),
                PUZZLE_BASE_Y,
                PUZZLE_SQUARE_SIZE,
                PUZZLE_SQUARE_SIZE
            )
            pygame.draw.rect(screen, PUZZLE_COLORS[puzzle_values[i]], rect)
            pygame.draw.rect(screen, (20, 20, 20), rect, 5)

    # Draw player on top with flipping
    img_to_draw = current_player_img
    if not facing_right:  # flip if moving left
        img_to_draw = pygame.transform.flip(current_player_img, True, False)
    player_pos = (player.topleft[0] + shake_offset_x, player.topleft[1] + shake_offset_y)
    screen.blit(img_to_draw, player_pos)

    # -------- HEALTH BAR --------
    BAR_X = 20
    BAR_Y = 20
    BAR_WIDTH = 150
    BAR_HEIGHT = 20

    # Background
    pygame.draw.rect(screen, (40, 40, 40), (BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT))

    # Health
    health_width = int((player_health / MAX_HEALTH) * BAR_WIDTH)
    pygame.draw.rect(screen, (200, 50, 50), (BAR_X, BAR_Y, health_width, BAR_HEIGHT))

    # Border
    pygame.draw.rect(screen, (255, 255, 255), (BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT), 2)

    pygame.display.flip()

pygame.quit()
sys.exit()