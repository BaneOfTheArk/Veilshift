# platform.py
import pygame
from settings import MASK_INFO

class Platform:
    """Basic platform with optional mask visibility."""
    def __init__(self, rect, visible_masks=None):
        self.rect = pygame.Rect(rect)
        self.visible_masks = visible_masks  # None = always visible

    def visible(self, current_mask):
        """Check if the platform should be visible for the current mask."""
        return self.visible_masks is None or current_mask in self.visible_masks

    def draw(self, surface, current_mask, camera=None):
        """Draw the platform if visible."""
        if not self.visible(current_mask):
            return
        base_color = MASK_INFO[current_mask]["color"]
        # Slightly brighter for visibility
        color = tuple(min(255, c + 20) for c in base_color)

        if camera:
            rect = camera.apply(self.rect)
        else:
            rect = self.rect

        pygame.draw.rect(surface, color, rect, border_radius=4)

class HookPlatform(Platform):
    """Floating ring platform for grappling."""
    def __init__(self, rect, visible_masks=None, radius=16):
        super().__init__(rect, visible_masks)
        self.radius = radius
        self.center = (self.rect.centerx, self.rect.centery)

    def draw(self, surface, current_mask, camera=None):
        """Draw the floating hook ring."""
        # Optional base rectangle (can be invisible)
        # super().draw(surface, current_mask)
        cx, cy = self.center

        if camera:
            cx -= camera.offset.x
            cy -= camera.offset.y

        # Draw inner black ring
        pygame.draw.circle(surface, (0, 0, 0), self.center, self.radius, width=2)

        # Draw outer white ring for grapple proximity feedback
        pygame.draw.circle(surface, (255, 255, 255), self.center, self.radius + 4, width=1)