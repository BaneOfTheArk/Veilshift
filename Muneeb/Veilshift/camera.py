# camera.py
import pygame

class Camera:
    def __init__(self, width, height):
        self.offset = pygame.Vector2(0, 0)
        self.width = width
        self.height = height

    def update(self, target_rect):
        # Center camera on player
        self.offset.x = target_rect.centerx - self.width // 2
        self.offset.y = target_rect.centery - self.height // 2

        # Clamp vertically (optional, tweak later)
        self.offset.y = max(self.offset.y, 0)

    def apply(self, rect):
        return rect.move(-self.offset.x, -self.offset.y)
