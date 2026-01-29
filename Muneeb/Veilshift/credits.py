# end_credits.py
import pygame
import sys
import random
import math

class EndCredits:
    """
    Cinematic, pixel-styled end credits for Veilshift.
    Features:
    - Pixel fonts with shadows
    - Scrolling text from left or right
    - Small radial spotlight on player
    - Wavy cone spotlight revealing each credit line
    - Particle ambient effect
    """

    def __init__(self, screen, player_img=None):
        self.screen = screen
        self.width, self.height = screen.get_size()

        # ---------------- FONTS ----------------
        self.pixel_font_title = pygame.font.SysFont("Courier", 48, bold=True)
        self.pixel_font_text = pygame.font.SysFont("Courier", 28)
        self.pixel_font_small = pygame.font.SysFont("Courier", 18, italic=True)

        # ---------------- CREDITS CONTENT ----------------
        self.credits = [
            ("VEILSHIFT", "A Game Jam Experience"),
            ("CREATED BY", "Your Name"),
            ("PROGRAMMING & DESIGN", "Your Name"),
            ("ART & VISUALS", "Your Name"),
            ("MUSIC & SOUND", "Composer Name"),
            ("SPECIAL THANKS", "Friends, Mentors, Community"),
            ("POWERED BY", "PYTHON & PYGAME"),
            ("", ""),
            ("THANK YOU FOR PLAYING!", ""),
            ("", ""),
            ("END OF TRANSMISSION", ""),
        ]

        # Randomly assign left/right entry for each credit line
        self.entry_sides = [random.choice([-1, 1]) for _ in self.credits]

        # ---------------- SCROLL ----------------
        self.start_y = self.height
        self.speed = 70
        self.running = True

        # ---------------- BACKGROUND ----------------
        self.bg_surface = pygame.Surface((self.width, self.height))
        self.bg_surface.fill((10, 10, 10))

        # ---------------- PARTICLES ----------------
        self.particles = [
            [random.uniform(0, self.width), random.uniform(0, self.height),
             random.uniform(0.2, 1.0)]
            for _ in range(200)
        ]

        # ---------------- PLAYER SPRITE ----------------
        if player_img:
            if isinstance(player_img, pygame.Surface):
                self.player_img = pygame.transform.scale(player_img, (32, 32))
            else:
                self.player_img = pygame.transform.scale(pygame.image.load(player_img).convert_alpha(), (32, 32))
        else:
            self.player_img = None
        self.player_y = -50  # start above screen

        # ---------------- SPOTLIGHT SURFACES ----------------
        self.spotlight_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.cone_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # ---------------- FADE ----------------
        self.fade_surface = pygame.Surface((self.width, self.height))
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 255
        self.fade_speed = 200

    # ---------------- HELPER FUNCTIONS ----------------
    def draw_pixel_text(self, surf, text, font, color, x, y, shadow=True):
        if shadow:
            shadow_surf = font.render(text, True, (0, 0, 0))
            surf.blit(shadow_surf, (x + 2, y + 2))
        text_surf = font.render(text, True, color)
        surf.blit(text_surf, (x, y))

    def draw_particles(self, surf, dt):
        for p in self.particles:
            x, y, speed = p
            alpha = int(100 + 155 * speed)
            pygame.draw.rect(surf, (150, 150, 255, alpha), (int(x), int(y), 2, 2))
            p[1] += 20 * speed * dt
            if p[1] > self.height:
                p[1] = -2
                p[0] = random.uniform(0, self.width)

    def draw_radial_spotlight(self, surf, player_pos):
        # Small radial light around player
        radius = 80
        self.spotlight_surface.fill((0, 0, 0, 180))  # semi-dark
        if self.player_img:
            px, py = int(player_pos[0]), int(player_pos[1])
            for r in range(radius, 0, -1):
                alpha = int(200 * (r / radius) ** 2)
                pygame.draw.circle(self.spotlight_surface, (255, 255, 255, alpha), (px, py), r)
        surf.blit(self.spotlight_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    def draw_cone_spotlight(self, surf, x, y, width=250, height=60, t=0):
        """
        Draw a wavy cone spotlight onto a credit line.
        x, y: center position of the text
        """
        self.cone_surface.fill((0, 0, 0, 0))
        points = []
        wave_offset = t * 0.005
        for i in range(0, width + 1, 5):
            dx = i - width // 2
            dy = math.sin(i * 0.2 + wave_offset) * 10
            points.append((x + dx, y - height//2 + dy))
        for i in range(width, -1, -5):
            dx = i - width // 2
            dy = math.sin(i * 0.2 + wave_offset + 3) * 10
            points.append((x + dx, y + height//2 + dy))
        pygame.draw.polygon(self.cone_surface, (255, 255, 255, 180), points)
        surf.blit(self.cone_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    # ---------------- MAIN LOOP ----------------
    def run(self):
        clock = pygame.time.Clock()
        y = self.start_y
        t = 0

        while self.running:
            dt = clock.tick(60) / 1000
            t += dt * 1000
            y -= self.speed * dt
            self.player_y += self.speed * dt * 0.2
            player_pos = [self.width // 2, self.player_y]

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            # ---------------- DRAW BACKGROUND ----------------
            self.screen.blit(self.bg_surface, (0, 0))
            self.draw_particles(self.screen, dt)

            # ---------------- DRAW CREDITS ----------------
            current_y = y
            for idx, (title, subtitle) in enumerate(self.credits):
                side = self.entry_sides[idx]
                entry_offset = side * max(0, 300 - (self.height - current_y)/2)  # slide in from left/right
                text_x_center = self.width // 2 + entry_offset

                # Draw wavy cone spotlight on this line
                self.draw_cone_spotlight(self.screen, text_x_center, int(current_y), width=250, height=50, t=t)

                if title:
                    color = (200, 200, 255)
                    x = text_x_center - len(title) * 12
                    self.draw_pixel_text(self.screen, title, self.pixel_font_title, color, x, int(current_y))
                    current_y += 50
                if subtitle:
                    color = (150, 200, 255)
                    x = text_x_center - len(subtitle) * 8
                    self.draw_pixel_text(self.screen, subtitle, self.pixel_font_text, color, x, int(current_y))
                    current_y += 36
                current_y += 10

            # ---------------- PLAYER RADIAL SPOTLIGHT ----------------
            self.draw_radial_spotlight(self.screen, player_pos)

            # ---------------- DRAW PLAYER SPRITE ----------------
            if self.player_img:
                self.screen.blit(self.player_img, (self.width // 2 - 16, int(self.player_y)))

            # ---------------- FADE ----------------
            if y > self.height / 2:
                self.fade_alpha = max(0, self.fade_alpha - self.fade_speed * dt)
            elif current_y < 0:
                self.fade_alpha = min(255, self.fade_alpha + self.fade_speed * dt)

            if self.fade_alpha > 0:
                self.fade_surface.set_alpha(int(self.fade_alpha))
                self.screen.blit(self.fade_surface, (0, 0))

            if current_y < 0 and self.fade_alpha >= 255:
                self.running = False

            pygame.display.flip()
