# end_credits.py
import pygame
import sys
import random
import math


class ShootingStar:
    def __init__(self, w, h):
        self.x = random.randint(0, w)
        self.y = random.randint(0, h // 2)
        self.speed = random.uniform(600, 900)
        self.angle = random.uniform(-0.6, -0.9)
        self.life = random.uniform(0.3, 0.6)
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

    def draw(self, surf):
        tail = 18
        end_x = self.x - math.cos(self.angle) * tail
        end_y = self.y - math.sin(self.angle) * tail
        pygame.draw.line(surf, (200, 220, 255), (self.x, self.y), (end_x, end_y), 2)

    def dead(self):
        return self.timer >= self.life


class EndCredits:
    """
    Stylised VEILSHIFT end credits.
    - Starry void background with shooting stars
    - Player falling down center
    - Alternating left/right credits
    - Simple, stable radial spotlight
    """

    def __init__(self, screen, player_img=None, font_path=None):
        self.screen = screen
        self.w, self.h = screen.get_size()

        # ---------------- FONTS ----------------
        self.font_title = self._load_font(font_path, 44)
        self.font_text = self._load_font(font_path, 26)

        # ---------------- CREDITS ----------------
        self.credits = [
            ("VEILSHIFT", ""),
            ("A GAME JAM EXPERIENCE", ""),
            ("", ""),
            ("CREATED BY", "YOUR NAME"),
            ("PROGRAMMING & DESIGN", "YOUR NAME"),
            ("ART & VISUALS", "YOUR NAME"),
            ("MUSIC & SOUND", "COMPOSER NAME"),
            ("", ""),
            ("THANK YOU FOR PLAYING", ""),
            ("END OF TRANSMISSION", ""),
        ]

        # ---------------- SCROLL ----------------
        self.scroll_y = self.h + 80
        self.scroll_speed = 45

        # ---------------- PLAYER ----------------
        self.player_img = None
        if isinstance(player_img, pygame.Surface):
            self.player_img = pygame.transform.scale(player_img, (32, 32))
        self.player_y = -48

        # ---------------- STARS ----------------
        self.stars = [
            (random.randint(0, self.w), random.randint(0, self.h), random.randint(1, 2))
            for _ in range(180)
        ]
        self.shooting_stars = []
        self.star_timer = 0

        # ---------------- LIGHT ----------------
        self.dark_surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.light_surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)

        self.clock = pygame.time.Clock()
        self.running = True

    # ---------------- UTIL ----------------
    def _load_font(self, path, size):
        if path:
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
        return pygame.font.SysFont("Courier", size, bold=True)

    # ---------------- DRAW HELPERS ----------------
    def draw_stars(self):
        for x, y, r in self.stars:
            pygame.draw.circle(self.screen, (160, 170, 200), (x, y), r)

    def draw_shooting_stars(self, dt):
        self.star_timer += dt
        if self.star_timer > random.uniform(1.2, 2.8):
            self.star_timer = 0
            self.shooting_stars.append(ShootingStar(self.w, self.h))

        for s in self.shooting_stars[:]:
            s.update(dt)
            s.draw(self.screen)
            if s.dead():
                self.shooting_stars.remove(s)

    def draw_radial_light(self, pos):
        radius = 90
        for r in range(radius, 0, -5):
            alpha = int(120 * (r / radius))
            pygame.draw.circle(
                self.light_surface,
                (255, 255, 255, alpha),
                pos,
                r
            )

    # ---------------- MAIN ----------------
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            self.scroll_y -= self.scroll_speed * dt
            self.player_y += self.scroll_speed * dt * 0.25

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False

            # ---------------- BACKGROUND ----------------
            self.screen.fill((5, 6, 10))
            self.draw_stars()
            self.draw_shooting_stars(dt)

            # ---------------- CREDITS ----------------
            current_y = self.scroll_y
            left = True
            spotlight_target = None

            for title, subtitle in self.credits:
                if title:
                    surf = self.font_title.render(title, True, (210, 220, 255))
                    x = 80 if left else self.w - surf.get_width() - 80
                    self.screen.blit(surf, (x, current_y))
                    spotlight_target = surf.get_rect(topleft=(x, current_y)).center
                    current_y += 46

                if subtitle:
                    surf = self.font_text.render(subtitle, True, (160, 190, 255))
                    x = 100 if left else self.w - surf.get_width() - 100
                    self.screen.blit(surf, (x, current_y))
                    spotlight_target = surf.get_rect(topleft=(x, current_y)).center
                    current_y += 32

                current_y += 26
                left = not left

            # ---------------- LIGHTING ----------------
            self.dark_surface.fill((0, 0, 0, 200))
            self.light_surface.fill((0, 0, 0, 0))

            if self.player_img:
                player_pos = (self.w // 2 - 16, int(self.player_y))
                self.screen.blit(self.player_img, player_pos)
                self.draw_radial_light((self.w // 2, int(self.player_y + 16)))

            self.dark_surface.blit(
                self.light_surface,
                (0, 0),
                special_flags=pygame.BLEND_RGBA_SUB
            )
            self.screen.blit(self.dark_surface, (0, 0))

            pygame.display.flip()

        return
