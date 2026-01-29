# light_system.py
import pygame
import math
import random
from settings import RAY_COUNT, RAY_STEP, FOV_ANGLE, AMBIENT_DARK

class LightSystem:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Darkness overlay (ALWAYS on top)
        self.dark_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Vision mask (used to CUT holes)
        self.vision_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Cheap animated void grain (darkness only)
        self.grain_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(0, height, 2):
            for x in range(0, width, 2):
                a = random.randint(8, 22)
                self.grain_surface.fill((0, 0, 0, a), (x, y, 2, 2))

        self.grain_offset = 0

    # ---------------- RAYCAST ----------------
    def cast_ray(self, origin, angle, platforms, max_radius, current_mask):
        ox, oy = origin
        rad = math.radians(angle)
        dx, dy = math.cos(rad), math.sin(rad)

        for dist in range(0, int(max_radius), RAY_STEP):
            px = ox + dx * dist
            py = oy + dy * dist

            for p in platforms:
                # Only block vision if platform is visible
                if not p.visible(current_mask):
                    continue
                if p.rect.collidepoint(px, py):
                    return (px, py)

        return (ox + dx * max_radius, oy + dy * max_radius)

    def get_vision_polygon(self, origin, facing_angle, cone_radius, platforms, current_mask):
        points = [origin]
        start_angle = facing_angle - FOV_ANGLE / 2
        step = FOV_ANGLE / RAY_COUNT
        t = pygame.time.get_ticks() * 0.002

        for i in range(RAY_COUNT + 1):
            angle = start_angle + i * step
            px, py = self.cast_ray(origin, angle, platforms, cone_radius, current_mask)

            # subtle organic edge wobble
            wobble = math.sin(i * 0.6 + t) * 1.2
            dx, dy = px - origin[0], py - origin[1]
            length = max(0, math.hypot(dx, dy) + wobble)
            ang = math.atan2(dy, dx)

            points.append((
                origin[0] + math.cos(ang) * length,
                origin[1] + math.sin(ang) * length
            ))

        return points

    # ---------------- DRAW VISION ----------------
    def draw_light(
        self,
        origin,
        focus_ratio,
        platforms,
        current_mask,
        facing_angle,
        cone_radius,
        camera_offset=(0, 0)  # 🔑 SAFE CAMERA FIX
    ):
        """
        origin is WORLD position
        camera_offset is (cam_x, cam_y)
        """

        # Convert world → screen
        ox = origin[0] - camera_offset[0]
        oy = origin[1] - camera_offset[1]
        screen_origin = (int(ox), int(oy))

        # 1️⃣ Full darkness
        self.dark_surface.fill(AMBIENT_DARK)

        # 2️⃣ Reset vision mask
        self.vision_surface.fill((0, 0, 0, 0))

        # 3️⃣ Player personal visibility (never disappears)
        pygame.draw.circle(
            self.vision_surface,
            (255, 255, 255, 255),
            screen_origin,
            28
        )

        # 4️⃣ Vision cone (focus affects RANGE only)
        effective_radius = int(cone_radius * max(0.15, focus_ratio))

        poly = self.get_vision_polygon(
            screen_origin,
            facing_angle,
            effective_radius,
            platforms,
            current_mask
        )

        pygame.draw.polygon(
            self.vision_surface,
            (255, 255, 255, 255),
            poly
        )

        # 5️⃣ Cut vision out of darkness
        self.dark_surface.blit(
            self.vision_surface,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_SUB
        )

        # 6️⃣ Animated void grain (darkness only)
        self.grain_offset = (self.grain_offset + 1) % self.width
        self.dark_surface.blit(self.grain_surface, (-self.grain_offset, 0))
        self.dark_surface.blit(self.grain_surface, (self.width - self.grain_offset, 0))

        return self.dark_surface
