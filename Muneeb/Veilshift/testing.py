from credits import EndCredits

# main.py
import pygame
import sys
from settings import *
from player import Player
from platform import Platform, HookPlatform
from light_system import LightSystem
from ui import draw_hud
from level_handler import LevelHandler

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
clock = pygame.time.Clock()

credits = EndCredits(screen, pygame.image.load(r"Charlotte\PlayerSprites\PlayerIdleNoMask.png").convert_alpha())
credits.run()