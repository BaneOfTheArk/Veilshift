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

DEBUG = False

# ---------------- COLORS ----------------
AMBIENT_DARK = (18, 18, 22)

MASK_INFO = {
    0: {"color": (90, 140, 220)},    # Physical
    1: {"color": (200, 80, 80)},   # Spectral
    2: {"color": (90, 200, 130)},   # Puzzle
}

# ---------------- PLAYER ----------------
CUBE_SIZE = 36
player = pygame.Rect(150, 550, CUBE_SIZE, CUBE_SIZE)

# Load player image
player_img = pygame.image.load("Q:\Veilshift\Veilshift\Charlotte\PlayerIdleNoMask.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (CUBE_SIZE, CUBE_SIZE))

vel_x = 0
vel_y = 0
SPEED = 6
JUMP = 14
GRAVITY = 0.7
on_ground = False

# Track facing
facing_right = True

# ---------------- ENEMY ----------------
ENEMY_SPEED = 2
ENEMY_VISION_RADIUS = 350
ENEMY_FOV = 160  # peripheral vision
ENEMY_CHASE_SPEED = 4
EYE_MAX_DISTANCE = 400   # distance where eyes fully disappear
EYE_MIN_ALPHA = 40       # faint glow at max range
EYE_MAX_ALPHA = 255      # full glow up close

class Enemy:
    def __init__(self, x, y, patrol_width=200):
        self.rect = pygame.Rect(x, y, CUBE_SIZE, CUBE_SIZE)
        self.start_x = x
        self.patrol_width = patrol_width
        self.vel_x = ENEMY_SPEED
        self.facing_right = True
        self.alerted = False

    def patrol(self):
        self.rect.x += self.vel_x

        if self.rect.x > self.start_x + self.patrol_width:
            self.vel_x = -ENEMY_SPEED
            self.facing_right = False
        elif self.rect.x < self.start_x:
            self.vel_x = ENEMY_SPEED
            self.facing_right = True

    def can_see_player(self, player_pos):
        dx = player_pos[0] - self.rect.centerx
        dy = player_pos[1] - self.rect.centery
        distance = math.hypot(dx, dy)

        if distance > ENEMY_VISION_RADIUS:
            return False

        angle_to_player = math.degrees(math.atan2(dy, dx))
        facing_angle = 0 if self.facing_right else 180
        delta = (angle_to_player - facing_angle + 180) % 360 - 180

        return abs(delta) < ENEMY_FOV / 2

    def chase(self, player):
        if player.centerx > self.rect.centerx:
            self.rect.x += ENEMY_CHASE_SPEED
            self.facing_right = True
        else:
            self.rect.x -= ENEMY_CHASE_SPEED
            self.facing_right = False

    def update(self, player):
        self.alerted = self.can_see_player(player.center)

        if self.alerted:
            self.chase(player)
        else:
            self.patrol()

    def draw(self):
        body_visible = (current_mask == 1)

        # Draw body ONLY on mask 1
        if body_visible:
            screen.blit(player_img, self.rect.topleft)

        # Draw glowing eyes ONLY when body is hidden
        if not body_visible:
            dx = player.centerx - self.rect.centerx
            dy = player.centery - self.rect.centery
            distance = math.hypot(dx, dy)

            if distance < EYE_MAX_DISTANCE:
                alpha = max(
                    EYE_MIN_ALPHA,
                    int(EYE_MAX_ALPHA * (1 - distance / EYE_MAX_DISTANCE))
                )

                eye_surface = pygame.Surface((20, 10), pygame.SRCALPHA)

                for i in range(2):
                    pygame.draw.circle(
                        eye_surface,
                        (255, 255, 255, alpha),
                        (5 + i * 10, 5),
                        3
                    )

                eye_x = self.rect.x + (10 if self.facing_right else 4)
                eye_y = self.rect.y + 10
                screen.blit(eye_surface, (eye_x, eye_y))

def draw_enemy_in_light(enemy):
    temp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    temp.blit(player_img, enemy.rect.topleft)
    light_surface.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

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
        Platform((460, 500, 180, 25), [0]),
        Platform((700, 420, 180, 25), [0]),
        Platform((960, 340, 160, 25), [0]),
        Platform((320, 360, 160, 25), [0]),
        Platform((120, 280, 160, 25), [0]),
        Platform((0, 0, 40, 720), [0]),
        Platform((1240, 0, 40, 720), [0]),
    ]

platforms = load_level()
enemy = Enemy(600, 384)

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
    if DEBUG:
        return

    # Fill darkness
    light_surface.fill((0, 0, 0, 255))


    vision_poly = get_vision_polygon(origin, facing_right, platforms)
    pygame.draw.polygon(light_surface, (255, 255, 180, 200), vision_poly)

    # Draw enemies INTO the light mask (Mask 1 only)
    if current_mask == 1:
        for e in enemies:
            draw_enemy_in_light(e)

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
            
            if event.key == pygame.K_F3:
                DEBUG = not DEBUG

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
    enemy.update(player)

    # -------- DRAW --------
    screen.fill(AMBIENT_DARK)

    # Draw platforms normally
    for p in platforms:
        p.draw()

    # Draw realistic vision cone
    draw_light(player.center, facing_right)

    # Draw player ON TOP
    screen.blit(player_img, player.topleft)

    enemy.draw()

    pygame.display.flip()

pygame.quit()
sys.exit()