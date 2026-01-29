# player.py
import pygame
import math
import settings as s

class Player:
    def __init__(self, rect, img):
        self.rect = pygame.Rect(rect)
        self.img = img

        # movement
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.jump_held = False

        # visual
        self.current_scale_x = 1.0
        self.bob_offset = 0.0

        # focus
        self.focus = s.FOCUS_MAX
        self.max_focus = s.FOCUS_MAX
        self.focus_active = False
        self.focus_debounce_timer = 0.0
        self.current_cone_radius = s.BASE_CONE_RADIUS

        # grapple
        self.grapple_active = False
        self.grapple_target = None

        # facing
        self.facing_angle = 0
        self.target_angle = 0

        # current mask
        self.current_mask = 0
        self.current_mask = 1
        self.health = 100
        self.max_health = 100

    # ---------------- INPUT & AIMING ----------------
    def handle_input(self, keys, dt):
        # horizontal movement
        if keys[pygame.K_a]:
            self.vel_x -= s.ACCEL * dt * 60
        elif keys[pygame.K_d]:
            self.vel_x += s.ACCEL * dt * 60
        else:
            self.vel_x *= s.FRICTION

        self.vel_x = max(-s.SPEED, min(s.SPEED, self.vel_x))

        # jump
        if keys[pygame.K_SPACE] and self.on_ground and not self.jump_held:
            self.vel_y = -s.JUMP
            self.jump_held = True
        elif not keys[pygame.K_SPACE]:
            self.jump_held = False

        # aiming / facing angle
        if keys[pygame.K_w]:
            self.target_angle = -90
            if keys[pygame.K_a]: self.target_angle = -135
            if keys[pygame.K_d]: self.target_angle = -45
        elif keys[pygame.K_s]:
            self.target_angle = 90
            if keys[pygame.K_a]: self.target_angle = 135
            if keys[pygame.K_d]: self.target_angle = 45
        else:
            if keys[pygame.K_a]:
                self.target_angle = 180
            if keys[pygame.K_d]:
                self.target_angle = 0

        # Smoothly rotate facing angle
        if self.target_angle is not None:
            delta = (self.target_angle - self.facing_angle)
            # Wrap-around fix for angles
            if delta > 180: delta -= 360
            elif delta < -180: delta += 360
            self.facing_angle += delta * 0.25
            self.facing_angle %= 360

    # ---------------- FOCUS ----------------
    def update_focus(self, dt, holding_shift):
        if self.focus_active:
            if holding_shift and self.focus > 0:
                self.focus -= s.FOCUS_DRAIN * dt
                self.focus = max(0, self.focus)
                target_radius = s.MAX_CONE_RADIUS
            else:
                self.focus_active = False
                self.focus_debounce_timer = s.FOCUS_DEBOUNCE_TIME
                target_radius = s.BASE_CONE_RADIUS
        else:
            if holding_shift and self.focus >= s.FOCUS_ACTIVATE_THRESHOLD and self.focus_debounce_timer <= 0:
                self.focus_active = True
                target_radius = s.MAX_CONE_RADIUS
            else:
                if self.focus_debounce_timer > 0:
                    self.focus_debounce_timer -= dt
                else:
                    regen_rate = s.FOCUS_REGEN_SLOW if self.focus < s.FOCUS_SLOW_REGEN_THRESHOLD else s.FOCUS_REGEN_FAST
                    self.focus += regen_rate * dt
                    self.focus = min(s.FOCUS_MAX, self.focus)
                target_radius = s.BASE_CONE_RADIUS

        # Smooth transition of cone radius
        self.current_cone_radius += (target_radius - self.current_cone_radius) * 0.12

    # ---------------- FOCUS RATIO ----------------
    def focus_ratio(self):
        return self.focus / s.FOCUS_MAX

    # ---------------- PHYSICS ----------------
    def move_and_collide(self, platforms):
        self.rect.x += int(self.vel_x)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_x > 0:
                    self.rect.right = p.rect.left
                elif self.vel_x < 0:
                    self.rect.left = p.rect.right

        self.vel_y += s.GRAVITY
        self.vel_y = min(self.vel_y, 18)
        self.rect.y += int(self.vel_y)

        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.on_ground = True
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0

    # ---------------- GRAPPLE ----------------
    def update_grapple(self, dt):
        if not self.grapple_active or not self.grapple_target:
            return
        px, py = self.rect.center
        tx, ty = self.grapple_target.rect.center
        dx, dy = tx - px, ty - py
        dist = math.hypot(dx, dy)
        if dist < 5:
            self.grapple_active = False
            self.vel_x = self.vel_y = 0
            return
        nx, ny = dx / dist, dy / dist
        self.vel_x, self.vel_y = nx * s.GRAPPLE_SPEED * dt, ny * s.GRAPPLE_SPEED * dt
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)

    # ---------------- DRAW ----------------
    def draw(self, surface):
        t = pygame.time.get_ticks() * 0.004
        self.bob_offset = math.sin(t) * 1

        h_scale = self.current_scale_x
        v_scale = 1 - 0.05 * abs(self.vel_x) / s.SPEED
        scaled_img = pygame.transform.scale(self.img, (int(s.CUBE_SIZE * abs(h_scale)), int(s.CUBE_SIZE * v_scale)))
        if h_scale < 0: scaled_img = pygame.transform.flip(scaled_img, True, False)

        surface.blit(scaled_img, (self.rect.topleft[0], self.rect.topleft[1] + self.bob_offset))

    # ---------------- FLIP ----------------
    def update_flip(self):
        target_scale_x = 1 if self.vel_x >= 0 else -1
        self.current_scale_x += (target_scale_x - self.current_scale_x) * 0.2

    # ---------------- UPDATE ALL ----------------
    def update(self, dt, platforms, keys, holding_shift):
        self.handle_input(keys, dt)
        self.update_focus(dt, holding_shift)

        if self.grapple_active:
            self.update_grapple(dt)
        else:
            self.move_and_collide(platforms)

        self.update_flip()