# settings.py
import pygame

# ---------------- SCREEN ----------------
FPS = 60
WIDTH, HEIGHT = 1280, 720

# ---------------- COLORS ----------------
AMBIENT_DARK = (10, 10, 15)

MASK_INFO = {
    0: {"color": (200, 80, 80), "name": "Red - See Enemies (TBA)"},
    1: {"color": (90, 140, 220), "name": "Blue - Platform Visibility"},
    2: {"color": (90, 200, 130), "name": "Green - See/Solve Puzzles"},
}

# ---------------- PLAYER ----------------
CUBE_SIZE = 36
SPEED = 6
ACCEL = 0.9
FRICTION = 0.82
JUMP = 14
GRAVITY = 0.7

# ---------------- FOCUS ----------------
FOCUS_MAX = 100.0
FOCUS_DRAIN = 5.0
FOCUS_REGEN_SLOW = 8.0
FOCUS_REGEN_FAST = 22.0
FOCUS_DEBOUNCE_TIME = 0.6
FOCUS_ACTIVATE_THRESHOLD = 35.0
FOCUS_SLOW_REGEN_THRESHOLD = 40.0

# ---------------- LIGHT ----------------
BASE_RADIUS = 30
BASE_CONE_RADIUS = 140
MAX_CONE_RADIUS = 300
FOV_ANGLE = 90
RAY_COUNT = 50
RAY_STEP = 4

# ---------------- GRAPPLE ----------------
GRAPPLE_MAX_RANGE = 300
GRAPPLE_SPEED = 450