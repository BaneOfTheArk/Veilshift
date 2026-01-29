# level_handler.py
import pygame
from platform import Platform, HookPlatform

class LevelHandler:
    """
    Ultimate Level Handler
    ---------------------
    - Loads levels from a mega dictionary
    - Builds platforms, hooks, exits, and other objects
    - Adds infinite side walls automatically
    - Supports level transitions and metadata queries
    """

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height

        self.current_level_id = 0
        self.platforms = []
        self.exit_rect = None
        self.extra_objects = []  # For future extendable things

        self.levels = self._define_levels()

    # ---------------- MEGA TABLE ----------------
    def _define_levels(self):
        """Compact, mega table for all levels"""
        return {
            0: {
                "platforms": [
                    # x, y, width, height, visible_masks
                    (0, self.height - 40, self.width, 40, None),  # floor
                    (200, 500, 200, 25, [1]),
                    (500, 400, 180, 25, [1]),
                ],
                "hooks": [
                    # x, y, radius
                    (600, 350, 16),
                ],
                "exit": (self.width - 120, self.height - 80, 80, 80),
            },
            1: {
                "platforms": [
                    (0, self.height - 40, self.width, 40, None),
                    (150, 520, 220, 25, [1]),
                    (450, 430, 200, 25, [1]),
                    (750, 350, 150, 25, [2]),
                ],
                "hooks": [
                    (700, 300, 16),
                ],
                "exit": (self.width - 120, self.height - 80, 80, 80),
            },
        }

    # ---------------- LOAD LEVEL ----------------
    def load_level(self, level_id):
        """Load level by ID and return platforms and exit rect"""
        if level_id not in self.levels:
            raise ValueError(f"Level {level_id} does not exist!")

        self.current_level_id = level_id
        level_data = self.levels[level_id]

        self.platforms = []
        self.extra_objects = []

        # Infinite side walls
        wall_height = 20000
        self.platforms.append(Platform((-50, -wall_height // 2, 50, wall_height)))  # Left wall
        self.platforms.append(Platform((self.width, -wall_height // 2, 50, wall_height)))  # Right wall

        # Platforms
        for x, y, w, h, masks in level_data.get("platforms", []):
            self.platforms.append(Platform((x, y, w, h), visible_masks=masks))

        # Hooks
        for hx, hy, radius in level_data.get("hooks", []):
            self.platforms.append(HookPlatform((hx, hy, 0, 0), radius=radius))

        # Exit
        ex, ey, ew, eh = level_data.get("exit", (self.width - 120, self.height - 80, 80, 80))
        self.exit_rect = pygame.Rect(ex, ey, ew, eh)

        return self.platforms, self.exit_rect

    # ---------------- NEXT LEVEL ----------------
    def next_level(self):
        """Load the next level if it exists"""
        next_id = self.current_level_id + 1
        if next_id in self.levels:
            return self.load_level(next_id)
        return None

    # ---------------- UTILITIES ----------------
    def get_level_metadata(self, level_id=None):
        """Return raw level data for queries"""
        if level_id is None:
            level_id = self.current_level_id
        return self.levels.get(level_id, {})

    def is_player_at_exit(self, player_rect):
        """Check if player has entered the exit door"""
        if self.exit_rect:
            return player_rect.colliderect(self.exit_rect)
        return False

    def draw_exit(self, surface, color=(255, 255, 255)):
        """Draw the exit door for the current level"""
        if self.exit_rect:
            pygame.draw.rect(surface, color, self.exit_rect)
            pygame.draw.rect(surface, (200, 200, 200), self.exit_rect, 2)
