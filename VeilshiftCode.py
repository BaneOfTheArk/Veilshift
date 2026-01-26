import tkinter as tk
from PIL import Image,ImageTk
from pygame import *
from pygame.locals import *
import sys
import pygame
import random
import time
import math

# Canvas surface
canvas = pygame.Surface((1900, 125))

# Create window
window = pygame.display.set_mode((0,0), pygame.FULLSCREEN)

# Background
Stage1 = pygame.image.load('')

# Platforms
Platform1 = pygame.image.load('')

# Name of window
pygame.display.set_caption("")

# Game Icon
GameIcon = pygame.image.load('')
pygame.display.set_icon(GameIcon)

# Player
PlayerIdleR = pygame.image.load('')
PlayerRunR  = pygame.image.load('')

# Load run-left frames, then flip them
PlayerIdleL = pygame.image.load('')
PlayerRunL = pygame.image.load('')
# PlayerRunL = pygame.transform.flip(PlayerRunL_raw, True, False)

# Jump
PlayerJumpingR = pygame.image.load('')
PlayerJumpingL = pygame.image.load('')
PlayerFallingR = pygame.image.load('')
PlayerFallingL = pygame.image.load('')

# Player Weapons
PlayerAttack = pygame.image.load('')

# Enemy Sprites
Enemy1 = pygame.image.load('')

# Enemy Weapons
EnemyBullet1 = pygame.image.load('')

# Current sprite the player is using
current_player_sprite = PlayerIdleR

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = PlayerIdleR
        self.rect = self.image.get_rect()
        self.rect.x = 70
        self.rect.y = 990

        self.mask = pygame.mask.from_surface(self.image)

        # movement flags
        self.LEFT_KEY = False
        self.RIGHT_KEY = False
        self.FACING_LEFT = False

        # physics
        self.gravity = .35
        self.friction = -.12
        self.position = pygame.math.Vector2(self.rect.x, self.rect.y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, self.gravity)

        self.grounded = False

    def drawPlayer(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

    def update(self, dt, platform):
        self.horizontal_movement(dt)
        self.vertical_movement(dt, platform)
        self.update_sprite()

    # horizontal movement
    def horizontal_movement(self, dt):
        self.acceleration.x = 0

        if self.LEFT_KEY:
            self.acceleration.x -= .75
        if self.RIGHT_KEY:
            self.acceleration.x += .75

        self.acceleration.x += self.velocity.x * self.friction
        self.velocity.x += self.acceleration.x * dt
        self.limit_velocity(15)

        self.position.x += self.velocity.x * dt
        self.rect.x = self.position.x

    # vertical movement
    def vertical_movement(self, dt, platform):
        self.grounded = False

        if not self.grounded:
            self.velocity.y += self.acceleration.y * dt

        # limit falling speed
        if self.velocity.y > 10:
            self.velocity.y = 10

        self.position.y += self.velocity.y * dt

        ground_y = window.get_height() - self.rect.height
        platform_y = window.get_height() - self.rect.height

        # ground collision
        if self.position.y > ground_y:
            self.position.y = ground_y
            self.velocity.y = 0
            self.grounded = True

        self.rect.y = self.position.y

        # Platform collision
        offset = (platform.rect.x - self.rect.x, platform.rect.y - self.rect.y)

        if (
            self.rect.right > platform.hitbox.left and
            self.rect.left < platform.hitbox.right and
            self.rect.bottom >= platform.hitbox.top and
            self.rect.bottom - self.velocity.y * dt <= platform.hitbox.top and
            self.velocity.y >= 0
        ):
            self.rect.bottom = platform.hitbox.top
            self.position.y = self.rect.y
            self.velocity.y = 0
            self.grounded = True

    def limit_velocity(self, max_vel):
        self.velocity.x = max(-max_vel, min(self.velocity.x, max_vel))
        if abs(self.velocity.x) < 0.01:
            self.velocity.x = 0

    def jump(self):
        if self.grounded:
            self.velocity.y = -15
            self.grounded = False

    def update_sprite(self):

        self.mask = pygame.mask.from_surface(self.image)

        if self.velocity.y > 0.1 and not (self.grounded):
            if self.FACING_LEFT:
                self.image = PlayerJumpingL
            else:
                self.image = PlayerJumpingR
            return

        if self.velocity.y > 0.1 and not (self.grounded):
            if self.FACING_LEFT:
                self.image = PlayerFallingL
            else:
                self.image = PlayerFallingR
            return

    # Running
        if self.velocity.x > 0.1:       # moving right
            self.image = PlayerRunR
            self.FACING_LEFT = False
            return
        
        elif self.velocity.x < -0.1:    # moving left
            self.image = PlayerRunL
            self.FACING_LEFT = True
            return

        # Idle
        else:
            if self.FACING_LEFT:
                self.image = PlayerIdleL
            else:
                self.image = PlayerIdleR

window = pygame.display.set_mode((1920, 1020))
canvas = pygame.Surface((1900, 125))

class Platform(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.Pimage = Platform1

        self.rect = self.Pimage.get_rect()
        self.rect.x = 100
        self.rect.y = 800

        self.hitbox = pygame.Rect(self.rect.x, self.rect.y + 30, self.rect.width, 8)

    def update(self):
        self.hitbox.x = self.rect.x
        self.hitbox.y = self.rect.y + 30

    def drawPlatform(self, surface):
        surface.blit(self.Pimage, (self.rect.x, self.rect.y))
        pygame.draw.rect(window, (255, 0, 0), platform.hitbox, 1)

player = Player()
platform = Platform()

clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(60) * 0.001 * 60

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                player.LEFT_KEY = True
            if event.key == pygame.K_d:
                player.RIGHT_KEY = True
            if event.key == pygame.K_w:
                player.jump()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                player.LEFT_KEY = False
            if event.key == pygame.K_d:
                player.RIGHT_KEY = False

    player.update(dt, platform)

    window.fill((0, 0, 0))
    window.blit(Stage1, (0,0))
    platform.drawPlatform(window)
    player.drawPlayer(window)

    pygame.display.update()

pygame.quit()