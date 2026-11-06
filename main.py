import pygame
import os
import math
import random
from pygame.locals import *
import time
import json
from datetime import datetime
import sys
from collections import deque
from move import (
    ALGORITHM_KEYS,
    draw_path,
    get_algorithm_display_name,
    normalize_algorithm_key,
    update_monster_movement,
)

pygame.init()
pygame.mixer.init()

info = pygame.display.Info()
DISPLAY_WIDTH = info.current_w
DISPLAY_HEIGHT = info.current_h
GAME_WIDTH = 1280
GAME_HEIGHT = 720
SCREEN_WIDTH = GAME_WIDTH
SCREEN_HEIGHT = GAME_HEIGHT
WORLD_WIDTH = 5000
WORLD_HEIGHT = 5000

is_fullscreen = False
DISPLAY_WIDTH = GAME_WIDTH
DISPLAY_HEIGHT = GAME_HEIGHT
screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("GI Survival")
game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT)).convert()
CAMERA_X = 0.0
CAMERA_Y = 0.0

viewport_scale = 1.0
viewport_width = GAME_WIDTH
viewport_height = GAME_HEIGHT
viewport_x = 0
viewport_y = 0


def update_viewport():
    global viewport_scale, viewport_width, viewport_height, viewport_x, viewport_y
    viewport_scale = min(DISPLAY_WIDTH / GAME_WIDTH, DISPLAY_HEIGHT / GAME_HEIGHT)
    viewport_width = int(GAME_WIDTH * viewport_scale)
    viewport_height = int(GAME_HEIGHT * viewport_scale)
    viewport_x = (DISPLAY_WIDTH - viewport_width) // 2
    viewport_y = (DISPLAY_HEIGHT - viewport_height) // 2


def to_virtual_pos(screen_pos):
    x = int((screen_pos[0] - viewport_x) / viewport_scale)
    y = int((screen_pos[1] - viewport_y) / viewport_scale)
    x = max(0, min(GAME_WIDTH - 1, x))
    y = max(0, min(GAME_HEIGHT - 1, y))
    return x, y


def get_virtual_mouse_pos():
    return to_virtual_pos(pygame.mouse.get_pos())


def world_to_screen(x, y):
    return int(x - CAMERA_X), int(y - CAMERA_Y)


def get_world_mouse_pos():
    vx, vy = to_virtual_pos(pygame.mouse.get_pos())
    return int(vx + CAMERA_X), int(vy + CAMERA_Y)


def toggle_fullscreen():
    global is_fullscreen, screen, DISPLAY_WIDTH, DISPLAY_HEIGHT
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        info_local = pygame.display.Info()
        DISPLAY_WIDTH = info_local.current_w
        DISPLAY_HEIGHT = info_local.current_h
        screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN)
    else:
        DISPLAY_WIDTH = GAME_WIDTH
        DISPLAY_HEIGHT = GAME_HEIGHT
        screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    update_viewport()


def present_frame():
    screen.fill(BLACK)
    if viewport_width == GAME_WIDTH and viewport_height == GAME_HEIGHT:
        screen.blit(game_surface, (viewport_x, viewport_y))
    else:
        scaled_surface = pygame.transform.smoothscale(game_surface, (viewport_width, viewport_height))
        screen.blit(scaled_surface, (viewport_x, viewport_y))
    pygame.display.flip()

if os.path.exists('icons/logo.png'):
    app_icon = pygame.image.load('icons/logo.png')
    pygame.display.set_icon(app_icon)

gold_icon = None
if os.path.exists('icons/gold.png'):
    gold_icon = pygame.image.load('icons/gold.png').convert_alpha()
    gold_icon = pygame.transform.scale(gold_icon, (24, 24))

custom_cursor = None
if os.path.exists('images/chuot.png'):
    custom_cursor = pygame.image.load('images/chuot.png').convert_alpha()
    custom_cursor = pygame.transform.scale(custom_cursor, (32, 32))
    pygame.mouse.set_visible(False)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
HIGHLIGHT = (200, 200, 200)
FIELD_COLOR = (50, 50, 50)
BORDER_COLOR = (150, 150, 150)
GOLD_COLOR = (255, 215, 0)
LEVEL_COLOR = (0, 255, 0)
TIMER_COLOR = (255, 255, 255)
DEAD_COLOR = (255, 0, 0)
XP_COLOR = (0, 191, 255)
STATS_COLOR = (200, 200, 200)

COLLECTABLE_SIZE = 32
COLLECTABLE_ANIMATION_SPEED = 0.1
COIN_VALUE = 10
XP_ORB_VALUE = 10

font_path = 'fonts/roboto.ttf'
font = pygame.font.Font(font_path, 60)  
small_font = pygame.font.Font(font_path, 28)  
status_font = pygame.font.Font(font_path, 18) 
player_name_font = pygame.font.Font(font_path, 24)  
timer_font = pygame.font.Font(font_path, 36)    
respawn_font = pygame.font.Font(font_path, 28) 
stats_font = pygame.font.Font(font_path, 16) 

STATUS_BAR_HEIGHT = 0
FIELD_PADDING = 0
FIELD_WIDTH = WORLD_WIDTH
FIELD_HEIGHT = WORLD_HEIGHT
FIELD_X = 0
FIELD_Y = 0

tile = pygame.image.load('sprites/nen/nen2.png').convert_alpha()
TILE_SIZE = tile.get_width()

TREE_COUNT = 20
TREE_MIN_DISTANCE_FROM_SPAWN = 180
MIN_TREE_DISTANCE = 120
TREE_PADDING = 24
TREE_COLLISION_SCALE = 0.2
TREE_VARIATION_SCALE = (0.7, 1.0)
CAMERA_LERP = 0.1
CAMERA_DEADZONE = 40

tree_sprites = []
for tree_file in [
    "sprites/tree/Moss_tree2.png",
    "sprites/tree/Burned_tree2.png",
    "sprites/tree/Broken_tree2.png",
]:
    if os.path.exists(tree_file):
        tree_sprites.append(pygame.image.load(tree_file).convert_alpha())


def collides_with_obstacles(rect, obstacles):
    for obstacle in obstacles:
        if rect.colliderect(obstacle):
            return True
    return False

MONSTER_SPAWN_RATE = 1
MONSTER_SPAWN_DISTANCE = 200
MAX_MONSTERS = 100
MONSTER_BASE_HEALTH = 1
MONSTER_HEALTH_INCREASE_PER_MINUTE = 1
SLIME2_SPAWN_RATE = 10
SLIME2_BASE_HEALTH = 2
SLIME2_HEALTH_INCREASE_PER_MINUTE = 5
SLIME3_SPAWN_RATE = 60
SLIME3_BASE_HEALTH = 10
SLIME3_HEALTH_INCREASE_PER_MINUTE = 10

PROJECTILE_SPEED = 10
PROJECTILE_RANGE = 300
SHOOT_COOLDOWN = 0.8
SHOOT_RANGE = 200

BASE_RESPAWN_TIME = 5
RESPAWN_TIME_INCREASE_PER_MINUTE = 1

BASE_XP_REQUIRED = 100
XP_SCALING_FACTOR = 1.5
REGENERATION_INTERVAL = 10

UPGRADES = {
    'damage': {'name': 'Damage', 'description': 'Increase damage by 1', 'base_cost': 100, 'cost_factor': 1.15, 'key1': K_1, 'key2': K_KP1},
    'health': {'name': 'Health', 'description': 'Increase max health by 1', 'base_cost': 100, 'cost_factor': 1.15, 'key1': K_2, 'key2': K_KP2},
    'speed': {'name': 'Speed', 'description': 'Increase movement speed by 10%', 'base_cost': 100, 'cost_factor': 1.15, 'key1': K_3, 'key2': K_KP3},
    'range': {'name': 'Range', 'description': 'Increase attack range by 10%', 'base_cost': 100, 'cost_factor': 1.15, 'key1': K_4, 'key2': K_KP4},
    'attack_speed': {'name': 'Attack Speed', 'description': 'Increase attack speed by 10%', 'base_cost': 100, 'cost_factor': 1.15, 'key1': K_5, 'key2': K_KP5},
    'gold_income': {'name': 'Gold Income', 'description': 'Increase gold income by 10%', 'base_cost': 100, 'cost_factor': 1.15, 'key1': K_6, 'key2': K_KP6},
    'xp_income': {'name': 'XP Income', 'description': 'Increase XP income by 10%', 'base_cost': 100, 'cost_factor': 1.15, 'key1': K_7, 'key2': K_KP7},
    'pickup_radius': {'name': 'Pickup Radius', 'description': 'Increase collectable pickup range by 50%', 'base_cost': 100, 'cost_factor': 1.15, 'key1': K_8, 'key2': K_KP8},
    'critical_rate': {'name': 'Critical Rate', 'description': 'Increase critical hit chance by 4%', 'base_cost': 100, 'cost_factor': 1.15, 'key1': K_9, 'key2': K_KP9}
}

clock = pygame.time.Clock()
FPS = 60

UI_BG_COLOR = (255, 253, 240)
UI_BG_ALPHA = 180
SHOW_PATH_DEBUG = False

SLIME_TYPES = ["slime1", "slime2", "slime3"]
SLIME_LABELS = {
    "slime1": "Slime1",
    "slime2": "Slime2",
    "slime3": "Slime3",
}

ARENA_ALGORITHMS = ["direct", "astar", "bfs"]
ARENA_ALGO_COLORS = {
    "direct": (255, 220, 0),
    "astar": (255, 80, 80),
    "bfs": (80, 170, 255),
    "dijkstra": (180, 90, 255),
    "greedy": (90, 220, 120),
    "hill_climbing": (255, 120, 180),
}
ARENA_ZONE_COUNT = 3
ARENA_MONSTERS_PER_ZONE = 6
ARENA_REPLAY_SECONDS = 8.0
ARENA_REPLAY_FPS = 20.0
ARENA_BASE_RECT = pygame.Rect(WORLD_WIDTH // 2 - 1200, WORLD_HEIGHT // 2 - 780, 2400, 1560)
ARENA_SLOW_MOTION_LEVELS = [1.0, 0.5, 0.25]

update_viewport()

class ArenaTarget:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.sprite_width = 24
        self.sprite_height = 24
        self.scale_factor = 1.0
        self.is_dead = False
        self.health = 999999
        self.max_health = 999999
        self.label = "Muc tieu"

class Button:
    def __init__(self, x, y, width, height, text, color=GRAY, highlight_color=HIGHLIGHT):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.highlight_color = highlight_color
        self.is_hovered = False
        self.is_enabled = True
        
    def draw(self, surface):
        if self.is_enabled:
            color = self.highlight_color if self.is_hovered else self.color
        else:
            color = (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)
        
        text_surf = small_font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos) and self.is_enabled
        return self.is_hovered
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click and self.is_enabled

class Projectile:
    def __init__(self, x, y, target_x, target_y, damage, crit_chance=0.05, bullet_sprite=None, slow_effect=False):
        self.original_sprite = bullet_sprite if bullet_sprite else pygame.image.load('sprites/bullets/1.png').convert_alpha()
        
        dx = target_x - x
        dy = target_y - y
        self.angle = math.degrees(math.atan2(dy, dx))
        
        self.sprite = pygame.transform.rotate(self.original_sprite, -self.angle)
        
        self.x = x
        self.y = y
        self.distance_traveled = 0
        self.damage = damage
        self.crit_chance = crit_chance
        self.is_crit = random.random() < self.crit_chance
        
     
        self.slow_effect = slow_effect
        self.slow_duration = 1.0  
        self.slow_factor = 0.5   
        
        self.hit_monsters = []
        
        length = math.sqrt(dx * dx + dy * dy)
        self.dx = (dx / length) * PROJECTILE_SPEED
        self.dy = (dy / length) * PROJECTILE_SPEED
        
        self.radius = 12
        
    def update(self, dt, monsters):
        self.x += self.dx
        self.y += self.dy
        
        self.distance_traveled += math.sqrt(self.dx * self.dx + self.dy * self.dy)
        
        for monster in monsters:
            if monster in self.hit_monsters:
                continue
                
            dx = (monster.x + monster.sprite_width * monster.scale_factor / 2) - self.x
            dy = (monster.y + monster.sprite_height * monster.scale_factor / 2) - self.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < monster.radius + self.radius:
                actual_damage = self.damage * 2 if self.is_crit else self.damage
                monster.take_damage(actual_damage, self.is_crit)
                
                
                if self.slow_effect:
                    monster.apply_slow_effect(self.slow_factor, self.slow_duration)
                    
                self.hit_monsters.append(monster)
        
        return self.distance_traveled < PROJECTILE_RANGE
        
    def draw(self, surface):
        sprite_width = self.sprite.get_width()
        sprite_height = self.sprite.get_height()
        draw_x, draw_y = world_to_screen(self.x - sprite_width / 2, self.y - sprite_height / 2)
        surface.blit(self.sprite, (draw_x, draw_y))

class Player:
    def __init__(self, x, y, controls, name, hero_data):
        self.sprite_sheet = pygame.image.load(hero_data['sprite_path']).convert_alpha()
        self.sprite_config = hero_data['sprite_config']
        
        self.name = name
        self.level = 1
        self.xp = 0
        self.xp_required = 100
        self.gold = 00
        self.max_health = 10
        self.health = self.max_health
        
        self.total_gold_received = 0
        self.total_xp_collected = 0
        
        self.upgrade_sound = pygame.mixer.Sound('sounds/upgrade.mp3')
        self.upgrade_sound.set_volume(0.5)
        self.shoot_sound = pygame.mixer.Sound('sounds/shoot.mp3')
        self.shoot_sound.set_volume(0.5)
        
        self.damage = 1
        self.attack_range = 200
        self.crit_chance = 0.05
        self.dodge_chance = 0.05
        self.attack_speed = 1.0
        self.speed = 5
        
        self.gold_multiplier = 1.0
        self.xp_multiplier = 1.0
        
        self.pickup_radius = 1.0
        
        self.last_regen_time = 0
        
        self.sprite_width = 64
        self.sprite_height = 64
        self.columns = 8
        self.rows = 4
        
        self.scale_factor = 2
        
        self.current_frame = 0
        self.animation_speed = 0.2
        self.animation_timer = 0
        self.direction = 0
        
        self.x = x
        self.y = y
        self.controls = controls
        
        self.projectiles = []
        self.last_shot_time = 0
        self.bullet_sprite = pygame.image.load(hero_data['bullet_path']).convert_alpha()
        
        self.is_dead = False
        self.death_time = 0
        self.respawn_time = 0
        
        self.frames = []
        self.load_frames()
        
        self.upgrade_levels = {
            'damage': 0,
            'health': 0,
            'speed': 0,
            'range': 0,
            'attack_speed': 0,
            'gold_income': 0,
            'xp_income': 0,
            'pickup_radius': 0,
            'critical_rate': 0
        }
        
        self.bought_items = []
        self.bought_bullets = []
        
        self.hero_type = hero_data.get('name', 'Paimon')
        
        self.attack_sprite_sheet = None
        self.attack_frames = []
        self.is_attacking = False
        self.attack_frame = 0
        self.attack_animation_speed = 0.02
        self.attack_animation_timer = 0
        if self.hero_type == 'Hutao':
            self.attack_sprite_sheet = pygame.image.load('sprites/Hutao/attack.png').convert_alpha()
            self.load_attack_frames()
        
    def load_frames(self):
        for row in range(self.rows):
            for col in range(self.columns):
                frame = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
                frame.blit(self.sprite_sheet, (0, 0), 
                          (col * self.sprite_width, 
                           row * self.sprite_height, 
                           self.sprite_width, 
                           self.sprite_height))
                frame = pygame.transform.scale(frame, 
                                             (self.sprite_width * self.scale_factor, 
                                              self.sprite_height * self.scale_factor))
                self.frames.append(frame)
    
    def load_attack_frames(self):
        if not self.attack_sprite_sheet:
            return
            
        for row in range(4):
            for col in range(8):
                frame = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
                frame.blit(self.attack_sprite_sheet, (0, 0), 
                          (col * self.sprite_width, 
                           row * self.sprite_height, 
                           self.sprite_width, 
                           self.sprite_height))
                frame = pygame.transform.scale(frame, 
                                            (self.sprite_width * self.scale_factor, 
                                             self.sprite_height * self.scale_factor))
                self.attack_frames.append(frame)
    
    def gain_xp(self, amount):
        amount = int(amount * self.xp_multiplier)
        self.xp += amount
        self.total_xp_collected += amount
        if self.xp >= self.xp_required:
            self.level_up()
            return True
        return False
        
    def level_up(self):
        self.level += 1
        self.xp = 0
        self.xp_required = int(100 * (XP_SCALING_FACTOR ** (self.level - 1)))
        self.health = self.max_health
        return True
        
    def get_upgrade_cost(self, upgrade_type):
        if upgrade_type in UPGRADES:
            base_cost = UPGRADES[upgrade_type]['base_cost']
            cost_factor = UPGRADES[upgrade_type]['cost_factor']
            current_level = self.upgrade_levels[upgrade_type]
            return int(base_cost * (cost_factor ** current_level))
        return 0
    
    def can_upgrade(self, upgrade_type):
        if upgrade_type not in UPGRADES:
            return False
            
        if self.upgrade_levels[upgrade_type] >= self.level:
            return False
            
        return self.gold >= self.get_upgrade_cost(upgrade_type)
    
    def apply_upgrade(self, upgrade_type):
        if not self.can_upgrade(upgrade_type):
            return False
        
        self.gold -= self.get_upgrade_cost(upgrade_type)
        self.upgrade_levels[upgrade_type] += 1
        
        if upgrade_type == 'damage':
            self.damage += 1
        elif upgrade_type == 'health':
            self.max_health += 1
            self.health = min(self.health + 1, self.max_health)
        elif upgrade_type == 'speed':
            self.speed *= 1.08
        elif upgrade_type == 'range':
            self.attack_range *= 1.1
        elif upgrade_type == 'attack_speed':
            self.attack_speed *= 1.07
        elif upgrade_type == 'gold_income':
            self.gold_multiplier = 1.0 + (0.1 * self.upgrade_levels['gold_income'])
        elif upgrade_type == 'xp_income':
            self.xp_multiplier *= 1.1
        elif upgrade_type == 'pickup_radius':
            self.pickup_radius += 1.0
        elif upgrade_type == 'critical_rate':
            self.crit_chance += 0.05
        
        self.upgrade_sound.play()
        return True

    def update(self, dt, monsters, current_time, other_player=None):
        if self.is_dead:
            if other_player and not other_player.is_dead:
                minutes_played = current_time / 60
                respawn_delay = BASE_RESPAWN_TIME + int(minutes_played * RESPAWN_TIME_INCREASE_PER_MINUTE)
                
                if current_time - self.death_time >= respawn_delay:
                    self.x = other_player.x
                    self.y = other_player.y
                    self.health = self.max_health
                    self.is_dead = False
                    self.death_time = 0
                    self.respawn_time = 0
            return
            
        regen_interval = max(1, 10 - (0.25 * self.level))
        if current_time - self.last_regen_time >= regen_interval:
            self.health = min(self.health + 1, self.max_health)
            self.last_regen_time = current_time
            
        keys = pygame.key.get_pressed()
        
        dx, dy = 0, 0
        
        if keys[self.controls['up']]:
            dy -= self.speed
            self.direction = self.sprite_config['up_row']
        if keys[self.controls['down']]:
            dy += self.speed
            self.direction = self.sprite_config['down_row']
        if keys[self.controls['left']]:
            dx -= self.speed
            self.direction = self.sprite_config['left_row']
        if keys[self.controls['right']]:
            dx += self.speed
            self.direction = self.sprite_config['right_row']
            
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
            
        new_x = self.x + dx
        new_y = self.y + dy
        
        sprite_width = self.sprite_width * self.scale_factor
        sprite_height = self.sprite_height * self.scale_factor
        
        overlap = 0.5
        obstacles = getattr(self, "environment_obstacles", [])

        clamped_x = max(FIELD_X - sprite_width * overlap, min(FIELD_X + FIELD_WIDTH - sprite_width * (1 - overlap), new_x))
        clamped_y = max(FIELD_Y - sprite_height * overlap, min(FIELD_Y + FIELD_HEIGHT - sprite_height * (1 - overlap), self.y))
        proposed_rect_x = pygame.Rect(int(clamped_x), int(clamped_y), int(sprite_width), int(sprite_height))
        if not collides_with_obstacles(proposed_rect_x, obstacles):
            self.x = clamped_x

        clamped_x = max(FIELD_X - sprite_width * overlap, min(FIELD_X + FIELD_WIDTH - sprite_width * (1 - overlap), self.x))
        clamped_y = max(FIELD_Y - sprite_height * overlap, min(FIELD_Y + FIELD_HEIGHT - sprite_height * (1 - overlap), new_y))
        proposed_rect_y = pygame.Rect(int(clamped_x), int(clamped_y), int(sprite_width), int(sprite_height))
        if not collides_with_obstacles(proposed_rect_y, obstacles):
            self.y = clamped_y
        
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % self.columns
            
        if self.is_attacking:
            self.attack_animation_timer += dt
            if self.attack_animation_timer >= self.attack_animation_speed:
                self.attack_animation_timer = 0
                self.attack_frame += 1
                if self.attack_frame >= 8:
                    self.attack_frame = 0
                    self.is_attacking = False
        
        nearest_monster = None
        nearest_distance = float('inf')
        
        for monster in monsters:
            if monster.is_dead:
                continue
                
            monster_center_x = monster.x + (monster.sprite_width * monster.scale_factor / 2)
            monster_center_y = monster.y + (monster.sprite_height * monster.scale_factor / 2)
            player_center_x = self.x + (self.sprite_width * self.scale_factor) / 2
            player_center_y = self.y + (self.sprite_height * self.scale_factor) / 2
            
            dx = monster_center_x - player_center_x
            dy = monster_center_y - player_center_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_monster = monster
                
        if nearest_monster and nearest_distance <= self.attack_range:
            if current_time - self.last_shot_time >= SHOOT_COOLDOWN / self.attack_speed:
                spawn_x = self.x + (self.sprite_width * self.scale_factor) / 2
                spawn_y = self.y + (self.sprite_height * self.scale_factor) / 2
                
                target_x = nearest_monster.x + (nearest_monster.sprite_width * nearest_monster.scale_factor) / 2
                target_y = nearest_monster.y + (nearest_monster.sprite_height * nearest_monster.scale_factor) / 2
                
                is_crit = random.random() < self.crit_chance
                damage = self.damage * (2 if is_crit else 1)
                
                self.shoot_sound.play()
                
                if self.hero_type == 'Hutao':
                    self.is_attacking = True
                    self.attack_frame = 0
                    self.attack_animation_timer = 0
                
             
                slow_effect = self.hero_type == 'Furina'
                
                self.projectiles.append(Projectile(spawn_x, spawn_y, target_x, target_y, damage, 
                                                 self.crit_chance, self.bullet_sprite, slow_effect))
                self.last_shot_time = current_time
        
        for projectile in self.projectiles[:]:
            if not projectile.update(dt, monsters):
                self.projectiles.remove(projectile)
    
    def draw_health_bar(self, surface):
        bar_width = (self.sprite_width * self.scale_factor) * 0.75
        bar_height = 6
        draw_x, draw_y = world_to_screen(self.x, self.y)
        bar_x = draw_x + (self.sprite_width * self.scale_factor - bar_width) // 2
        bar_y = draw_y - 4
        
        pygame.draw.rect(surface, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        max_visible_blocks = 20
        if self.max_health > max_visible_blocks:
            health_per_block = self.max_health / max_visible_blocks
            current_health = self.health
            block_width = bar_width / max_visible_blocks
            separator_width = 1
            
            for i in range(max_visible_blocks):
                block_x = bar_x + (i * block_width)
                block_health = min(health_per_block, current_health)
                if block_health > 0:
                    green_width = (block_health / health_per_block) * (block_width - separator_width)
                    pygame.draw.rect(surface, (0, 255, 0), (block_x, bar_y, green_width, bar_height))
                current_health -= block_health
                
                if i < max_visible_blocks - 1:
                    separator_x = block_x + block_width - separator_width
                    pygame.draw.rect(surface, (200, 200, 200), (separator_x, bar_y, separator_width, bar_height))
        else:
            block_width = bar_width / self.max_health
            separator_width = 1
            block_width_with_spacing = block_width - separator_width
            
            health_int = int(self.health)
            for i in range(health_int):
                block_x = bar_x + (i * block_width)
                pygame.draw.rect(surface, (0, 255, 0), (block_x, bar_y, block_width_with_spacing, bar_height))
            
            for i in range(1, self.max_health):
                separator_x = bar_x + (i * block_width) - separator_width // 2
                pygame.draw.rect(surface, (200, 200, 200), (separator_x, bar_y, separator_width, bar_height))
        
        pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)
    
    def draw_xp_bar(self, surface):
        bar_width = (self.sprite_width * self.scale_factor) * 0.75
        bar_height = 6
        draw_x, draw_y = world_to_screen(self.x, self.y)
        bar_x = draw_x + (self.sprite_width * self.scale_factor - bar_width) // 2
        bar_y = draw_y - 18
        
        pygame.draw.rect(surface, GRAY, (bar_x, bar_y, bar_width, bar_height))
        
        xp_percentage = self.xp / self.xp_required
        
        if xp_percentage > 0:
            xp_width = int(bar_width * xp_percentage)
            pygame.draw.rect(surface, XP_COLOR, (bar_x, bar_y, xp_width, bar_height))
            
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)
        
    def draw_stats(self, surface, x, y, width):
        stats = [
            f"Level: {self.level}",
            f"XP: {self.xp}/{self.xp_required}",
            f"Damage: {self.damage}",
            f"Health: {self.health}/{self.max_health}",
            f"Range: {int(self.attack_range)}",
            f"Crit: {int(self.crit_chance * 100)}%",
            f"Dodge: {int(self.dodge_chance * 100)}%",
            f"Regen: {self.regeneration}/10s",
            f"Attack Speed: {int(self.attack_speed * 100)}%",
            f"Move Speed: {int(self.speed)}"
        ]
        
        for i, stat in enumerate(stats):
            stat_surf = stats_font.render(stat, True, STATS_COLOR)
            stat_rect = stat_surf.get_rect(topleft=(x, y + i * 20))
            surface.blit(stat_surf, stat_rect)
            
    def draw_name_and_level(self, surface):
        level_surf = status_font.render(f"Level: {self.level}", True, BLACK)
        draw_x, draw_y = world_to_screen(self.x, self.y)
        level_rect = level_surf.get_rect(center=(draw_x + (self.sprite_width * self.scale_factor) // 2, draw_y - 30))
        surface.blit(level_surf, level_rect)
        
    def draw(self, surface):
        self.draw_health_bar(surface)
        self.draw_xp_bar(surface)
        
        if self.is_attacking and self.hero_type == 'Hutao':
            frame_index = self.sprite_config[f"{['down', 'up', 'left', 'right'][self.direction]}_row"] * 8 + self.attack_frame
            current_sprite = self.attack_frames[frame_index]
        else:
            frame_index = self.direction * self.columns + self.current_frame
            current_sprite = self.frames[frame_index]
        
        if self.is_dead:
            dead_sprite = current_sprite.copy()
            dead_sprite.fill((255, 0, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
            draw_x, draw_y = world_to_screen(self.x, self.y)
            surface.blit(dead_sprite, (draw_x, draw_y))
        else:
            draw_x, draw_y = world_to_screen(self.x, self.y)
            surface.blit(current_sprite, (draw_x, draw_y))
        
        self.draw_name_and_level(surface)
        
        for projectile in self.projectiles:
            projectile.draw(surface)
    
    def draw_respawn_timer(self, surface, current_time):
        if not self.is_dead:
            return
            
        minutes_played = current_time / 60
        respawn_delay = BASE_RESPAWN_TIME + int(minutes_played * RESPAWN_TIME_INCREASE_PER_MINUTE)
        time_left = respawn_delay - (current_time - self.death_time)
        
        if time_left <= 0:
            return
            
        timer_text = respawn_font.render(f"Hồi sinh sau: {int(time_left)}s", True, DEAD_COLOR)
        draw_x, draw_y = world_to_screen(self.x, self.y)
        timer_rect = timer_text.get_rect(center=(draw_x + (self.sprite_width * self.scale_factor) // 2, 
                                               draw_y - 50))
        surface.blit(timer_text, timer_rect)
        
        bar_width = self.sprite_width * self.scale_factor
        bar_height = 6
        bar_x = draw_x
        bar_y = draw_y - 40
        
        pygame.draw.rect(surface, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        progress = 1 - (time_left / respawn_delay)
        progress_width = int(bar_width * progress)
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, progress_width, bar_height))
        
        pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)

class MonsterType:
    def __init__(self, name, folder, base_health, health_increase_per_minute, spawn_rate):
        self.name = name
        self.folder = folder
        self.base_health = base_health
        self.health_increase_per_minute = health_increase_per_minute
        self.spawn_rate = spawn_rate

MONSTER_TYPES = {
    'slime1': MonsterType('Slime1', 'slime1', MONSTER_BASE_HEALTH, MONSTER_HEALTH_INCREASE_PER_MINUTE, MONSTER_SPAWN_RATE),
    'slime2': MonsterType('Slime2', 'slime2', SLIME2_BASE_HEALTH, SLIME2_HEALTH_INCREASE_PER_MINUTE, SLIME2_SPAWN_RATE),
    'slime3': MonsterType('Slime3', 'slime3', SLIME3_BASE_HEALTH, SLIME3_HEALTH_INCREASE_PER_MINUTE, SLIME3_SPAWN_RATE)
}

class Monster:
    def __init__(self, x, y, target, game_time, monster_type='slime1'):
        self.monster_type = monster_type
        self.type_data = MONSTER_TYPES[monster_type]
        
        if monster_type == 'slime3':
            self.attack_range = 120
        else:
            self.attack_range = 8
        
        self.run_sprite_sheet = pygame.image.load(f'sprites/monster/{self.type_data.folder}/run/run_anim.png').convert_alpha()
        self.attack_sprite_sheet = pygame.image.load(f'sprites/monster/{self.type_data.folder}/Attack/attack_anim.png').convert_alpha()
        self.hurt_sprite_sheet = pygame.image.load(f'sprites/monster/{self.type_data.folder}/Hurt/hurt_anim.png').convert_alpha()
        
        self.hit_sound = pygame.mixer.Sound('sounds/hit.mp3')
        self.hit_sound.set_volume(0.5)
        
        self.x = x
        self.y = y
        self.target = target
        
        self.base_speed = 2
        
        if monster_type == 'slime1':
            self.speed = self.base_speed
            self.damage = 1
            self.heal_rate = 0
        elif monster_type == 'slime2':
            self.speed = self.base_speed * 1.5
            self.damage = 2
            self.heal_rate = 0
        elif monster_type == 'slime3':
            self.speed = self.base_speed * 1.25
            self.damage = 2
            self.heal_rate = int(game_time / 60)
        
        self.original_speed = self.speed
        self.is_slowed = False
        self.slow_effect_end_time = 0
        
        minutes_played = game_time / 60
        self.health = self.type_data.base_health + int(minutes_played * self.type_data.health_increase_per_minute)
        self.max_health = self.health
        
        self.radius = 32
        self.max_overlap = 0.7
        self.attack_cooldown = 1.0
        self.last_attack_time = 0
        self.is_attacking = False
        self.attack_duration = 0.5
        self.attack_timer = 0
        self.damage_cooldown = 1.0
        self.last_damage_time = 0
        self.last_heal_time = 0
        
        self.sprite_width = 64
        self.sprite_height = 64
        self.columns = 8
        self.rows = 4
        
        if monster_type == 'slime1':
            self.scale_factor = 1.5
        elif monster_type == 'slime2':
            self.scale_factor = 2.0
        elif monster_type == 'slime3':
            self.scale_factor = 2.5
        
        self.current_frame = 0
        self.animation_speed = 0.1
        self.animation_timer = 0
        self.direction = 0
        
        self.run_frames = []
        self.attack_frames = []
        self.hurt_frames = []
        self.load_frames()
        
        self.damage_texts = []
        
        self.is_dying = False
        self.death_timer = 0
        self.death_duration = 0.2
        self.hurt_animation_speed = 0.1
        self.hurt_frame = 0
        self.hurt_row = 0
        self.hurt_animation_played = False
        
        self.is_dead = False
        
        self.attack_sound_played = False
        self.show_path_debug = False
        self.movement_algorithm = "direct"
        self.path = []
        self.path_index = 0
        self.path_update_time = 0.0
        self.path_update_interval = random.uniform(0.3, 0.7)
        self.path_visited_cells = []
        self.pathfinder_instances = {}
        self.path_metrics = {
            "algorithm": "Direct",
            "nodes_visited": 0,
            "path_length": 0,
            "calculation_time_ms": 0.0,
            "failed_attempts": 0,
            "success_rate": 1.0,
            "attempts": 0,
            "successes": 0,
        }
    
    def load_frames(self):
        for row in range(self.rows):
            for col in range(self.columns):
                frame = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
                frame.blit(self.run_sprite_sheet, (0, 0), 
                          (col * self.sprite_width, 
                           row * self.sprite_height, 
                           self.sprite_width, 
                           self.sprite_height))
                frame = pygame.transform.scale(frame, 
                                             (self.sprite_width * self.scale_factor, 
                                              self.sprite_height * self.scale_factor))
                self.run_frames.append(frame)
                
        for row in range(self.rows):
            for col in range(self.columns):
                frame = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
                frame.blit(self.attack_sprite_sheet, (0, 0), 
                          (col * self.sprite_width, 
                           row * self.sprite_height, 
                           self.sprite_width, 
                           self.sprite_height))
                frame = pygame.transform.scale(frame, 
                                             (self.sprite_width * self.scale_factor, 
                                              self.sprite_height * self.scale_factor))
                self.attack_frames.append(frame)
                
        for row in range(4):
            for col in range(5):
                frame = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
                frame.blit(self.hurt_sprite_sheet, (0, 0), 
                          (col * self.sprite_width, 
                           row * self.sprite_height, 
                           self.sprite_width, 
                           self.sprite_height))
                frame = pygame.transform.scale(frame, 
                                             (self.sprite_width * self.scale_factor, 
                                              self.sprite_height * self.scale_factor))
                self.hurt_frames.append(frame)
    
    def take_damage(self, amount, is_crit=False):
        if self.is_dead:
            return
            
        self.health -= amount
        
        center_x = self.x + (self.sprite_width * self.scale_factor) / 2
        center_y = self.y + (self.sprite_height * self.scale_factor) / 2
        self.damage_texts.append(DamageText(center_x, center_y, amount, is_crit))
        
        self.hurt_animation_played = False
        self.hurt_frame = 0
        self.hurt_row = self.direction
        
        if self.health <= 0 and not self.is_dying:
            self.is_dying = True
            self.death_timer = 0
            self.is_dead = True
            if hasattr(self.target, 'hero_type') and self.target.hero_type == 'Hutao':
                self.target.health = min(self.target.health + 1, self.target.max_health)
    
    def apply_slow_effect(self, slow_factor, duration):
        self.is_slowed = True
        self.speed = self.original_speed * slow_factor
        self.slow_effect_end_time = time.time() + duration
        
    
        self.animation_speed = self.animation_speed * 1.5
    
    def update(self, dt, players, monsters, current_time):
        return update_monster_movement(
            self,
            players,
            monsters,
            current_time,
            FIELD_WIDTH,
            FIELD_HEIGHT,
            self.movement_algorithm,
        )
    
    def draw_health_bar(self, surface):
        bar_width = (self.sprite_width * self.scale_factor) * 0.75
        bar_height = 6
        draw_x, draw_y = world_to_screen(self.x, self.y)
        bar_x = draw_x + (self.sprite_width * self.scale_factor - bar_width) // 2
        bar_y = draw_y - 4
        
        pygame.draw.rect(surface, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        max_visible_blocks = 20
        if self.max_health > max_visible_blocks:
            health_per_block = self.max_health / max_visible_blocks
            current_health = self.health
            block_width = bar_width / max_visible_blocks
            separator_width = 1
            
            for i in range(max_visible_blocks):
                block_x = bar_x + (i * block_width)
                block_health = min(health_per_block, current_health)
                if block_health > 0:
                    green_width = (block_health / health_per_block) * (block_width - separator_width)
                    pygame.draw.rect(surface, (0, 255, 0), (block_x, bar_y, green_width, bar_height))
                current_health -= block_health
                
                if i < max_visible_blocks - 1:
                    separator_x = block_x + block_width - separator_width
                    pygame.draw.rect(surface, (200, 200, 200), (separator_x, bar_y, separator_width, bar_height))
        else:
            block_width = bar_width / self.max_health
            separator_width = 1
            block_width_with_spacing = block_width - separator_width
            
            health_int = int(self.health)
            for i in range(health_int):
                block_x = bar_x + (i * block_width)
                pygame.draw.rect(surface, (0, 255, 0), (block_x, bar_y, block_width_with_spacing, bar_height))
            
            for i in range(1, self.max_health):
                separator_x = bar_x + (i * block_width) - separator_width // 2
                pygame.draw.rect(surface, (200, 200, 200), (separator_x, bar_y, separator_width, bar_height))
        
        pygame.draw.rect(surface, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)
    
    def draw(self, surface):
        self.draw_health_bar(surface)
        
        if self.is_dying:
            frame_index = self.hurt_row * 5 + self.hurt_frame
            current_sprite = self.hurt_frames[frame_index]
        elif self.is_attacking:
            frames = self.attack_frames
            attack_frame = int((self.attack_timer / self.attack_duration) * self.columns)
            attack_frame = min(attack_frame, self.columns - 1)
            frame_index = self.direction * self.columns + attack_frame
            current_sprite = frames[frame_index]
        else:
            frames = self.run_frames
            frame_index = self.direction * self.columns + self.current_frame
            current_sprite = frames[frame_index]
            
        if self.is_slowed:
            slowed_sprite = current_sprite.copy()
            blue_overlay = pygame.Surface(slowed_sprite.get_size(), pygame.SRCALPHA)
            blue_overlay.fill((0, 0, 255, 40))  
            slowed_sprite.blit(blue_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            current_sprite = slowed_sprite
            
        sprite_width = self.sprite_width * self.scale_factor
        sprite_height = self.sprite_height * self.scale_factor
        
        draw_x, draw_y = world_to_screen(self.x, self.y)
        surface.blit(current_sprite, (draw_x, draw_y))

        if self.show_path_debug:
            draw_path(surface, self)
            
        for text in self.damage_texts:
            text.draw(surface)
        

    def drop_collectable(self):
        drop_x = self.x + (self.sprite_width * self.scale_factor) / 2 - COLLECTABLE_SIZE / 2
        drop_y = self.y + (self.sprite_height * self.scale_factor) / 2 - COLLECTABLE_SIZE / 2
        
        if self.monster_type == 'slime2':
            collectables = []
            
            for i in range(5):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(40, 80)
                
                offset_x = math.cos(angle) * distance
                offset_y = math.sin(angle) * distance
                
                item_type = random.randint(0, 2)
                
                collectables.append(Collectable(drop_x + offset_x, drop_y + offset_y, item_type))
            
            return collectables
        elif self.monster_type == 'slime3':
            collectables = []
            
            for i in range(10):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(90, 120)
                
                offset_x = math.cos(angle) * distance
                offset_y = math.sin(angle) * distance
                
                item_types = [0, 2, 3]
                item_type = random.choice(item_types)
                
                collectables.append(Collectable(drop_x + offset_x, drop_y + offset_y, item_type))
            
            return collectables
        else:
            collectable_type = random.randint(0, 1)
            return [Collectable(drop_x, drop_y, collectable_type)]

class Upgrade:
    def __init__(self, type, value):
        self.type = type
        self.value = value
        self.name = UPGRADES[type]['name']
        self.description = UPGRADES[type]['description']
        
    def apply(self, player):
        if self.type == 'damage':
            player.damage += self.value
        elif self.type == 'health':
            player.max_health += self.value
            player.health += self.value
        elif self.type == 'range':
            player.attack_range *= (1 + self.value)
        elif self.type == 'crit_chance':
            player.crit_chance += self.value
        elif self.type == 'dodge_chance':
            player.dodge_chance += self.value
        elif self.type == 'attack_speed':
            player.attack_speed *= (1 + self.value)
        elif self.type == 'movement_speed':
            player.speed *= (1 + self.value)

class Collectable:
    def __init__(self, x, y, type):
        self.sprite_sheet = pygame.image.load('sprites/collectables/items.png').convert_alpha()
        
        self.x = x
        self.y = y
        
        self.type = type
        
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = COLLECTABLE_ANIMATION_SPEED
        self.columns = 8
        self.rows = 8
        
        self.frames = []
        self.load_frames()
        
        self.is_collected = False
        self.collected_by = None
        self.collection_timer = 0
        self.collection_speed = 10
        self.collection_threshold = 30
        
    def load_frames(self):
        if self.type == 0:
            row = 0
        elif self.type == 1:
            row = 7
        elif self.type == 2:
            row = 6
        elif self.type == 3:
            row = 8
        
        for col in range(self.columns):
            frame = pygame.Surface((COLLECTABLE_SIZE, COLLECTABLE_SIZE), pygame.SRCALPHA)
            frame.blit(self.sprite_sheet, (0, 0), 
                      (col * COLLECTABLE_SIZE, 
                       row * COLLECTABLE_SIZE, 
                       COLLECTABLE_SIZE, 
                       COLLECTABLE_SIZE))
            self.frames.append(frame)
            
    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % self.columns
            
        if self.is_collected and self.collected_by:
            self.collection_timer += dt
            
            player_center_x = self.collected_by.x + (self.collected_by.sprite_width * self.collected_by.scale_factor) / 2
            player_center_y = self.collected_by.y + (self.collected_by.sprite_height * self.collected_by.scale_factor) / 2
            
            dx = player_center_x - self.x
            dy = player_center_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                dx /= distance
                dy /= distance
                
                self.x += dx * self.collection_speed
                self.y += dy * self.collection_speed
            
    def draw(self, surface):
        current_sprite = self.frames[self.current_frame]
        draw_x, draw_y = world_to_screen(self.x, self.y)
        surface.blit(current_sprite, (draw_x, draw_y))
        
    def check_collection(self, player):
        if self.is_collected:
            return False
            
        collectable_center_x = self.x + COLLECTABLE_SIZE / 2
        collectable_center_y = self.y + COLLECTABLE_SIZE / 2
        player_center_x = player.x + (player.sprite_width * player.scale_factor) / 2
        player_center_y = player.y + (player.sprite_height * player.scale_factor) / 2
        
        dx = player_center_x - collectable_center_x
        dy = player_center_y - collectable_center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < COLLECTABLE_SIZE * player.pickup_radius:
            self.is_collected = True
            self.collected_by = player
            return True
        return False
        
    def is_collection_complete(self):
        if not self.is_collected or not self.collected_by:
            return False
            
        player_center_x = self.collected_by.x + (self.collected_by.sprite_width * self.collected_by.scale_factor) / 2
        player_center_y = self.collected_by.y + (self.collected_by.sprite_height * self.collected_by.scale_factor) / 2
        
        dx = player_center_x - self.x
        dy = player_center_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        return distance < self.collection_threshold


class TreeObstacle:
    def __init__(self, x, y, sprite):
        self.base_sprite = sprite
        self.scale = random.uniform(TREE_VARIATION_SCALE[0], TREE_VARIATION_SCALE[1])
        scaled_w = max(24, int(sprite.get_width() * self.scale))
        scaled_h = max(24, int(sprite.get_height() * self.scale))
        self.sprite = pygame.transform.smoothscale(sprite, (scaled_w, scaled_h))
        self.rect = self.sprite.get_rect(topleft=(int(x), int(y)))

        collision_w = max(10, int(self.rect.width * TREE_COLLISION_SCALE))
        collision_h = max(10, int(self.rect.height * 0.14))
        collision_x = self.rect.centerx - collision_w // 2
        collision_y = self.rect.bottom - collision_h - 2
        self.collision_rect = pygame.Rect(collision_x, collision_y, collision_w, collision_h)

    def draw(self, surface):
        draw_x, draw_y = world_to_screen(self.rect.x, self.rect.y)
        surface.blit(self.sprite, (draw_x, draw_y))

    def draw_debug(self, surface):
        debug_rect = self.collision_rect.move(-int(CAMERA_X), -int(CAMERA_Y))
        pygame.draw.rect(surface, (0, 255, 255), debug_rect, 2)

class UpgradeMenu:
    def __init__(self):
        self.is_open = False
        self.current_player = None
        self.hovered_upgrade = None
        self.player1_hovered_upgrade = None
        self.player2_hovered_upgrade = None
        self.back_to_menu_button = Button(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 100, 300, 50, "Menu")
        self.continue_button = Button(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 160, 300, 50, "Tiếp tục")

    def _compute_layout(self):
        menu1_x = SCREEN_WIDTH // 4
        menu2_x = 3 * SCREEN_WIDTH // 4
        panel_width = 400
        top_margin = 40

        button_width = 300
        button_height = 48
        button_gap = 12
        button_bottom_padding = 24

        back_y = SCREEN_HEIGHT - button_bottom_padding - button_height
        continue_y = back_y - button_gap - button_height
        self.back_to_menu_button.rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, back_y, button_width, button_height)
        self.continue_button.rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, continue_y, button_width, button_height)

        total_upgrades = len(UPGRADES)
        available_bottom = continue_y - 20
        available_height = max(250, available_bottom - top_margin)
        row_slot_height = max(48, min(60, available_height // max(1, total_upgrades)))
        row_height = row_slot_height - 8
        start_y = top_margin

        return {
            "menu1_x": menu1_x,
            "menu2_x": menu2_x,
            "panel_width": panel_width,
            "row_slot_height": row_slot_height,
            "row_height": row_height,
            "start_y": start_y,
        }

    def _upgrade_rect(self, panel_center_x, layout, index):
        left = panel_center_x - layout["panel_width"] // 2
        y = layout["start_y"] + index * layout["row_slot_height"]
        return pygame.Rect(left, y, layout["panel_width"], layout["row_height"])
    
    def toggle(self):
        self.is_open = not self.is_open
    
    def set_current_player(self, player):
        self.current_player = player
    
    def handle_mouse_hover(self, pos, player1, player2):
        layout = self._compute_layout()
        self.back_to_menu_button.check_hover(pos)
        self.continue_button.check_hover(pos)
        
        self.player1_hovered_upgrade = None
        self.player2_hovered_upgrade = None
        
        for i, upgrade_type in enumerate(UPGRADES.keys()):
            upgrade_rect = self._upgrade_rect(layout["menu1_x"], layout, i)
            if upgrade_rect.collidepoint(pos):
                self.player1_hovered_upgrade = upgrade_type
                break
        
        if player2 != player1:
            for i, upgrade_type in enumerate(UPGRADES.keys()):
                upgrade_rect = self._upgrade_rect(layout["menu2_x"], layout, i)
                if upgrade_rect.collidepoint(pos):
                    self.player2_hovered_upgrade = upgrade_type
                    break
    
    def handle_mouse_click(self, pos, player1, player2):
        if not self.is_open:
            return False
        layout = self._compute_layout()
        
        if self.back_to_menu_button.is_clicked(pos, True):
            return "back_to_menu"
            
        if self.continue_button.is_clicked(pos, True):
            return "continue"
        
        for i, upgrade_type in enumerate(UPGRADES.keys()):
            upgrade_rect = self._upgrade_rect(layout["menu1_x"], layout, i)
            if upgrade_rect.collidepoint(pos):
                return player1.apply_upgrade(upgrade_type)
        
        if player2 != player1:
            for i, upgrade_type in enumerate(UPGRADES.keys()):
                upgrade_rect = self._upgrade_rect(layout["menu2_x"], layout, i)
                if upgrade_rect.collidepoint(pos):
                    return player2.apply_upgrade(upgrade_type)
        
        return False
    
    def draw(self, surface, player1, player2):
        if not self.is_open:
            return
        layout = self._compute_layout()
        menu1_x = layout["menu1_x"]
        menu2_x = layout["menu2_x"]
        panel_width = layout["panel_width"]

        overlay1 = pygame.Surface((panel_width, SCREEN_HEIGHT))
        overlay1.fill(BLACK)
        overlay1.set_alpha(128)
        surface.blit(overlay1, (menu1_x - panel_width // 2, 0))
        
        for i, (upgrade_type, upgrade_data) in enumerate(UPGRADES.items()):
            upgrade_rect = self._upgrade_rect(menu1_x, layout, i)
            
            if upgrade_type == self.player1_hovered_upgrade:
                pygame.draw.rect(surface, HIGHLIGHT, upgrade_rect)
            else:
                pygame.draw.rect(surface, GRAY, upgrade_rect)
                
            pygame.draw.rect(surface, WHITE, upgrade_rect, 2)
            
            key_name = pygame.key.name(upgrade_data['key1'])
            
            name_text = status_font.render(f"[{key_name}] {upgrade_data['name']} ({player1.upgrade_levels[upgrade_type]}/{player1.level})", True, WHITE)
            name_rect = name_text.get_rect(midleft=(upgrade_rect.left + 10, upgrade_rect.centery))
            surface.blit(name_text, name_rect)
            
            cost = player1.get_upgrade_cost(upgrade_type)
            cost_text = status_font.render(f"{cost} Gold", True, GOLD_COLOR)
            cost_rect = cost_text.get_rect(midright=(upgrade_rect.right - 10, upgrade_rect.centery))
            surface.blit(cost_text, cost_rect)
            
            if player1.upgrade_levels[upgrade_type] >= player1.level:
                max_text = status_font.render("MAX", True, (255, 0, 0))
                max_rect = max_text.get_rect(midright=(upgrade_rect.right - 100, upgrade_rect.centery))
                surface.blit(max_text, max_rect)
        
        self.continue_button.draw(surface)
        self.back_to_menu_button.draw(surface)
        
        if player2 != player1:
            overlay2 = pygame.Surface((panel_width, SCREEN_HEIGHT))
            overlay2.fill(BLACK)
            overlay2.set_alpha(128)
            surface.blit(overlay2, (menu2_x - panel_width // 2, 0))
            
            for i, (upgrade_type, upgrade_data) in enumerate(UPGRADES.items()):
                upgrade_rect = self._upgrade_rect(menu2_x, layout, i)
                
                if upgrade_type == self.player2_hovered_upgrade:
                    pygame.draw.rect(surface, HIGHLIGHT, upgrade_rect)
                else:
                    pygame.draw.rect(surface, GRAY, upgrade_rect)
                    
                pygame.draw.rect(surface, WHITE, upgrade_rect, 2)
                
                key_name = pygame.key.name(upgrade_data['key2'])
                
                name_text = status_font.render(f"[{key_name}] {upgrade_data['name']} ({player2.upgrade_levels[upgrade_type]}/{player2.level})", True, WHITE)
                name_rect = name_text.get_rect(midleft=(upgrade_rect.left + 10, upgrade_rect.centery))
                surface.blit(name_text, name_rect)
                
                cost = player2.get_upgrade_cost(upgrade_type)
                cost_text = status_font.render(f"{cost} Gold", True, GOLD_COLOR)
                cost_rect = cost_text.get_rect(midright=(upgrade_rect.right - 10, upgrade_rect.centery))
                surface.blit(cost_text, cost_rect)
                
                if player2.upgrade_levels[upgrade_type] >= player2.level:
                    max_text = status_font.render("MAX", True, (255, 0, 0))
                    max_rect = max_text.get_rect(midright=(upgrade_rect.right - 100, upgrade_rect.centery))
                    surface.blit(max_text, max_rect)

class HeroSelection:
    def __init__(self):
        self.heroes = {
            'Paimon': {
                'name': 'Paimon',
                'sprite_path': 'sprites/player/animations/run_anim.png',
                'description': 'Ngoài ăn nhiều và nói lắm không còn gì đặc biệt .',
                'icon_path': 'icons/Paimon.png',
                'bullet_path': 'sprites/bullets/2.png',
                'sprite_config': {
                    'down_row': 0,
                    'left_row': 1,
                    'right_row': 2,
                    'up_row': 3
                }
            },
            'Hutao': {
                'name': 'Hutao',
                'sprite_path': 'sprites/Hutao/run_anim.png',
                'description': 'Em xinh nên em có quyền hút máu.',
                'icon_path': 'icons/Hutao.png',
                'bullet_path': 'sprites/bullets/3.png',
                'sprite_config': {
                    'down_row': 0,
                    'up_row': 1,
                    'left_row': 2,
                    'right_row': 3
                }
            },
            'Furina': {
                'name': 'Furina',
                'sprite_path': 'sprites/Furina/run_anim.png',
                'description': 'Furina có khả năng bắn và làm chậm quái.',
                'icon_path': 'icons/Furina.png',
                'bullet_path': 'sprites/bullets/1.png',
                'sprite_config': {
                    'down_row': 0,
                    'left_row': 1,
                    'right_row': 2,
                    'up_row': 3
                }
            }
        }
        self.selected_hero_p1 = None
        self.selected_hero_p2 = None
        self.is_coop = False
        
        self.hero_icons = {}
        self.hero_rects_p1 = {}
        self.hero_rects_p2 = {}
        
        icon_spacing = 120
        start_x_p1 = SCREEN_WIDTH // 4 - (len(self.heroes) * icon_spacing) // 4
        start_x_p2 = 3 * SCREEN_WIDTH // 4 - (len(self.heroes) * icon_spacing) // 4
        
        for i, (hero_id, hero_data) in enumerate(self.heroes.items()):
            if os.path.exists(hero_data['icon_path']):
                icon = pygame.image.load(hero_data['icon_path']).convert_alpha()
                icon = pygame.transform.scale(icon, (100, 100))
                self.hero_icons[hero_id] = icon
                
                icon_rect_p1 = icon.get_rect(center=(start_x_p1 + i * icon_spacing, SCREEN_HEIGHT // 2 - 50))
                icon_rect_p2 = icon.get_rect(center=(start_x_p2 + i * icon_spacing, SCREEN_HEIGHT // 2 - 50))
                self.hero_rects_p1[hero_id] = icon_rect_p1
                self.hero_rects_p2[hero_id] = icon_rect_p2
        
        button_width = 200
        button_height = 50
        self.select_button = Button(SCREEN_WIDTH // 2 - button_width // 2, 
                                  SCREEN_HEIGHT - 100, 
                                  button_width, button_height, "Bắt đầu")
        self.select_button.is_enabled = False
    
    def set_mode(self, is_coop):
        self.is_coop = is_coop
        self.selected_hero_p1 = None
        self.selected_hero_p2 = None
        self.select_button.is_enabled = False
    
    def handle_click(self, pos):
        if self.is_coop:
            for hero_id, rect in self.hero_rects_p1.items():
                if rect.collidepoint(pos):
                    self.selected_hero_p1 = hero_id
                    self.update_button_state()
                    return True
            
            for hero_id, rect in self.hero_rects_p2.items():
                if rect.collidepoint(pos):
                    self.selected_hero_p2 = hero_id
                    self.update_button_state()
                    return True
        else:
            for hero_id, rect in self.hero_rects_p1.items():
                if rect.collidepoint(pos):
                    self.selected_hero_p1 = hero_id
                    self.update_button_state()
                    return True
        return False
    
    def update_button_state(self):
        if self.is_coop:
            self.select_button.is_enabled = self.selected_hero_p1 is not None and self.selected_hero_p2 is not None
        else:
            self.select_button.is_enabled = self.selected_hero_p1 is not None
    
    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))
        
        title = font.render("Chọn Char", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title, title_rect)
        
        if self.is_coop:
            p1_title = small_font.render("Player 1", True, (0, 0, 255))
            p2_title = small_font.render("Player 2", True, (255, 0, 0))
            surface.blit(p1_title, p1_title.get_rect(center=(SCREEN_WIDTH // 4, 100)))
            surface.blit(p2_title, p2_title.get_rect(center=(3 * SCREEN_WIDTH // 4, 100)))
            
            for hero_id, icon in self.hero_icons.items():
                rect_p1 = self.hero_rects_p1[hero_id]
                if hero_id == self.selected_hero_p1:
                    pygame.draw.rect(surface, (0, 0, 255), rect_p1.inflate(10, 10), 3)
                surface.blit(icon, rect_p1)
                
                rect_p2 = self.hero_rects_p2[hero_id]
                if hero_id == self.selected_hero_p2:
                    pygame.draw.rect(surface, (255, 0, 0), rect_p2.inflate(10, 10), 3)
                surface.blit(icon, rect_p2)
            
            if self.selected_hero_p1:
                name = small_font.render(self.heroes[self.selected_hero_p1]['name'], True, WHITE)
                desc = small_font.render(self.heroes[self.selected_hero_p1]['description'], True, WHITE)
                surface.blit(name, name.get_rect(center=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 100)))
                surface.blit(desc, desc.get_rect(center=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 150)))
            
            if self.selected_hero_p2:
                name = small_font.render(self.heroes[self.selected_hero_p2]['name'], True, WHITE)
                desc = small_font.render(self.heroes[self.selected_hero_p2]['description'], True, WHITE)
                surface.blit(name, name.get_rect(center=(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 100)))
                surface.blit(desc, desc.get_rect(center=(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 150)))
        else:
            for hero_id, icon in self.hero_icons.items():
                rect = self.hero_rects_p1[hero_id]
                if hero_id == self.selected_hero_p1:
                    pygame.draw.rect(surface, HIGHLIGHT, rect.inflate(10, 10), 3)
                surface.blit(icon, rect)
            
            if self.selected_hero_p1:
                name = small_font.render(self.heroes[self.selected_hero_p1]['name'], True, WHITE)
                desc = small_font.render(self.heroes[self.selected_hero_p1]['description'], True, WHITE)
                surface.blit(name, name.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)))
                surface.blit(desc, desc.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150)))
        
        if not self.select_button.is_enabled:
            old_color = self.select_button.color
            self.select_button.color = GRAY
        self.select_button.draw(surface)
        if not self.select_button.is_enabled:
            self.select_button.color = old_color
        
        if custom_cursor:
            mouse_pos = get_virtual_mouse_pos()
            surface.blit(custom_cursor, (mouse_pos[0] - 16, mouse_pos[1] - 16))

class Game:
    def __init__(self):
        self.state = "menu"
        self.create_menu_buttons()
        self.monsters = []
        self.collectables = []
        self.last_spawn_time = 0
        self.last_slime2_spawn_time = 0
        self.current_time = 0
        self.game_start_time = 0
        self.game_time = 0
        self.is_paused = False
        self.upgrade_menu = UpgradeMenu()
        self.hero_selection = HeroSelection()
        self.current_player = None
        self.pause_start_time = 0
        self.total_pause_time = 0
        self.last_monster_spawn_time = 0
        self.last_slime3_spawn_time = 0
        self.game_over_sound_played = False
        
        self.leaderboard_mode = "singleplayer"
        
        self.controls = self.load_controls()
        
        self.game_over_background = None
        if os.path.exists('images/gameover.jpg'):
            self.game_over_background = pygame.image.load('images/gameover.jpg').convert()
            self.game_over_background = pygame.transform.scale(self.game_over_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.game_over_sound = None
        if os.path.exists('sounds/gameover.mp3'):
            self.game_over_sound = pygame.mixer.Sound('sounds/gameover.mp3')
            self.game_over_sound.set_volume(0.5)
        
        self.menu_selection_sound = None
        if os.path.exists('sounds/menu_selection.mp3'):
            self.menu_selection_sound = pygame.mixer.Sound('sounds/menu_selection.mp3')
            self.menu_selection_sound.set_volume(0.5)
        
        self.collect_sound = None
        if os.path.exists('sounds/collect.mp3'):
            self.collect_sound = pygame.mixer.Sound('sounds/collect.mp3')
            self.collect_sound.set_volume(0.5)
        
        self.menu_music = None
        self.ingame_music = None
        if os.path.exists('sounds/menu_music.mp3'):
            self.menu_music = pygame.mixer.Sound('sounds/menu_music.mp3')
            self.menu_music.set_volume(0.5)
        if os.path.exists('sounds/ingame_music.mp3'):
            self.ingame_music = pygame.mixer.Sound('sounds/ingame_music.mp3')
            self.ingame_music.set_volume(0.5)
        self.current_music = None
        
        self.menu_background = None
        if os.path.exists('images/background.jpg'):
            self.menu_background = pygame.image.load('images/background.jpg').convert()
            self.menu_background = pygame.transform.scale(self.menu_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
        self.play_menu_music()
        
        self.highscores = self.load_highscores()
        
        self.editing_control = None
        self.waiting_for_key = False
        self.control_buttons = []
        self.create_control_buttons()
        self.ensure_runtime_state()

    def ensure_runtime_state(self):
        if not hasattr(self, "show_path_debug"):
            self.show_path_debug = SHOW_PATH_DEBUG
        if not hasattr(self, "algorithm_comparison_mode"):
            self.algorithm_comparison_mode = False
        if not hasattr(self, "algorithm_selector_open"):
            self.algorithm_selector_open = False
        if not hasattr(self, "algorithm_selector_index"):
            self.algorithm_selector_index = 0
        if not hasattr(self, "selected_algorithms"):
            self.selected_algorithms = {
                "slime1": "direct",
                "slime2": "astar",
                "slime3": "hill_climbing",
            }
        if not hasattr(self, "toast_message"):
            self.toast_message = ""
        if not hasattr(self, "toast_expire_time"):
            self.toast_expire_time = 0.0

        if not hasattr(self, "arena_mode_same_target"):
            self.arena_mode_same_target = True
        if not hasattr(self, "arena_time_scale_index"):
            self.arena_time_scale_index = 0
        if not hasattr(self, "arena_time_scale"):
            self.arena_time_scale = ARENA_SLOW_MOTION_LEVELS[0]
        if not hasattr(self, "arena_locked_camera"):
            self.arena_locked_camera = True
        if not hasattr(self, "arena_zoom"):
            self.arena_zoom = 0.62
        if not hasattr(self, "arena_zone_algorithms"):
            self.arena_zone_algorithms = ARENA_ALGORITHMS[:]
        if not hasattr(self, "arena_zone_targets"):
            self.arena_zone_targets = []
        if not hasattr(self, "arena_replay_buffer"):
            self.arena_replay_buffer = deque(maxlen=int(ARENA_REPLAY_SECONDS * ARENA_REPLAY_FPS) + 5)
        if not hasattr(self, "arena_replay_active"):
            self.arena_replay_active = False
        if not hasattr(self, "arena_replay_cursor"):
            self.arena_replay_cursor = 0
        if not hasattr(self, "arena_replay_frame_interval"):
            self.arena_replay_frame_interval = 1.0 / ARENA_REPLAY_FPS
        if not hasattr(self, "arena_replay_accumulator"):
            self.arena_replay_accumulator = 0.0
        if not hasattr(self, "arena_last_summary"):
            self.arena_last_summary = {}
        if not hasattr(self, "arena_new_button"):
            self.arena_new_button = Button(SCREEN_WIDTH - 220, 24, 190, 36, "Map moi")
        self.show_path_debug = SHOW_PATH_DEBUG
        self.algorithm_comparison_mode = False
        self.algorithm_selector_open = False
        self.algorithm_selector_index = 0
        self.selected_algorithms = {
            "slime1": "direct",
            "slime2": "astar",
            "slime3": "hill_climbing",
        }
        self.toast_message = ""
        self.toast_expire_time = 0.0
        self.arena_mode_same_target = True
        self.arena_time_scale_index = 0
        self.arena_time_scale = ARENA_SLOW_MOTION_LEVELS[0]
        self.arena_locked_camera = True
        self.arena_zone_algorithms = ARENA_ALGORITHMS[:]
        self.arena_zone_targets = []
        self.arena_replay_buffer = deque(maxlen=int(ARENA_REPLAY_SECONDS * ARENA_REPLAY_FPS) + 5)
        self.arena_replay_active = False
        self.arena_replay_cursor = 0
        self.arena_replay_frame_interval = 1.0 / ARENA_REPLAY_FPS
        self.arena_replay_accumulator = 0.0
        self.arena_last_summary = {}
        self.arena_new_button = Button(SCREEN_WIDTH - 220, 24, 190, 36, "Map moi")
        self.tree_obstacles = []
        self.tree_collision_rects = []
        self.generate_tree_obstacles()

    def load_controls(self):
        try:
            with open('controls.json', 'r') as f:
                controls = json.load(f)
                for player in controls:
                    for direction in controls[player]:
                        key_str = controls[player][direction]
                        if key_str.startswith("K_["):
                            key_num = int(key_str[3:-1])
                            controls[player][direction] = key_num
                        else:
                            key_name = key_str[2:]
                            if key_name in ["UP", "DOWN", "LEFT", "RIGHT"]:
                                controls[player][direction] = getattr(pygame, f"K_{key_name}")
                            else:
                                controls[player][direction] = getattr(pygame, key_str)
                
                if "upgrades" not in controls["player1"]:
                    controls["player1"]["upgrades"] = pygame.K_e
                if "upgrades" not in controls["player2"]:
                    controls["player2"]["upgrades"] = pygame.K_e
                    
                return controls
        except FileNotFoundError:
            return {
                "player1": {
                    "up": K_w,
                    "down": K_s,
                    "left": K_a,
                    "right": K_d,
                    "upgrades": K_e
                },
                "player2": {
                    "up": K_UP,
                    "down": K_DOWN,
                    "left": K_LEFT,
                    "right": K_RIGHT,
                    "upgrades": K_e
                }
            }
            
    def save_controls(self):
        controls_to_save = {}
        for player in self.controls:
            controls_to_save[player] = {}
            for direction in self.controls[player]:
                key = self.controls[player][direction]
                if isinstance(key, int):
                    controls_to_save[player][direction] = f"K_[{key}]"
                else:
                    key_name = pygame.key.name(key)
                    controls_to_save[player][direction] = f"K_{key_name.upper()}"
        
        with open('controls.json', 'w') as f:
            json.dump(controls_to_save, f, indent=4)
            
    def create_control_buttons(self):
        self.control_buttons = []
        directions = ["up", "down", "left", "right"]
        button_width = 200
        button_height = 40
        spacing = 60
        
        for i, direction in enumerate(directions):
            x = SCREEN_WIDTH // 4 - button_width // 2
            y = 200 + i * spacing
            button = Button(x, y, button_width, button_height, 
                          f"Player 1 {direction}: {pygame.key.name(self.controls['player1'][direction])}")
            self.control_buttons.append(("player1", direction, button))
            
        
        self.hero_icons = {}
        self.hero_rects_p1 = {}
        self.hero_rects_p2 = {}
        
        icon_spacing = 120  
        start_x_p1 = SCREEN_WIDTH // 4 - (len(self.heroes) * icon_spacing) // 4
        start_x_p2 = 3 * SCREEN_WIDTH // 4 - (len(self.heroes) * icon_spacing) // 4
        
        for i, (hero_id, hero_data) in enumerate(self.heroes.items()):
            if os.path.exists(hero_data['icon_path']):
                icon = pygame.image.load(hero_data['icon_path']).convert_alpha()
                icon = pygame.transform.scale(icon, (100, 100))
                self.hero_icons[hero_id] = icon
                
                icon_rect_p1 = icon.get_rect(center=(start_x_p1 + i * icon_spacing, SCREEN_HEIGHT // 2 - 50))
                icon_rect_p2 = icon.get_rect(center=(start_x_p2 + i * icon_spacing, SCREEN_HEIGHT // 2 - 50))
                self.hero_rects_p1[hero_id] = icon_rect_p1
                self.hero_rects_p2[hero_id] = icon_rect_p2
        
        button_width = 200
        button_height = 50
        self.select_button = Button(SCREEN_WIDTH // 2 - button_width // 2, 
                                  SCREEN_HEIGHT - 100, 
                                  button_width, button_height, "Bắt đầu")
        self.select_button.is_enabled = False
    
    def set_mode(self, is_coop):
        self.is_coop = is_coop
        self.selected_hero_p1 = None
        self.selected_hero_p2 = None
        self.select_button.is_enabled = False
    
    def handle_click(self, pos):
        if self.is_coop:
            for hero_id, rect in self.hero_rects_p1.items():
                if rect.collidepoint(pos):
                    self.selected_hero_p1 = hero_id
                    self.update_button_state()
                    return True
            
            for hero_id, rect in self.hero_rects_p2.items():
                if rect.collidepoint(pos):
                    self.selected_hero_p2 = hero_id
                    self.update_button_state()
                    return True
        else:
            for hero_id, rect in self.hero_rects_p1.items():
                if rect.collidepoint(pos):
                    self.selected_hero_p1 = hero_id
                    self.update_button_state()
                    return True
        return False
    
    def update_button_state(self):
        if self.is_coop:
            self.select_button.is_enabled = self.selected_hero_p1 is not None and self.selected_hero_p2 is not None
        else:
            self.select_button.is_enabled = self.selected_hero_p1 is not None
    
    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))
        
        title = font.render("Chọn Char", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title, title_rect)
        
        if self.is_coop:
            p1_title = small_font.render("Player 1", True, (0, 0, 255))
            p2_title = small_font.render("Player 2", True, (255, 0, 0))
            surface.blit(p1_title, p1_title.get_rect(center=(SCREEN_WIDTH // 4, 100)))
            surface.blit(p2_title, p2_title.get_rect(center=(3 * SCREEN_WIDTH // 4, 100)))
            
            for hero_id, icon in self.hero_icons.items():
                rect_p1 = self.hero_rects_p1[hero_id]
                if hero_id == self.selected_hero_p1:
                    pygame.draw.rect(surface, (0, 0, 255), rect_p1.inflate(10, 10), 3)
                surface.blit(icon, rect_p1)
                
                rect_p2 = self.hero_rects_p2[hero_id]
                if hero_id == self.selected_hero_p2:
                    pygame.draw.rect(surface, (255, 0, 0), rect_p2.inflate(10, 10), 3)
                surface.blit(icon, rect_p2)
            
            if self.selected_hero_p1:
                name = small_font.render(self.heroes[self.selected_hero_p1]['name'], True, WHITE)
                desc = small_font.render(self.heroes[self.selected_hero_p1]['description'], True, WHITE)
                surface.blit(name, name.get_rect(center=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 100)))
                surface.blit(desc, desc.get_rect(center=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 150)))
            
            if self.selected_hero_p2:
                name = small_font.render(self.heroes[self.selected_hero_p2]['name'], True, WHITE)
                desc = small_font.render(self.heroes[self.selected_hero_p2]['description'], True, WHITE)
                surface.blit(name, name.get_rect(center=(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 100)))
                surface.blit(desc, desc.get_rect(center=(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 150)))
        else:
            for hero_id, icon in self.hero_icons.items():
                rect = self.hero_rects_p1[hero_id]
                if hero_id == self.selected_hero_p1:
                    pygame.draw.rect(surface, HIGHLIGHT, rect.inflate(10, 10), 3)
                surface.blit(icon, rect)
            
            if self.selected_hero_p1:
                name = small_font.render(self.heroes[self.selected_hero_p1]['name'], True, WHITE)
                desc = small_font.render(self.heroes[self.selected_hero_p1]['description'], True, WHITE)
                surface.blit(name, name.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)))
                surface.blit(desc, desc.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150)))
        
        if not self.select_button.is_enabled:
            old_color = self.select_button.color
            self.select_button.color = GRAY
        self.select_button.draw(surface)
        if not self.select_button.is_enabled:
            self.select_button.color = old_color
        
        if custom_cursor:
            mouse_pos = get_virtual_mouse_pos()
            surface.blit(custom_cursor, (mouse_pos[0] - 16, mouse_pos[1] - 16))

class Game:
    def __init__(self):
        self.state = "menu"
        self.create_menu_buttons()
        self.monsters = []
        self.collectables = []
        self.last_spawn_time = 0
        self.last_slime2_spawn_time = 0
        self.current_time = 0
        self.game_start_time = 0
        self.game_time = 0
        self.is_paused = False
        self.upgrade_menu = UpgradeMenu()
        self.hero_selection = HeroSelection()
        self.current_player = None
        self.pause_start_time = 0
        self.total_pause_time = 0
        self.last_monster_spawn_time = 0
        self.last_slime3_spawn_time = 0
        self.game_over_sound_played = False
        
        self.leaderboard_mode = "singleplayer"
        
        self.controls = self.load_controls()
        
        self.game_over_background = None
        if os.path.exists('images/gameover.jpg'):
            self.game_over_background = pygame.image.load('images/gameover.jpg').convert()
            self.game_over_background = pygame.transform.scale(self.game_over_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.game_over_sound = None
        if os.path.exists('sounds/gameover.mp3'):
            self.game_over_sound = pygame.mixer.Sound('sounds/gameover.mp3')
            self.game_over_sound.set_volume(0.5)
        
        self.menu_selection_sound = None
        if os.path.exists('sounds/menu_selection.mp3'):
            self.menu_selection_sound = pygame.mixer.Sound('sounds/menu_selection.mp3')
            self.menu_selection_sound.set_volume(0.5)
        
        self.collect_sound = None
        if os.path.exists('sounds/collect.mp3'):
            self.collect_sound = pygame.mixer.Sound('sounds/collect.mp3')
            self.collect_sound.set_volume(0.5)
        
        self.menu_music = None
        self.ingame_music = None
        if os.path.exists('sounds/menu_music.mp3'):
            self.menu_music = pygame.mixer.Sound('sounds/menu_music.mp3')
            self.menu_music.set_volume(0.5)
        if os.path.exists('sounds/ingame_music.mp3'):
            self.ingame_music = pygame.mixer.Sound('sounds/ingame_music.mp3')
            self.ingame_music.set_volume(0.5)
        self.current_music = None
        
        self.menu_background = None
        if os.path.exists('images/background.jpg'):
            self.menu_background = pygame.image.load('images/background.jpg').convert()
            self.menu_background = pygame.transform.scale(self.menu_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
        self.play_menu_music()
        
        self.highscores = self.load_highscores()
        
        self.editing_control = None
        self.waiting_for_key = False
        self.control_buttons = []
        self.create_control_buttons()
        self.ensure_runtime_state()

    def ensure_runtime_state(self):
        if not hasattr(self, "show_path_debug"):
            self.show_path_debug = SHOW_PATH_DEBUG
        if not hasattr(self, "algorithm_comparison_mode"):
            self.algorithm_comparison_mode = False
        if not hasattr(self, "algorithm_selector_open"):
            self.algorithm_selector_open = False
        if not hasattr(self, "algorithm_selector_index"):
            self.algorithm_selector_index = 0
        if not hasattr(self, "selected_algorithms"):
            self.selected_algorithms = {
                "slime1": "direct",
                "slime2": "astar",
                "slime3": "hill_climbing",
            }
        if not hasattr(self, "toast_message"):
            self.toast_message = ""
        if not hasattr(self, "toast_expire_time"):
            self.toast_expire_time = 0.0

        if not hasattr(self, "arena_mode_same_target"):
            self.arena_mode_same_target = True
        if not hasattr(self, "arena_time_scale_index"):
            self.arena_time_scale_index = 0
        if not hasattr(self, "arena_time_scale"):
            self.arena_time_scale = ARENA_SLOW_MOTION_LEVELS[0]
        if not hasattr(self, "arena_locked_camera"):
            self.arena_locked_camera = True
        if not hasattr(self, "arena_zoom"):
            self.arena_zoom = 0.62
        if not hasattr(self, "arena_zone_algorithms"):
            self.arena_zone_algorithms = ARENA_ALGORITHMS[:]
        if not hasattr(self, "arena_zone_targets"):
            self.arena_zone_targets = []
        if not hasattr(self, "arena_replay_buffer"):
            self.arena_replay_buffer = deque(maxlen=int(ARENA_REPLAY_SECONDS * ARENA_REPLAY_FPS) + 5)
        if not hasattr(self, "arena_replay_active"):
            self.arena_replay_active = False
        if not hasattr(self, "arena_replay_cursor"):
            self.arena_replay_cursor = 0
        if not hasattr(self, "arena_replay_frame_interval"):
            self.arena_replay_frame_interval = 1.0 / ARENA_REPLAY_FPS
        if not hasattr(self, "arena_replay_accumulator"):
            self.arena_replay_accumulator = 0.0
        if not hasattr(self, "arena_last_summary"):
            self.arena_last_summary = {}
        if not hasattr(self, "arena_new_button"):
            self.arena_new_button = Button(SCREEN_WIDTH - 220, 24, 190, 36, "Map moi")

    def load_controls(self):
        try:
            with open('controls.json', 'r') as f:
                controls = json.load(f)
                for player in controls:
                    for direction in controls[player]:
                        key_str = controls[player][direction]
                        if key_str.startswith("K_["):
                            key_num = int(key_str[3:-1])
                            controls[player][direction] = key_num
                        else:
                            key_name = key_str[2:] 
                            if key_name in ["UP", "DOWN", "LEFT", "RIGHT"]:
                                controls[player][direction] = getattr(pygame, f"K_{key_name}")
                            else:
                                controls[player][direction] = getattr(pygame, key_str)
                
                if "upgrades" not in controls["player1"]:
                    controls["player1"]["upgrades"] = pygame.K_p
                if "upgrades" not in controls["player2"]:
                    controls["player2"]["upgrades"] = pygame.K_p
                    
                return controls
        except FileNotFoundError:
            return {
                "player1": {
                    "up": K_w,
                    "down": K_s,
                    "left": K_a,
                    "right": K_d,
                    "upgrades": K_p
                },
                "player2": {
                    "up": K_UP,
                    "down": K_DOWN,
                    "left": K_LEFT,
                    "right": K_RIGHT,
                    "upgrades": K_p
                }
            }
            
    def save_controls(self):
        controls_to_save = {}
        for player in self.controls:
            controls_to_save[player] = {}
            for direction in self.controls[player]:
                key = self.controls[player][direction]
                if isinstance(key, int):
                    controls_to_save[player][direction] = f"K_[{key}]"
                else:
                    key_name = pygame.key.name(key)
                    controls_to_save[player][direction] = f"K_{key_name.upper()}"
        
        with open('controls.json', 'w') as f:
            json.dump(controls_to_save, f, indent=4)
            
    def create_control_buttons(self):
        self.control_buttons = []
        directions = ["up", "down", "left", "right"]
        button_width = 200
        button_height = 40
        spacing = 60
        
        for i, direction in enumerate(directions):
            x = SCREEN_WIDTH // 4 - button_width // 2
            y = 200 + i * spacing
            button = Button(x, y, button_width, button_height, 
                          f"Player 1 {direction}: {pygame.key.name(self.controls['player1'][direction])}")
            self.control_buttons.append(("player1", direction, button))
            
        for i, direction in enumerate(directions):
            x = 3 * SCREEN_WIDTH // 4 - button_width // 2
            y = 200 + i * spacing
            button = Button(x, y, button_width, button_height, 
                          f"Player 2 {direction}: {pygame.key.name(self.controls['player2'][direction])}")
            self.control_buttons.append(("player2", direction, button))
            
        self.reset_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 160, 300, 50, "Đặt lại về mặc định")
        self.back_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 100, 300, 50, "Menu")
        
    def draw_controls_menu(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("Controls", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title_text, title_rect)

        player_font = pygame.font.Font(None, 36)
        player1_text = player_font.render("Player 1", True, WHITE)
        player2_text = player_font.render("Player 2", True, WHITE)
        
        player1_rect = player1_text.get_rect(center=(SCREEN_WIDTH // 4, 120))
        player2_rect = player2_text.get_rect(center=(3 * SCREEN_WIDTH // 4, 120))
        
        surface.blit(player1_text, player1_rect)
        surface.blit(player2_text, player2_rect)

        label_font = pygame.font.Font(None, 32)
        start_y = 180
        spacing = 40

        control_labels = {
            "up": "Move Up",
            "down": "Move Down",
            "left": "Move Left",
            "right": "Move Right",
            "upgrades": "Upgrades"
        }
        
        self.control_buttons = []
        for i, (label, key) in enumerate(self.controls["player1"].items()):
            display_label = control_labels.get(label, label)
            label_text = label_font.render(display_label, True, WHITE)
            key_text = label_font.render(pygame.key.name(key), True, WHITE)
            
            label_rect = label_text.get_rect(midright=(SCREEN_WIDTH // 4 - 20, start_y + i * spacing))
            key_rect = key_text.get_rect(midleft=(SCREEN_WIDTH // 4 + 20, start_y + i * spacing))
            
            surface.blit(label_text, label_rect)
            
            button_width = max(key_rect.width + 40, 100)  
            button = Button(key_rect.x - 20, key_rect.y - 5, button_width, key_rect.height + 10, pygame.key.name(key), GRAY, HIGHLIGHT)
            button.draw(surface)
            self.control_buttons.append(("player1", label, button))

        for i, (label, key) in enumerate(self.controls["player2"].items()):
            display_label = control_labels.get(label, label)
            label_text = label_font.render(display_label, True, WHITE)
            key_text = label_font.render(pygame.key.name(key), True, WHITE)
            
            label_rect = label_text.get_rect(midright=(3 * SCREEN_WIDTH // 4 - 20, start_y + i * spacing))
            key_rect = key_text.get_rect(midleft=(3 * SCREEN_WIDTH // 4 + 20, start_y + i * spacing))
            
            surface.blit(label_text, label_rect)
            
            button_width = max(key_rect.width + 40, 100)  
            button = Button(key_rect.x - 20, key_rect.y - 5, button_width, key_rect.height + 10, pygame.key.name(key), GRAY, HIGHLIGHT)
            button.draw(surface)
            self.control_buttons.append(("player2", label, button))

        reset_button = Button(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 100, 200, 50, "Đặt về mặc định", GRAY, HIGHLIGHT)
        back_button = Button(SCREEN_WIDTH // 2 + 50, SCREEN_HEIGHT - 100, 200, 50, "Menu", GRAY, HIGHLIGHT)
        
        reset_button.draw(surface)
        back_button.draw(surface)

        self.reset_button = reset_button
        self.back_button = back_button

        if self.waiting_for_key:
            message = label_font.render("Nhập phím...", True, WHITE)
            message_rect = message.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(message, message_rect)
            
        mouse_pos = get_virtual_mouse_pos()
        surface.blit(custom_cursor, (mouse_pos[0] - 16, mouse_pos[1] - 16))

    def handle_controls_menu(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = get_virtual_mouse_pos()
            
            for player, direction, button in self.control_buttons:
                if button.is_clicked(mouse_pos, True):
                    self.editing_control = (player, direction)
                    self.waiting_for_key = True
                    return True
                    
            if self.reset_button.is_clicked(mouse_pos, True):
                self.controls = {
                    "player1": {
                        "up": pygame.K_w,
                        "down": pygame.K_s,
                        "left": pygame.K_a,
                        "right": pygame.K_d,
                        "upgrades": pygame.K_e
                    },
                    "player2": {
                        "up": pygame.K_UP,
                        "down": pygame.K_DOWN,
                        "left": pygame.K_LEFT,
                        "right": pygame.K_RIGHT,
                        "upgrades": pygame.K_e
                    }
                }
                self.save_controls()
                return True
                
            elif self.back_button.is_clicked(mouse_pos, True):
                self.state = "menu"
                return True
                
        elif event.type == pygame.KEYDOWN and self.waiting_for_key:
            if self.editing_control:
                player, direction = self.editing_control
                self.controls[player][direction] = event.key
                self.save_controls()
                self.editing_control = None
                self.waiting_for_key = False
                return True
                
        return False
    
    def load_highscores(self):
        try:
            with open('highscores.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"singleplayer": [], "coop": []}
            
    def save_highscores(self):
        with open('highscores.json', 'w') as f:
            json.dump(self.highscores, f, indent=4)
            
    def add_highscore(self, mode, time_seconds):
        hours = int(time_seconds // 3600)
        minutes = int((time_seconds % 3600) // 60)
        seconds = int(time_seconds % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        self.highscores[mode].append({
            "time": time_str,
            "seconds": time_seconds,
            "date": date_str
        })
        
        self.highscores[mode].sort(key=lambda x: x["seconds"], reverse=True)
        self.highscores[mode] = self.highscores[mode][:10]
        
        self.save_highscores()
        
    def draw_leaderboard(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))
        
        title = font.render("Bảng xếp hạng", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        surface.blit(title, title_rect)
        
        header_font = pygame.font.Font(None, 36)
        headers = ["Rank", "Thoi gian", "Ngày"]
        header_spacing = 200
        
        singleplayer_title = header_font.render("Singleplayer", True, WHITE)
        singleplayer_rect = singleplayer_title.get_rect(center=(SCREEN_WIDTH // 4, 150))
        surface.blit(singleplayer_title, singleplayer_rect)
        
        for i, header in enumerate(headers):
            header_text = header_font.render(header, True, WHITE)
            header_rect = header_text.get_rect(center=(SCREEN_WIDTH // 4 - 200 + i * header_spacing, 200))
            surface.blit(header_text, header_rect)
            
        coop_title = header_font.render("Local Coop", True, WHITE)
        coop_rect = coop_title.get_rect(center=(3 * SCREEN_WIDTH // 4, 150))
        surface.blit(coop_title, coop_rect)
        
        for i, header in enumerate(headers):
            header_text = header_font.render(header, True, WHITE)
            header_rect = header_text.get_rect(center=(3 * SCREEN_WIDTH // 4 - 200 + i * header_spacing, 200))
            surface.blit(header_text, header_rect)
        
        y = 240  
        for i in range(10): 
            if i < len(self.highscores["singleplayer"]):
                score = self.highscores["singleplayer"][i]
                rank_text = small_font.render(f"{i+1}.", True, WHITE)
                time_text = small_font.render(score["time"], True, WHITE)
                date_text = small_font.render(score["date"], True, WHITE)
                
                surface.blit(rank_text, (SCREEN_WIDTH // 4 - 200, y))
                surface.blit(time_text, (SCREEN_WIDTH // 4, y))
                surface.blit(date_text, (SCREEN_WIDTH // 4 + 200, y))
            
            if i < len(self.highscores["coop"]):
                score = self.highscores["coop"][i]
                rank_text = small_font.render(f"{i+1}.", True, WHITE)
                time_text = small_font.render(score["time"], True, WHITE)
                date_text = small_font.render(score["date"], True, WHITE)
                
                surface.blit(rank_text, (3 * SCREEN_WIDTH // 4 - 200, y))
                surface.blit(time_text, (3 * SCREEN_WIDTH // 4, y))
                surface.blit(date_text, (3 * SCREEN_WIDTH // 4 + 200, y))
            
            y += 40
        
        back_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 100, 300, 50, "Menu")
        
        clear_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 160, 300, 50, "Xóa toàn bộ")
        
        mouse_pos = get_virtual_mouse_pos()
        back_button.check_hover(mouse_pos)
        clear_button.check_hover(mouse_pos)
        
        back_button.draw(surface)
        clear_button.draw(surface)
        
        if pygame.mouse.get_pressed()[0]:
            if back_button.is_clicked(mouse_pos, True):
                if self.menu_selection_sound:
                    self.menu_selection_sound.play(0)
                self.state = "menu"
            elif clear_button.is_clicked(mouse_pos, True):
                if self.menu_selection_sound:
                    self.menu_selection_sound.play(0)
                self.highscores = {"singleplayer": [], "coop": []}
                self.save_highscores()
                
        if custom_cursor:
            surface.blit(custom_cursor, (mouse_pos[0] - 16, mouse_pos[1] - 16))
    
    def play_menu_music(self):
        if self.menu_music and self.current_music != self.menu_music:
            pygame.mixer.stop()
            self.menu_music.play(-1) 
            self.current_music = self.menu_music
            
    def play_ingame_music(self):
        if self.ingame_music and self.current_music != self.ingame_music:
            pygame.mixer.stop()
            self.ingame_music.play(-1)  
            self.current_music = self.ingame_music
            
    def stop_music(self):
        pygame.mixer.stop()
        self.current_music = None

    def update_music(self):
        if self.state in ["menu", "keybindings", "language", "credits", "leaderboard"]:
            self.play_menu_music()
        elif self.state in ["singleplayer", "coop", "arena"]:
            self.play_ingame_music()
        elif self.state == "gameover":
            if self.current_music:
                self.current_music.stop()
                self.current_music = None

    def create_menu_buttons(self):
        button_height = 50
        button_width = 220
        button_margin = 10
        leave_game_margin = 25
        num_buttons = 6

        total_height = (num_buttons - 1) * (button_height + button_margin) + button_height + leave_game_margin
        start_y = (SCREEN_HEIGHT - total_height) // 2

        self.menu_buttons = []
        labels = [
            "1 nguoi",
            "2 nguoi",
            "Algorithm Arena",
            "Bang xep hang",
            "Dieu khien",
            "Thoat game",
        ]

        for idx, label in enumerate(labels):
            y = start_y + idx * (button_height + button_margin)
            if idx == len(labels) - 1:
                y += leave_game_margin
            self.menu_buttons.append(
                Button(
                    (SCREEN_WIDTH - button_width) // 2,
                    y,
                    button_width,
                    button_height,
                    label,
                )
            )
    def handle_menu_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = get_virtual_mouse_pos()
            for i, button in enumerate(self.menu_buttons):
                if button.is_clicked(mouse_pos, True):
                    if self.menu_selection_sound:
                        self.menu_selection_sound.play()

                    if i == 0:
                        self.state = "hero_selection"
                        self.next_state = "singleplayer"
                        self.hero_selection.set_mode(False)
                    elif i == 1:
                        self.state = "hero_selection"
                        self.next_state = "coop"
                        self.hero_selection.set_mode(True)
                    elif i == 2:
                        self.start_algorithm_arena()
                    elif i == 3:
                        self.state = "leaderboard"
                        self.leaderboard_mode = "singleplayer"
                    elif i == 4:
                        self.state = "keybindings"
                    elif i == 5:
                        pygame.quit()
                        sys.exit()
    def leaderboard_mode_singleplayer(self):
        self.leaderboard_mode = "singleplayer"
        
    def leaderboard_mode_coop(self):
        self.leaderboard_mode = "coop"
    
    def draw_menu(self, surface):
        if self.menu_background:
            surface.blit(self.menu_background, (0, 0))
        else:
            surface.fill(BLACK)
            
        title_font = pygame.font.Font(None, 72)
        shadow_surf = title_font.render("GI Survival", True, (30, 30, 30))
        title_surf = title_font.render("GI Survival", True, (200, 200, 200))
        
        title_x = (SCREEN_WIDTH - title_surf.get_width()) // 2
        title_y = 50
        
        surface.blit(shadow_surf, (title_x + 3, title_y + 3))
        surface.blit(title_surf, (title_x, title_y))
        
        subtitle_font = pygame.font.Font(None, 36)
        subtitle_shadow = subtitle_font.render("yé", True, (30, 30, 30))
        subtitle = subtitle_font.render("yé", True, (200, 200, 200))
        
        subtitle_x = (SCREEN_WIDTH - subtitle.get_width()) // 2
        subtitle_y = title_y + title_surf.get_height() + 10
        
        surface.blit(subtitle_shadow, (subtitle_x + 2, subtitle_y + 2))
        surface.blit(subtitle, (subtitle_x, subtitle_y))
        
        for button in self.menu_buttons:
            button.draw(surface)

    def generate_tree_obstacles(self):
        self.tree_obstacles = []
        self.tree_collision_rects = []
        if not tree_sprites:
            return

        spawn_safe_rect = pygame.Rect(
            WORLD_WIDTH // 2 - TREE_MIN_DISTANCE_FROM_SPAWN,
            WORLD_HEIGHT // 2 - TREE_MIN_DISTANCE_FROM_SPAWN,
            TREE_MIN_DISTANCE_FROM_SPAWN * 2,
            TREE_MIN_DISTANCE_FROM_SPAWN * 2,
        )
        attempts = 0
        max_attempts = TREE_COUNT * 25
        while len(self.tree_obstacles) < TREE_COUNT and attempts < max_attempts:
            attempts += 1
            sprite = random.choice(tree_sprites)
            scale = random.uniform(TREE_VARIATION_SCALE[0], TREE_VARIATION_SCALE[1])
            sprite_w = max(24, int(sprite.get_width() * scale))
            sprite_h = max(24, int(sprite.get_height() * scale))
            x = random.randint(FIELD_X + TREE_PADDING, FIELD_X + WORLD_WIDTH - sprite_w - TREE_PADDING)
            y = random.randint(FIELD_Y + TREE_PADDING, FIELD_Y + WORLD_HEIGHT - sprite_h - TREE_PADDING)
            tree = TreeObstacle(x, y, sprite)

            if tree.rect.colliderect(spawn_safe_rect):
                continue

            too_close = False
            for existing in self.tree_collision_rects:
                if tree.collision_rect.centerx - existing.centerx == 0 and tree.collision_rect.centery - existing.centery == 0:
                    too_close = True
                    break
                dx = tree.collision_rect.centerx - existing.centerx
                dy = tree.collision_rect.centery - existing.centery
                if dx * dx + dy * dy < MIN_TREE_DISTANCE * MIN_TREE_DISTANCE:
                    too_close = True
                    break

            if too_close or collides_with_obstacles(tree.collision_rect, self.tree_collision_rects):
                continue

            self.tree_obstacles.append(tree)
            self.tree_collision_rects.append(tree.collision_rect)

    def get_tree_obstacle_tuples(self):
        return [
            (rect.x, rect.y, rect.width, rect.height)
            for rect in self.tree_collision_rects
        ]

    def draw_trees(self, surface):
        if self.state == "arena" and hasattr(self, "arena_obstacle_rects"):
            for rect in self.arena_obstacle_rects:
                sx, sy = world_to_screen(rect.x, rect.y)
                pygame.draw.rect(surface, (70, 70, 78), (sx, sy, rect.width, rect.height))
            if hasattr(self, "arena_bounds"):
                sx, sy = world_to_screen(self.arena_bounds.x, self.arena_bounds.y)
                pygame.draw.rect(surface, (120, 120, 140), (sx, sy, self.arena_bounds.width, self.arena_bounds.height), 2)
            return

        view_w, view_h = self.get_viewport_size()
        viewport_rect = pygame.Rect(int(CAMERA_X), int(CAMERA_Y), view_w, view_h)
        show_debug = getattr(self, "show_path_debug", False)
        for tree in self.tree_obstacles:
            if tree.rect.colliderect(viewport_rect):
                tree.draw(surface)
                if show_debug:
                    tree.draw_debug(surface)

    def get_camera_focus(self):
        if self.state == "coop" and hasattr(self, "player2"):
            if self.player1.is_dead and not self.player2.is_dead:
                return self.player2
            if self.player2.is_dead and not self.player1.is_dead:
                return self.player1
        return getattr(self, "player1", None)

    def get_viewport_size(self):
        if self.state == "arena":
            zoom = max(0.35, float(getattr(self, "arena_zoom", 1.0)))
            return int(SCREEN_WIDTH / zoom), int(SCREEN_HEIGHT / zoom)
        return SCREEN_WIDTH, SCREEN_HEIGHT

    def update_camera(self):
        global CAMERA_X, CAMERA_Y
        if self.state == "arena" and getattr(self, "arena_locked_camera", True):
            if hasattr(self, "arena_locked_camera_x") and hasattr(self, "arena_locked_camera_y"):
                CAMERA_X = self.arena_locked_camera_x
                CAMERA_Y = self.arena_locked_camera_y
            else:
                CAMERA_X = 0.0
                CAMERA_Y = 0.0
            return

        focus = self.get_camera_focus()
        if not focus:
            return

        view_w, view_h = self.get_viewport_size()
        target_x = focus.x + (focus.sprite_width * focus.scale_factor) / 2 - view_w / 2
        target_y = focus.y + (focus.sprite_height * focus.scale_factor) / 2 - view_h / 2

        max_camera_x = max(0, WORLD_WIDTH - view_w)
        max_camera_y = max(0, WORLD_HEIGHT - view_h)
        target_x = max(0, min(target_x, max_camera_x))
        target_y = max(0, min(target_y, max_camera_y))

        if abs(target_x - CAMERA_X) < CAMERA_DEADZONE:
            target_x = CAMERA_X
        if abs(target_y - CAMERA_Y) < CAMERA_DEADZONE:
            target_y = CAMERA_Y

        CAMERA_X += (target_x - CAMERA_X) * CAMERA_LERP
        CAMERA_Y += (target_y - CAMERA_Y) * CAMERA_LERP

    def _update_arena_free_camera(self, dt):
        global CAMERA_X, CAMERA_Y
        if getattr(self, "arena_locked_camera", True):
            return
        if not hasattr(self, "arena_bounds"):
            return

        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        if keys[K_a] or keys[K_LEFT]:
            dx -= 1
        if keys[K_d] or keys[K_RIGHT]:
            dx += 1
        if keys[K_w] or keys[K_UP]:
            dy -= 1
        if keys[K_s] or keys[K_DOWN]:
            dy += 1

        if dx == 0 and dy == 0:
            return

        cam_speed = 920.0
        if keys[K_LSHIFT] or keys[K_RSHIFT]:
            cam_speed = 1550.0
        CAMERA_X += dx * cam_speed * dt
        CAMERA_Y += dy * cam_speed * dt

        view_w, view_h = self.get_viewport_size()
        min_x = max(0, self.arena_bounds.left - 560)
        max_x = min(WORLD_WIDTH - view_w, self.arena_bounds.right - view_w + 560)
        min_y = max(0, self.arena_bounds.top - 420)
        max_y = min(WORLD_HEIGHT - view_h, self.arena_bounds.bottom - view_h + 420)
        CAMERA_X = max(min_x, min(CAMERA_X, max_x))
        CAMERA_Y = max(min_y, min(CAMERA_Y, max_y))
    
    def start_singleplayer(self):
        global CAMERA_X, CAMERA_Y
        self.monsters = []
        self.last_spawn_time = 0
        self.last_slime2_spawn_time = 0
        self.last_slime3_spawn_time = 0
        
        self.collectables = []
        self.generate_tree_obstacles()
        
        self.player1 = Player(FIELD_X + FIELD_WIDTH // 2, FIELD_Y + FIELD_HEIGHT // 2, 
                            self.controls["player1"], "Player 1", self.hero_selection.heroes['Paimon'])
        CAMERA_X = max(0, min(self.player1.x - SCREEN_WIDTH / 2, WORLD_WIDTH - SCREEN_WIDTH))
        CAMERA_Y = max(0, min(self.player1.y - SCREEN_HEIGHT / 2, WORLD_HEIGHT - SCREEN_HEIGHT))
        self.game_start_time = self.current_time
        self.game_time = 0
        self.total_pause_time = 0
        self.algorithm_selector_open = False
        self.game_over_sound_played = False  
        
    def start_coop(self):
        global CAMERA_X, CAMERA_Y
        self.monsters = []
        self.last_spawn_time = 0
        self.last_slime2_spawn_time = 0
        self.last_slime3_spawn_time = 0
        
        self.collectables = []
        self.generate_tree_obstacles()
        
        self.player1 = Player(FIELD_X + FIELD_WIDTH // 2 - 50, FIELD_Y + FIELD_HEIGHT // 2, 
                            self.controls["player1"], "Player 1", self.hero_selection.heroes['Paimon'])
        self.player2 = Player(FIELD_X + FIELD_WIDTH // 2 + 50, FIELD_Y + FIELD_HEIGHT // 2,
                            self.controls["player2"], "Player 2", self.hero_selection.heroes['Hutao'])
        CAMERA_X = max(0, min(self.player1.x - SCREEN_WIDTH / 2, WORLD_WIDTH - SCREEN_WIDTH))
        CAMERA_Y = max(0, min(self.player1.y - SCREEN_HEIGHT / 2, WORLD_HEIGHT - SCREEN_HEIGHT))
        self.game_start_time = self.current_time
        self.game_time = 0
        self.total_pause_time = 0
        self.algorithm_selector_open = False
        self.game_over_sound_played = False 

    def show_toast(self, message, duration=2.0):
        self.toast_message = message
        self.toast_expire_time = self.current_time + duration

    def get_algorithm_for_type(self, monster_type):
        return normalize_algorithm_key(self.selected_algorithms.get(monster_type, "direct"))

    def set_selected_algorithm(self, monster_type, algorithm_key, show_message=True):
        algorithm_key = normalize_algorithm_key(algorithm_key)
        if algorithm_key not in ALGORITHM_KEYS:
            return
        self.selected_algorithms[monster_type] = algorithm_key
        for monster in self.monsters:
            if monster.monster_type == monster_type:
                monster.movement_algorithm = algorithm_key
                monster.path = []
                monster.path_index = 0
        if show_message:
            display = get_algorithm_display_name(algorithm_key)
            self.show_toast(f"{SLIME_LABELS[monster_type]} đổi thuật toán thành {display}")

    def toggle_algorithm_selector(self):
        self.algorithm_selector_open = not self.algorithm_selector_open
        if self.algorithm_selector_open:
            self.show_toast("Đã mở bảng chọn thuật toán (TAB để đóng)", 1.5)

    def handle_algorithm_selector_input(self, event):
        if event.type != pygame.KEYDOWN:
            return False

        if event.key in (K_TAB, K_ESCAPE, K_RETURN):
            self.toggle_algorithm_selector()
            return True

        if event.key == K_UP:
            self.algorithm_selector_index = (self.algorithm_selector_index - 1) % len(SLIME_TYPES)
            return True
        if event.key == K_DOWN:
            self.algorithm_selector_index = (self.algorithm_selector_index + 1) % len(SLIME_TYPES)
            return True
        if event.key in (K_LEFT, K_RIGHT):
            slime_type = SLIME_TYPES[self.algorithm_selector_index]
            current_key = normalize_algorithm_key(self.selected_algorithms.get(slime_type, "direct"))
            current_idx = ALGORITHM_KEYS.index(current_key)
            delta = -1 if event.key == K_LEFT else 1
            next_key = ALGORITHM_KEYS[(current_idx + delta) % len(ALGORITHM_KEYS)]
            self.set_selected_algorithm(slime_type, next_key, show_message=True)
            return True
        return False

    def draw_algorithm_selector(self, surface):
        if not self.algorithm_selector_open:
            return

        panel_width = 720
        panel_height = 300
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = 90
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (22, 22, 30), panel_rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 220), panel_rect, 2, border_radius=8)

        title = small_font.render("Bảng Chọn Thuật Toán", True, WHITE)
        surface.blit(title, (panel_x + 20, panel_y + 16))
        hint = status_font.render("Lên/Xuống: chọn slime  Trái/Phải: đổi thuật toán  TAB: đóng", True, (200, 200, 210))
        surface.blit(hint, (panel_x + 20, panel_y + 52))

        row_y = panel_y + 95
        row_h = 58
        for index, slime_type in enumerate(SLIME_TYPES):
            selected = index == self.algorithm_selector_index
            row_rect = pygame.Rect(panel_x + 20, row_y + index * row_h, panel_width - 40, row_h - 6)
            base_color = (44, 44, 56) if selected else (33, 33, 44)
            pygame.draw.rect(surface, base_color, row_rect, border_radius=6)
            border_color = (255, 255, 255) if selected else (90, 90, 105)
            pygame.draw.rect(surface, border_color, row_rect, 2, border_radius=6)

            slime_text = status_font.render(SLIME_LABELS[slime_type], True, WHITE)
            surface.blit(slime_text, (row_rect.x + 14, row_rect.y + 16))

            algo_key = normalize_algorithm_key(self.selected_algorithms.get(slime_type, "direct"))
            algo_name = get_algorithm_display_name(algo_key)
            algo_text = status_font.render(algo_name, True, WHITE)
            surface.blit(algo_text, (row_rect.x + 220, row_rect.y + 16))

        if self.algorithm_comparison_mode:
            note = status_font.render("F4 So sánh đang BẬT: game dùng mapping cố định.", True, (255, 230, 130))
            surface.blit(note, (panel_x + 20, panel_y + panel_height - 30))

    def draw_toast(self, surface):
        if not self.toast_message or self.current_time > self.toast_expire_time:
            return
        msg = status_font.render(self.toast_message, True, WHITE)
        padding_x = 16
        padding_y = 10
        width = msg.get_width() + padding_x * 2
        height = msg.get_height() + padding_y * 2
        x = SCREEN_WIDTH // 2 - width // 2
        y = SCREEN_HEIGHT - 120
        box = pygame.Surface((width, height), pygame.SRCALPHA)
        box.fill((20, 20, 20, 185))
        surface.blit(box, (x, y))
        pygame.draw.rect(surface, (220, 220, 220), (x, y, width, height), 1, border_radius=4)
        surface.blit(msg, (x + padding_x, y + padding_y))

    def _pick_arena_algorithms(self):
        keys = list(ALGORITHM_KEYS)
        random.shuffle(keys)
        picked = keys[:ARENA_ZONE_COUNT]
        if len(picked) < ARENA_ZONE_COUNT:
            while len(picked) < ARENA_ZONE_COUNT:
                picked.append(ARENA_ALGORITHMS[len(picked) % len(ARENA_ALGORITHMS)])
        return picked

    def get_arena_bounds(self):
        return ARENA_BASE_RECT.copy()

    def _get_arena_cluster_centers(self):
        bounds = self.arena_bounds
        return [
            (bounds.left + int(bounds.width * 0.18), bounds.top + int(bounds.height * 0.22)),
            (bounds.right - int(bounds.width * 0.18), bounds.top + int(bounds.height * 0.25)),
            (bounds.centerx, bounds.bottom - int(bounds.height * 0.2)),
        ]

    def _build_arena_obstacles(self):
        rng = random.Random(time.time_ns())
        bounds = self.get_arena_bounds()
        self.arena_bounds = bounds
        center = (bounds.centerx, bounds.centery)
        local_obstacles = []
        edge_clear = 55
        attempts = 0
        while len(local_obstacles) < 8 and attempts < 160:
            attempts += 1
            w = rng.randint(58, 105)
            h = rng.randint(46, 88)
            x = rng.randint(bounds.left + edge_clear, bounds.right - w - edge_clear)
            y = rng.randint(bounds.top + edge_clear, bounds.bottom - h - edge_clear)
            rect = pygame.Rect(x, y, w, h)
            if rect.collidepoint(center):
                continue
            if math.hypot(rect.centerx - center[0], rect.centery - center[1]) < 210:
                continue
            center_lane_h = pygame.Rect(bounds.left + 90, bounds.centery - 40, bounds.width - 180, 80)
            center_lane_v = pygame.Rect(bounds.centerx - 36, bounds.top + 90, 72, bounds.height - 180)
            if rect.colliderect(center_lane_h) or rect.colliderect(center_lane_v):
                continue
            local_obstacles.append(rect)

        self.arena_obstacle_rects = local_obstacles
        self.arena_cluster_centers = self._get_arena_cluster_centers()

    def _spawn_arena_monster(self, monster_type, zone_idx, algorithm_key):
        cx, cy = self.arena_cluster_centers[zone_idx]
        target = self.arena_zone_targets[zone_idx]
        x = cx
        y = cy
        for _ in range(35):
            ang = random.uniform(0, math.tau)
            rad = random.randint(110, 290)
            x = int(cx + math.cos(ang) * rad)
            y = int(cy + math.sin(ang) * rad)
            x = max(self.arena_bounds.left + 38, min(x, self.arena_bounds.right - 38))
            y = max(self.arena_bounds.top + 38, min(y, self.arena_bounds.bottom - 38))
            if math.hypot(x - target.x, y - target.y) < 125:
                continue
            monster_box = pygame.Rect(x - 46, y - 46, 92, 92)
            blocked = any(monster_box.colliderect(obst) for obst in self.arena_obstacle_rects)
            if not blocked:
                break

        monster = Monster(x, y, target, self.game_time, monster_type)
        monster.movement_algorithm = algorithm_key
        monster.arena_zone_idx = zone_idx
        monster.arena_algorithm = algorithm_key
        monster.ignore_monster_obstacles = True
        monster.ignore_monster_collisions = True
        monster.path_obstacle_clearance = 14
        monster.path_update_interval = random.uniform(0.35, 0.6)
        self.monsters.append(monster)

    def _ensure_arena_population(self):
        counts = {}
        for zone_idx in range(ARENA_ZONE_COUNT):
            counts[zone_idx] = {"slime1": 0, "slime2": 0, "slime3": 0}
        for monster in self.monsters:
            zone_idx = getattr(monster, "arena_zone_idx", -1)
            if zone_idx in counts and monster.monster_type in counts[zone_idx]:
                counts[zone_idx][monster.monster_type] += 1

        per_type_target = max(1, ARENA_MONSTERS_PER_ZONE // 3)
        zone_algorithms = getattr(self, "arena_zone_algorithms", ARENA_ALGORITHMS)
        for zone_idx in range(ARENA_ZONE_COUNT):
            algo = zone_algorithms[zone_idx % len(zone_algorithms)]
            for monster_type in ["slime1", "slime2", "slime3"]:
                while counts[zone_idx][monster_type] < per_type_target:
                    self._spawn_arena_monster(monster_type, zone_idx, algo)
                    counts[zone_idx][monster_type] += 1

    def _record_arena_replay_snapshot(self):
        snapshot = []
        for monster in self.monsters:
            snapshot.append(
                (
                    monster.x,
                    monster.y,
                    monster.direction,
                    getattr(monster, "arena_zone_idx", 0),
                    getattr(monster, "arena_algorithm", monster.movement_algorithm),
                )
            )
        self.arena_replay_buffer.append(snapshot)

    def _apply_arena_replay_snapshot(self, snapshot):
        max_len = min(len(snapshot), len(self.monsters))
        for idx in range(max_len):
            monster = self.monsters[idx]
            mx, my, direction, zone_idx, algo = snapshot[idx]
            monster.x = mx
            monster.y = my
            monster.direction = direction
            monster.arena_zone_idx = zone_idx
            monster.movement_algorithm = algo

    def toggle_arena_replay(self):
        if self.arena_replay_active:
            self.arena_replay_active = False
            self.show_toast("Phat lai: Tat")
            return
        if len(self.arena_replay_buffer) < 4:
            self.show_toast("Chua du du lieu phat lai")
            return
        self.arena_replay_active = True
        self.arena_replay_cursor = 0
        self.show_toast("Phat lai: Bat")

    def cycle_arena_slow_motion(self):
        self.arena_time_scale_index = (self.arena_time_scale_index + 1) % len(ARENA_SLOW_MOTION_LEVELS)
        self.arena_time_scale = ARENA_SLOW_MOTION_LEVELS[self.arena_time_scale_index]
        self.show_toast(f"Toc do x{self.arena_time_scale:.2f}")

    def toggle_arena_target_mode(self):
        self.arena_mode_same_target = not self.arena_mode_same_target
        mode = "Chung" if self.arena_mode_same_target else "Rieng"
        self.show_toast(f"Muc tieu: {mode}")

    def randomize_algorithm_arena(self):
        self.arena_zone_algorithms = self._pick_arena_algorithms()
        self._build_arena_obstacles()
        center_x = self.arena_bounds.centerx
        center_y = self.arena_bounds.centery
        self.arena_zone_targets = [ArenaTarget(center_x, center_y) for _ in range(ARENA_ZONE_COUNT)]
        self.monsters = []
        self._ensure_arena_population()
        self.arena_replay_buffer.clear()
        self.arena_replay_active = False
        self.arena_replay_cursor = 0
        self.arena_replay_accumulator = 0.0
        view_w, view_h = self.get_viewport_size()
        self.arena_locked_camera_x = max(0, min(self.arena_bounds.centerx - view_w / 2, WORLD_WIDTH - view_w))
        self.arena_locked_camera_y = max(0, min(self.arena_bounds.centery - view_h / 2, WORLD_HEIGHT - view_h))
        self.show_toast("Da tao map moi")

    def start_algorithm_arena(self):
        global CAMERA_X, CAMERA_Y
        self.ensure_runtime_state()
        self.state = "arena"
        self.monsters = []
        self.collectables = []
        self.show_path_debug = True
        self.algorithm_selector_open = False
        self.upgrade_menu.is_open = False
        self.game_start_time = self.current_time
        self.game_time = 0.0
        self.total_pause_time = 0.0
        self.pause_start_time = 0.0
        self.arena_time_scale_index = 0
        self.arena_time_scale = ARENA_SLOW_MOTION_LEVELS[0]
        self.arena_locked_camera = True
        self.arena_zone_algorithms = self._pick_arena_algorithms()
        self.arena_replay_buffer.clear()
        self.arena_replay_active = False
        self.arena_replay_cursor = 0
        self.arena_replay_accumulator = 0.0
        self.arena_zone_targets = []
        self._build_arena_obstacles()
        center_x = self.arena_bounds.centerx
        center_y = self.arena_bounds.centery
        for _ in range(ARENA_ZONE_COUNT):
            self.arena_zone_targets.append(ArenaTarget(center_x, center_y))
        self._ensure_arena_population()
        self.arena_new_button = Button(SCREEN_WIDTH - 220, 24, 190, 36, "Map moi")
        view_w, view_h = self.get_viewport_size()
        self.arena_locked_camera_x = max(0, min(self.arena_bounds.centerx - view_w / 2, WORLD_WIDTH - view_w))
        self.arena_locked_camera_y = max(0, min(self.arena_bounds.centery - view_h / 2, WORLD_HEIGHT - view_h))
        CAMERA_X = self.arena_locked_camera_x
        CAMERA_Y = self.arena_locked_camera_y

    def update_arena(self, dt):
        if not hasattr(self, "arena_bounds"):
            self.start_algorithm_arena()
            return
        self._update_arena_free_camera(dt)

        if self.arena_replay_active:
            self.arena_replay_accumulator += dt
            if self.arena_replay_accumulator >= self.arena_replay_frame_interval:
                self.arena_replay_accumulator = 0.0
                if self.arena_replay_cursor >= len(self.arena_replay_buffer):
                    self.arena_replay_active = False
                    self.show_toast("Da phat lai xong")
                else:
                    self._apply_arena_replay_snapshot(self.arena_replay_buffer[self.arena_replay_cursor])
                    self.arena_replay_cursor += 1
            return

        scaled_dt = dt * self.arena_time_scale
        self.game_time += scaled_dt
        self._ensure_arena_population()
        center_x = self.arena_bounds.centerx
        center_y = self.arena_bounds.centery

        if self.arena_mode_same_target:
            for target in self.arena_zone_targets:
                target.x = center_x
                target.y = center_y
        else:
            for idx in range(ARENA_ZONE_COUNT):
                target = self.arena_zone_targets[idx]
                radius = 55 + idx * 18
                ang = self.current_time * (0.8 + 0.15 * idx) + idx * 2.1
                target.x = center_x + math.cos(ang) * radius
                target.y = center_y + math.sin(ang * 1.07) * radius * 0.8

        for monster in self.monsters[:]:
            zone_idx = getattr(monster, "arena_zone_idx", 0)
            if zone_idx < 0 or zone_idx >= len(self.arena_zone_targets):
                zone_idx = 0
            target = self.arena_zone_targets[zone_idx]
            monster.target = target
            monster.environment_obstacles = self.arena_obstacle_rects
            monster.environment_obstacle_tuples = [(r.x, r.y, r.width, r.height) for r in self.arena_obstacle_rects]

            # Arena-only behavior: quái chạm mục tiêu thì biến mất để vòng mới spawn liên tục.
            monster_center_x = monster.x + (monster.sprite_width * monster.scale_factor) * 0.5
            monster_center_y = monster.y + (monster.sprite_height * monster.scale_factor) * 0.5
            target_center_x = target.x + (target.sprite_width * target.scale_factor) * 0.5
            target_center_y = target.y + (target.sprite_height * target.scale_factor) * 0.5
            if math.hypot(monster_center_x - target_center_x, monster_center_y - target_center_y) <= 42:
                self.monsters.remove(monster)
                continue

            should_remove = monster.update(scaled_dt, [target], self.monsters, self.current_time)
            if should_remove:
                self.monsters.remove(monster)

        # Bù quái ngay trong Arena, không ảnh hưởng mode khác.
        self._ensure_arena_population()

        self.arena_replay_accumulator += dt
        if self.arena_replay_accumulator >= self.arena_replay_frame_interval:
            self.arena_replay_accumulator = 0.0
            self._record_arena_replay_snapshot()

    def draw_arena_overlay(self, surface):
        title = status_font.render("Dau truong thuat toan", True, WHITE)
        surface.blit(title, (24, 24))

        self.arena_new_button.draw(surface)
        hint = status_font.render("R: Map moi  Y: Phat lai  M: Toc do  T: Muc tieu  C: Camera", True, WHITE)
        surface.blit(hint, (24, 52))

        mode = "Chung" if self.arena_mode_same_target else "Rieng"
        replay = "Bat" if self.arena_replay_active else "Tat"
        cam = "Khoa" if self.arena_locked_camera else "Tu do"
        state = status_font.render(
            f"Toc do x{self.arena_time_scale:.2f} | Muc tieu {mode} | Phat lai {replay} | Camera {cam}",
            True,
            WHITE,
        )
        surface.blit(state, (24, 76))
        zone_algorithms = getattr(self, "arena_zone_algorithms", ARENA_ALGORITHMS)
        zone_text = " | ".join(
            [
                f"Nhom {idx + 1}: {get_algorithm_display_name(zone_algorithms[idx % len(zone_algorithms)])}"
                for idx in range(ARENA_ZONE_COUNT)
            ]
        )
        surface.blit(status_font.render(zone_text, True, WHITE), (24, 98))

        table_rect = pygame.Rect(24, SCREEN_HEIGHT - 175, 620, 145)
        pygame.draw.rect(surface, (14, 14, 22), table_rect)
        pygame.draw.rect(surface, (200, 200, 220), table_rect, 1)
        headers = ["Thuat toan", "SL", "TB ms", "Node", "Do dai", "Ty le"]
        hx = [10, 120, 200, 300, 390, 490]
        for idx, head in enumerate(headers):
            surface.blit(stats_font.render(head, True, WHITE), (table_rect.x + hx[idx], table_rect.y + 8))

        stats = {}
        for key in ALGORITHM_KEYS:
            stats[key] = {"count": 0, "ms": 0.0, "nodes": 0.0, "path": 0.0, "success": 0.0}
        for monster in self.monsters:
            key = normalize_algorithm_key(getattr(monster, "movement_algorithm", "direct"))
            metric = getattr(monster, "path_metrics", {})
            row = stats[key]
            row["count"] += 1
            row["ms"] += float(metric.get("calculation_time_ms", 0.0))
            row["nodes"] += float(metric.get("nodes_visited", 0.0))
            row["path"] += float(metric.get("path_length", 0.0))
            row["success"] += float(metric.get("success_rate", 0.0))

        for idx, key in enumerate(ALGORITHM_KEYS):
            row = stats[key]
            count = max(1, row["count"])
            y = table_rect.y + 30 + idx * 18
            values = [
                get_algorithm_display_name(key),
                str(row["count"]),
                f"{row['ms']/count:.2f}",
                f"{row['nodes']/count:.0f}",
                f"{row['path']/count:.0f}",
                f"{(row['success']/count)*100:.0f}%",
            ]
            for col, value in enumerate(values):
                color = ARENA_ALGO_COLORS.get(key, WHITE) if col == 0 else WHITE
                surface.blit(stats_font.render(value, True, color), (table_rect.x + hx[col], y))
    
    def spawn_monster(self, current_time):
        if self.upgrade_menu.is_open or self.algorithm_selector_open:
            return

        import math
        monsters_per_second = math.exp(self.game_time / 433)  

        spawn_rate = 1 / monsters_per_second if monsters_per_second > 0 else 1
        
        if current_time - self.last_spawn_time >= spawn_rate:
            spawn_pos = self.find_valid_spawn_position()
            if spawn_pos:
                x, y = spawn_pos
                closest_player = self.find_closest_living_player(x, y)
                if closest_player: 
                    new_monster = Monster(x, y, closest_player, self.game_time, 'slime1')
                    new_monster.movement_algorithm = self.get_algorithm_for_type("slime1")
                    self.monsters.append(new_monster)
                    self.last_spawn_time = current_time
        
        slime2_rate = 6 if self.state == "coop" else SLIME2_SPAWN_RATE  
        slime3_rate = 35 if self.state == "coop" else SLIME3_SPAWN_RATE 
        
        if current_time - self.last_slime2_spawn_time >= slime2_rate and self.last_slime2_spawn_time > 0:
            spawn_pos = self.find_valid_spawn_position()
            if spawn_pos:
                x, y = spawn_pos
                closest_player = self.find_closest_living_player(x, y)
                if closest_player: 
                    new_monster = Monster(x, y, closest_player, self.game_time, 'slime2')
                    new_monster.movement_algorithm = self.get_algorithm_for_type("slime2")
                    self.monsters.append(new_monster)
                    self.last_slime2_spawn_time = current_time
        elif self.last_slime2_spawn_time == 0:
            self.last_slime2_spawn_time = current_time
                    
        if current_time - self.last_slime3_spawn_time >= slime3_rate and self.last_slime3_spawn_time > 0:
            spawn_pos = self.find_valid_spawn_position()
            if spawn_pos:
                x, y = spawn_pos
                closest_player = self.find_closest_living_player(x, y)
                if closest_player: 
                    new_monster = Monster(x, y, closest_player, self.game_time, 'slime3')
                    new_monster.movement_algorithm = self.get_algorithm_for_type("slime3")
                    self.monsters.append(new_monster)
                    self.last_slime3_spawn_time = current_time
        elif self.last_slime3_spawn_time == 0:

            self.last_slime3_spawn_time = current_time
    
    def find_valid_spawn_position(self):
        """Tìm kiếm vị trí sinh sản của quái vậtt"""
        side = random.randint(0, 3)

        view_left = int(CAMERA_X)
        view_top = int(CAMERA_Y)
        view_right = view_left + SCREEN_WIDTH
        view_bottom = view_top + SCREEN_HEIGHT

        if side == 0:
            x = random.randint(view_left, view_right)
            y = view_top - MONSTER_SPAWN_DISTANCE
        elif side == 1:
            x = view_right + MONSTER_SPAWN_DISTANCE
            y = random.randint(view_top, view_bottom)
        elif side == 2:
            x = random.randint(view_left, view_right)
            y = view_bottom + MONSTER_SPAWN_DISTANCE
        else:
            x = view_left - MONSTER_SPAWN_DISTANCE
            y = random.randint(view_top, view_bottom)

        x = max(0, min(x, WORLD_WIDTH))
        y = max(0, min(y, WORLD_HEIGHT))
        
        valid_position = True
        
        if not self.player1.is_dead:
            dx = x - self.player1.x
            dy = y - self.player1.y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < MONSTER_SPAWN_DISTANCE:
                valid_position = False
        
        if self.state == "coop" and hasattr(self, 'player2') and not self.player2.is_dead:
            dx = x - self.player2.x
            dy = y - self.player2.y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < MONSTER_SPAWN_DISTANCE:
                valid_position = False
        
        if valid_position:
            return (x, y)
        return None
    
    def find_closest_living_player(self, x, y):
        closest_player = None
        closest_distance = float('inf')
        
        if not self.player1.is_dead:
            dx = self.player1.x - x
            dy = self.player1.y - y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < closest_distance:
                closest_distance = distance
                closest_player = self.player1
        
        if self.state == "coop" and hasattr(self, 'player2') and not self.player2.is_dead:
            dx = x - self.player2.x
            dy = y - self.player2.y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < closest_distance:
                closest_distance = distance
                closest_player = self.player2
        
        return closest_player
    
    def update_collectables(self, dt):
        if self.upgrade_menu.is_open or self.algorithm_selector_open:
            return
            
        for collectable in self.collectables:
            collectable.update(dt)
            
        if self.state == "singleplayer":
            for collectable in self.collectables[:]:
                if collectable.is_collected:
                    if collectable.is_collection_complete():
                        if collectable.type == 0:
                            gold_value = int(COIN_VALUE * collectable.collected_by.gold_multiplier)
                            collectable.collected_by.gold += gold_value
                            collectable.collected_by.total_gold_received += gold_value
                        elif collectable.type == 1:
                            collectable.collected_by.gain_xp(XP_ORB_VALUE)
                        elif collectable.type == 2:
                            collectable.collected_by.gain_xp(25)
                        elif collectable.type == 3:
                            collectable.collected_by.gain_xp(50)
                        if self.collect_sound:
                            self.collect_sound.play()
                        self.collectables.remove(collectable)
                else:
                    if collectable.check_collection(self.player1):
                        pass
        elif self.state == "coop" and hasattr(self, 'player2'):
            for collectable in self.collectables[:]:
                if collectable.is_collected:
                    if collectable.is_collection_complete():
                        if collectable.type == 0:
                            gold_value = int(COIN_VALUE * collectable.collected_by.gold_multiplier)
                            collectable.collected_by.gold += gold_value
                            collectable.collected_by.total_gold_received += gold_value
                            other_player = self.player2 if collectable.collected_by == self.player1 else self.player1
                            if other_player.health > 0:
                                shared_gold = int(gold_value * 0.5)
                                other_player.gold += shared_gold
                                other_player.total_gold_received += shared_gold
                        elif collectable.type == 1:
                            collectable.collected_by.gain_xp(XP_ORB_VALUE)
                            other_player = self.player2 if collectable.collected_by == self.player1 else self.player1
                            if other_player.health > 0:
                                shared_xp = int(XP_ORB_VALUE * 0.5)
                                other_player.gain_xp(shared_xp)
                        elif collectable.type == 2:
                            collectable.collected_by.gain_xp(25)
                            other_player = self.player2 if collectable.collected_by == self.player1 else self.player1
                            if other_player.health > 0:
                                shared_xp = int(25 * 0.5)
                                other_player.gain_xp(shared_xp)
                        elif collectable.type == 3:
                            collectable.collected_by.gain_xp(50)
                            other_player = self.player2 if collectable.collected_by == self.player1 else self.player1
                            if other_player.health > 0:
                                shared_xp = int(50 * 0.5)
                                other_player.gain_xp(shared_xp)
                        if self.collect_sound:
                            self.collect_sound.play()
                        self.collectables.remove(collectable)
                else:
                    if collectable.check_collection(self.player1) or collectable.check_collection(self.player2):
                        pass
    
    def draw_collectables(self, surface):
        viewport_rect = pygame.Rect(int(CAMERA_X), int(CAMERA_Y), SCREEN_WIDTH, SCREEN_HEIGHT)
        for collectable in self.collectables:
            collectable_rect = pygame.Rect(int(collectable.x), int(collectable.y), COLLECTABLE_SIZE, COLLECTABLE_SIZE)
            if collectable_rect.colliderect(viewport_rect):
                collectable.draw(surface)
            
    def update_monsters(self, dt):
        if self.upgrade_menu.is_open or self.algorithm_selector_open:
            return
            
        players = []
        if self.state == "singleplayer":
            players.append(self.player1)
        elif self.state == "coop":
            players.append(self.player1)
            players.append(self.player2)
            
        for monster in self.monsters[:]:
            monster.environment_obstacles = self.tree_collision_rects
            monster.environment_obstacle_tuples = self.get_tree_obstacle_tuples()
            should_remove = monster.update(dt, players, self.monsters, self.current_time)
            if should_remove:
                collectables = monster.drop_collectable()
                for collectable in collectables:
                    self.collectables.append(collectable)
                self.monsters.remove(monster)
    
    def draw_timer(self, surface):
        minutes = int(self.game_time // 60)
        seconds = int(self.game_time % 60)
        time_text = f"{minutes:02d}:{seconds:02d}"
        
        timer_bg = pygame.Surface((120, 40), pygame.SRCALPHA)
        timer_bg.fill((*UI_BG_COLOR, UI_BG_ALPHA))
        
        timer_surf = timer_font.render(time_text, True, BLACK)
        timer_rect = timer_surf.get_rect(center=(60, 20))
        timer_bg.blit(timer_surf, timer_rect)
        
        surface.blit(timer_bg, (SCREEN_WIDTH // 2 - 60, 20))
        
        if self.upgrade_menu.is_open or self.algorithm_selector_open:
            pause_text = small_font.render("Tạm Dừng", True, (255, 0, 0))
            pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, 70))
            surface.blit(pause_text, pause_rect)
    
    def draw_gold(self, surface, x, y, player=None):
        gold_bg = pygame.Surface((150, 60), pygame.SRCALPHA)  
        medium_bg_color = (80, 80, 80)  
        gold_bg.fill((*medium_bg_color, UI_BG_ALPHA))
        
        if player:
            if self.state == "coop":
                if player == self.player1:
                    name_color = (0, 0, 255)  
                else:
                    name_color = (255, 0, 0)  
            else:
                name_color = WHITE  
                
            name_surf = status_font.render(player.name, True, name_color)
            name_rect = name_surf.get_rect(center=(75, 20))  
            gold_bg.blit(name_surf, name_rect)
            
            if gold_icon:
                icon_width = gold_icon.get_width()
                gold_surf = status_font.render(f"{player.gold}", True, name_color)
                text_width = gold_surf.get_width()
                
                total_width = icon_width + text_width + 5  
                
                start_x = (150 - total_width) // 2
                
                gold_bg.blit(gold_icon, (start_x, 31)) 
                gold_bg.blit(gold_surf, (start_x + icon_width + 5, 40)) 
        else:
            name_surf = status_font.render("Muc tieu", True, WHITE)  
            name_rect = name_surf.get_rect(center=(75, 20))  
            gold_bg.blit(name_surf, name_rect)
            
            if gold_icon:
                icon_width = gold_icon.get_width()
                gold_surf = status_font.render(f"{self.shared_gold if self.state == 'coop' else self.player1.gold}", True, WHITE)  # Use white for better contrast
                text_width = gold_surf.get_width()
                
                total_width = icon_width + text_width + 5  
                
                start_x = (150 - total_width) // 2
                
                gold_bg.blit(gold_icon, (start_x, 31))  
                gold_bg.blit(gold_surf, (start_x + icon_width + 5, 40))  
        
        surface.blit(gold_bg, (x, y))
    
    def draw_game(self, surface):
        dt = clock.get_time() / 1000.0
        if self.state == "arena":
            self.update_camera()
            self.update_arena(dt)

            view_w, view_h = self.get_viewport_size()
            if (
                not hasattr(self, "_arena_world_surface")
                or self._arena_world_surface.get_width() != view_w
                or self._arena_world_surface.get_height() != view_h
            ):
                self._arena_world_surface = pygame.Surface((view_w, view_h)).convert()
            world_surface = self._arena_world_surface
            world_surface.fill(BLACK)
        else:
            world_surface = surface
            world_surface.fill(BLACK)

        view_w, view_h = self.get_viewport_size()
        start_tile_x = int(CAMERA_X // TILE_SIZE)
        start_tile_y = int(CAMERA_Y // TILE_SIZE)
        end_tile_x = int((CAMERA_X + view_w) // TILE_SIZE) + 1
        end_tile_y = int((CAMERA_Y + view_h) // TILE_SIZE) + 1

        for ty in range(start_tile_y, end_tile_y):
            for tx in range(start_tile_x, end_tile_x):
                world_x = tx * TILE_SIZE
                world_y = ty * TILE_SIZE
                if 0 <= world_x < WORLD_WIDTH and 0 <= world_y < WORLD_HEIGHT:
                    draw_x, draw_y = world_to_screen(world_x, world_y)
                    world_surface.blit(tile, (draw_x, draw_y))

        self.draw_trees(world_surface)
        
        if self.state == "singleplayer":
            self.update_players(dt)
            self.update_camera()
            self.player1.draw(world_surface)
            self.draw_gold(world_surface, 20, 20, self.player1)  
            self.update_monsters(dt)
            self.draw_monsters(world_surface)
            self.update_collectables(dt)
            self.draw_collectables(world_surface)
        elif self.state == "coop":
            self.update_players(dt)
            self.update_camera()
            
            circle_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            
            player1_center_x = self.player1.x + (self.player1.sprite_width * self.player1.scale_factor) / 2
            player1_center_y = self.player1.y + (self.player1.sprite_height * self.player1.scale_factor) / 2
            p1_draw_x, p1_draw_y = world_to_screen(player1_center_x, player1_center_y)
            pygame.draw.circle(circle_surface, (0, 0, 255, 51), (int(p1_draw_x), int(p1_draw_y)), 
                              int((self.player1.sprite_width * self.player1.scale_factor / 2 + 5) * 0.5), 3)
            
            player2_center_x = self.player2.x + (self.player2.sprite_width * self.player2.scale_factor) / 2
            player2_center_y = self.player2.y + (self.player2.sprite_height * self.player2.scale_factor) / 2
            p2_draw_x, p2_draw_y = world_to_screen(player2_center_x, player2_center_y)
            pygame.draw.circle(circle_surface, (255, 0, 0, 51), (int(p2_draw_x), int(p2_draw_y)), 
                              int((self.player2.sprite_width * self.player2.scale_factor / 2 + 5) * 0.5), 3)
            
            world_surface.blit(circle_surface, (0, 0))
            
            self.player1.draw(world_surface)
            self.player2.draw(world_surface)
            
            if self.player1.is_dead:
                self.player1.draw_respawn_timer(world_surface, self.current_time)
            if self.player2.is_dead:
                self.player2.draw_respawn_timer(world_surface, self.current_time)
                
            self.draw_gold(world_surface, 20, 20, self.player1)  
            self.draw_gold(world_surface, SCREEN_WIDTH - 170, 20, self.player2)  
            
            self.update_monsters(dt)
            self.draw_monsters(world_surface)
            self.update_collectables(dt)
            self.draw_collectables(world_surface)
        elif self.state == "arena":
            for target in getattr(self, "arena_zone_targets", []):
                tx, ty = world_to_screen(target.x, target.y)
                pygame.draw.circle(world_surface, (248, 248, 248), (int(tx), int(ty)), 10)
                pygame.draw.circle(world_surface, (40, 40, 40), (int(tx), int(ty)), 10, 2)
                pygame.draw.circle(world_surface, (50, 120, 255), (int(tx), int(ty - 12)), 5)
                label = status_font.render("Muc tieu", True, WHITE)
                world_surface.blit(label, (int(tx - label.get_width() // 2), int(ty - 32)))
            self.draw_monsters(world_surface)
            surface.blit(pygame.transform.smoothscale(world_surface, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))

        if self.state != "arena":
            self.draw_timer(world_surface)
        else:
            self.draw_timer(surface)

    def draw_monsters(self, surface):
        show_path_debug = getattr(self, "show_path_debug", SHOW_PATH_DEBUG)
        view_w, view_h = self.get_viewport_size()
        viewport_rect = pygame.Rect(int(CAMERA_X), int(CAMERA_Y), view_w, view_h)
        for monster in self.monsters:
            sprite_w = int(monster.sprite_width * monster.scale_factor)
            sprite_h = int(monster.sprite_height * monster.scale_factor)
            monster_rect = pygame.Rect(int(monster.x), int(monster.y), sprite_w, sprite_h)
            if not monster_rect.colliderect(viewport_rect):
                continue
            monster.show_path_debug = show_path_debug
            monster.camera_offset_x = CAMERA_X
            monster.camera_offset_y = CAMERA_Y
            monster.draw(surface)

    def apply_algorithm_mode(self):
        for monster in self.monsters:
            monster.movement_algorithm = self.get_algorithm_for_type(monster.monster_type)
            monster.path = []
            monster.path_index = 0

    def draw_debug_metrics(self, surface):
        show_path_debug = getattr(self, "show_path_debug", SHOW_PATH_DEBUG)
        if not show_path_debug:
            return

        cache_interval = 0.35
        now = self.current_time
        if not hasattr(self, "_debug_metrics_cache_until"):
            self._debug_metrics_cache_until = 0.0
            self._debug_metrics_cache_surface = None

        if self._debug_metrics_cache_surface is None or now >= self._debug_metrics_cache_until:
            table_w = 620
            header_h = 24
            row_h = 22
            rows = len(ALGORITHM_KEYS)
            table_h = 95 + header_h + rows * row_h + 8

            panel = pygame.Surface((table_w, table_h), pygame.SRCALPHA)
            panel.fill((12, 12, 18, 165))

            fps_text = status_font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
            total_text = status_font.render(f"Số lượng slime: {len(self.monsters)}", True, WHITE)
            mode = "BẬT" if getattr(self, "algorithm_comparison_mode", False) else "TẮT"
            mode_text = status_font.render(f"F3 Debug: BẬT | F4 So sánh: {mode}", True, WHITE)
            panel.blit(fps_text, (10, 8))
            panel.blit(total_text, (10, 30))
            panel.blit(mode_text, (10, 52))

            stats_by_algorithm = {}
            for key in ALGORITHM_KEYS:
                stats_by_algorithm[key] = {
                    "count": 0,
                    "sum_ms": 0.0,
                    "sum_nodes": 0.0,
                    "sum_path": 0.0,
                    "sum_success": 0.0,
                }

            for monster in self.monsters:
                key = normalize_algorithm_key(getattr(monster, "movement_algorithm", "direct"))
                metrics = getattr(monster, "path_metrics", {})
                row = stats_by_algorithm[key]
                row["count"] += 1
                row["sum_ms"] += float(metrics.get("calculation_time_ms", 0.0))
                row["sum_nodes"] += float(metrics.get("nodes_visited", 0.0))
                row["sum_path"] += float(metrics.get("path_length", 0.0))
                row["sum_success"] += float(metrics.get("success_rate", 0.0))

            table_y = 88
            pygame.draw.rect(panel, (220, 220, 230), (0, table_y, table_w, table_h - table_y), 1)
            headers = ["Thuật toán", "Số lượng", "TB ms", "TB node", "TB path", "Thành công"]
            header_x = [10, 170, 240, 330, 440, 530]
            for idx, header in enumerate(headers):
                text = stats_font.render(header, True, (235, 235, 235))
                panel.blit(text, (header_x[idx], table_y + 4))

            algo_color = {
                "direct": (255, 220, 0),
                "astar": (255, 80, 80),
                "bfs": (80, 170, 255),
                "dijkstra": (180, 90, 255),
                "greedy": (90, 220, 120),
                "hill_climbing": (255, 120, 180),
            }
            for idx, key in enumerate(ALGORITHM_KEYS):
                row_y = table_y + header_h + idx * row_h
                data = stats_by_algorithm[key]
                count = data["count"]
                if count > 0:
                    avg_ms = data["sum_ms"] / count
                    avg_nodes = data["sum_nodes"] / count
                    avg_path = data["sum_path"] / count
                    avg_success = (data["sum_success"] / count) * 100.0
                else:
                    avg_ms = avg_nodes = avg_path = avg_success = 0.0

                values = [
                    get_algorithm_display_name(key),
                    str(count),
                    f"{avg_ms:.2f}",
                    f"{avg_nodes:.0f}",
                    f"{avg_path:.0f}",
                    f"{avg_success:.0f}%",
                ]
                for col, value in enumerate(values):
                    text_color = algo_color.get(key, WHITE) if col == 0 else WHITE
                    text = stats_font.render(value, True, text_color)
                    panel.blit(text, (header_x[col], row_y + 3))

            self._debug_metrics_cache_surface = panel
            self._debug_metrics_cache_until = now + cache_interval

        surface.blit(self._debug_metrics_cache_surface, (20, 20))
            
    def update_players(self, dt):
        if self.state == "singleplayer":
            if self.upgrade_menu.is_open or self.algorithm_selector_open:
                return
            self.player1.environment_obstacles = self.tree_collision_rects
            self.player1.update(dt, self.monsters, self.current_time)
            
            if self.player1.health <= 0 and not self.player1.is_dead:
                self.player1.is_dead = True
                self.player1.death_time = self.current_time
                self.add_highscore("singleplayer", self.game_time)
                self.state = "gameover"
                if self.game_over_sound and not self.game_over_sound_played:
                    self.game_over_sound.play(0)  
                    self.game_over_sound_played = True
                
        elif self.state == "coop":
            if self.upgrade_menu.is_open or self.algorithm_selector_open:
                return
            self.player1.environment_obstacles = self.tree_collision_rects
            self.player2.environment_obstacles = self.tree_collision_rects
            self.player1.update(dt, self.monsters, self.current_time, self.player2)
            self.player2.update(dt, self.monsters, self.current_time, self.player1)
            
            if self.player1.health <= 0 and not self.player1.is_dead:
                self.player1.is_dead = True
                self.player1.death_time = self.current_time
                
            if self.player2.health <= 0 and not self.player2.is_dead:
                self.player2.is_dead = True
                self.player2.death_time = self.current_time
                
            if self.player1.is_dead and self.player2.is_dead:
                self.add_highscore("coop", self.game_time)
                self.state = "gameover"
                if self.game_over_sound and not self.game_over_sound_played:
                    self.game_over_sound.play(0)  
                    self.game_over_sound_played = True
    
    def draw(self, surface):
        self.update_music()
        
        if self.state == "menu":
            self.draw_menu(surface)
        elif self.state == "hero_selection":
            self.hero_selection.draw(surface)
        elif self.state in ["singleplayer", "coop", "arena"]:
            self.draw_game(surface)
            if self.state in ["singleplayer", "coop"]:
                self.draw_debug_metrics(surface)
            if self.state in ["singleplayer", "coop"]:
                self.draw_algorithm_selector(surface)
            if self.state == "arena":
                self.draw_arena_overlay(surface)
            self.draw_toast(surface)
            if self.upgrade_menu.is_open and self.state in ["singleplayer", "coop"]:
                if self.state == "coop":
                    self.upgrade_menu.draw(surface, self.player1, self.player2)
                else:
                    self.upgrade_menu.draw(surface, self.player1, self.player1)
                
                if custom_cursor:
                    mouse_pos = get_virtual_mouse_pos()
                    surface.blit(custom_cursor, (mouse_pos[0] - 16, mouse_pos[1] - 16))
        elif self.state == "keybindings":
            self.draw_controls_menu(surface)
        elif self.state == "language":
            self.draw_language_menu(surface)
        elif self.state == "credits":
            self.draw_credits(surface)
        elif self.state == "gameover":
            self.draw_game_over(surface)
        elif self.state == "leaderboard":
            self.draw_leaderboard(surface)
        
        if self.state in ["menu", "language", "credits", "leaderboard"]:
            if custom_cursor:
                mouse_pos = get_virtual_mouse_pos()
                surface.blit(custom_cursor, (mouse_pos[0] - 16, mouse_pos[1] - 16))
        
    def handle_events(self, event):
        self.ensure_runtime_state()
        if event.type == pygame.QUIT:
            return False
            
        if self.state == "keybindings":
            self.handle_controls_menu(event)
            return True
        elif self.state == "hero_selection":
            self.handle_hero_selection_events(event)
            return True
        elif self.state == "menu":
            self.handle_menu_events(event)
            return True
            
        if event.type == pygame.KEYDOWN:
            if event.key == K_F11:
                toggle_fullscreen()
            elif self.state == "arena":
                if event.key == K_F3:
                    self.show_path_debug = not getattr(self, "show_path_debug", SHOW_PATH_DEBUG)
                    msg = "Bat" if self.show_path_debug else "Tat"
                    self.show_toast(f"F3 Debug: {msg}")
                elif event.key == K_r:
                    self.randomize_algorithm_arena()
                elif event.key == K_y:
                    self.toggle_arena_replay()
                elif event.key == K_m:
                    self.cycle_arena_slow_motion()
                elif event.key == K_t:
                    self.toggle_arena_target_mode()
                elif event.key == K_c:
                    self.arena_locked_camera = not self.arena_locked_camera
                    mode = "Khoa" if self.arena_locked_camera else "Tu do"
                    self.show_toast(f"Camera: {mode}")
                elif event.key == K_ESCAPE:
                    self.state = "menu"
                    self.play_menu_music()
                return True
            elif self.state in ["singleplayer", "coop"] and self.algorithm_selector_open:
                if self.handle_algorithm_selector_input(event):
                    return True
            elif event.key == K_F3 and self.state in ["singleplayer", "coop"]:
                self.show_path_debug = not getattr(self, "show_path_debug", SHOW_PATH_DEBUG)
            elif event.key == K_F4 and self.state in ["singleplayer", "coop"]:
                self.algorithm_comparison_mode = not getattr(self, "algorithm_comparison_mode", False)
                self.apply_algorithm_mode()
                mode_text = "BẬT" if self.algorithm_comparison_mode else "TẮT"
                self.show_toast(f"Chế độ so sánh F4: {mode_text}")
            elif event.key == K_TAB and self.state in ["singleplayer", "coop"] and not self.upgrade_menu.is_open:
                self.toggle_algorithm_selector()
            elif event.key == K_ESCAPE and self.state in ["singleplayer", "coop"]:
                if self.algorithm_selector_open:
                    self.algorithm_selector_open = False
                    return True
                self.upgrade_menu.toggle()
                if self.upgrade_menu.is_open:
                    if self.state == "singleplayer":
                        self.upgrade_menu.set_current_player(self.player1)
                    else:
                        self.upgrade_menu.set_current_player(self.player1)
                    self.pause_start_time = self.current_time
                else:
                    if self.pause_start_time > 0:
                        self.total_pause_time += self.current_time - self.pause_start_time
                        self.pause_start_time = 0
            elif event.key == K_p and self.state in ["singleplayer", "coop"]:
                if self.algorithm_selector_open:
                    return True
                self.upgrade_menu.toggle()
                if self.upgrade_menu.is_open:
                    if self.state == "singleplayer":
                        self.upgrade_menu.set_current_player(self.player1)
                    else:
                        self.upgrade_menu.set_current_player(self.player1)
                    self.pause_start_time = self.current_time
                else:
                    if self.pause_start_time > 0:
                        self.total_pause_time += self.current_time - self.pause_start_time
                        self.pause_start_time = 0
            elif self.state in ["singleplayer", "coop"] and not self.algorithm_selector_open:
                for upgrade_type, upgrade_data in UPGRADES.items():
                    if event.key == upgrade_data['key1'] or event.key == upgrade_data['key2']:
                        if event.key == upgrade_data['key1']:
                            if self.state == "singleplayer":
                                self.player1.apply_upgrade(upgrade_type)
                            elif self.state == "coop":
                                self.player1.apply_upgrade(upgrade_type)
                        elif event.key == upgrade_data['key2']:
                            if self.state == "coop":
                                self.player2.apply_upgrade(upgrade_type)
        elif event.type == pygame.MOUSEMOTION:
            if self.state == "arena":
                self.arena_new_button.check_hover(get_virtual_mouse_pos())
            if self.upgrade_menu.is_open and not self.algorithm_selector_open:
                if self.state == "coop":
                    self.upgrade_menu.handle_mouse_hover(get_virtual_mouse_pos(), self.player1, self.player2)
                else:
                    self.upgrade_menu.handle_mouse_hover(get_virtual_mouse_pos(), self.player1, self.player1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.state == "arena":
            if self.arena_new_button.is_clicked(get_virtual_mouse_pos(), True):
                self.randomize_algorithm_arena()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.upgrade_menu.is_open and not self.algorithm_selector_open:
            result = None
            if self.state == "coop":
                result = self.upgrade_menu.handle_mouse_click(get_virtual_mouse_pos(), self.player1, self.player2)
            else:
                result = self.upgrade_menu.handle_mouse_click(get_virtual_mouse_pos(), self.player1, self.player1)
            
            if result == "back_to_menu":
                self.state = "menu"
                self.upgrade_menu.toggle()
                self.play_menu_music()
            elif result == "continue":
                self.upgrade_menu.toggle()
                if self.pause_start_time > 0:
                    self.total_pause_time += self.current_time - self.pause_start_time
                    self.pause_start_time = 0
        elif self.state == "menu":
            self.handle_menu_events(event)
            
        return True

    def start_game(self, mode):
        global CAMERA_X, CAMERA_Y
        self.state = mode
        
        self.monsters = []
        self.last_spawn_time = 0
        self.last_slime2_spawn_time = 0
        self.last_slime3_spawn_time = 0
        
        self.collectables = []
        self.generate_tree_obstacles()
        
        hero_data_p1 = self.hero_selection.heroes[self.hero_selection.selected_hero_p1]
        hero_data_p2 = self.hero_selection.heroes[self.hero_selection.selected_hero_p2 or self.hero_selection.selected_hero_p1]
        
        self.player1 = Player(FIELD_X + FIELD_WIDTH // 2 - 50, FIELD_Y + FIELD_HEIGHT // 2, 
                            self.controls["player1"], "Player 1", hero_data_p1)
        self.player2 = Player(FIELD_X + FIELD_WIDTH // 2 + 50, FIELD_Y + FIELD_HEIGHT // 2,
                            self.controls["player2"], "Player 2", hero_data_p2)
        CAMERA_X = max(0, min(self.player1.x - SCREEN_WIDTH / 2, WORLD_WIDTH - SCREEN_WIDTH))
        CAMERA_Y = max(0, min(self.player1.y - SCREEN_HEIGHT / 2, WORLD_HEIGHT - SCREEN_HEIGHT))
        
        self.game_start_time = self.current_time
        self.game_time = 0
        self.total_pause_time = 0
        self.pause_start_time = 0
        self.algorithm_selector_open = False
    
    def draw_game_over(self, surface):
        if self.game_over_sound and not self.game_over_sound_played and pygame.mixer.get_busy() == False:
            self.game_over_sound.play(0)  
            self.game_over_sound_played = True
            
        if self.game_over_background:
            surface.blit(self.game_over_background, (0, 0))
        else:
            surface.fill(BLACK)
            
        hours = int(self.game_time // 3600)
        minutes = int((self.game_time % 3600) // 60)
        seconds = int(self.game_time % 60)
        time_text = f"Thời gian sống sót: {hours:02d}:{minutes:02d}:{seconds:02d}"
        time_surface = small_font.render(time_text, True, BLACK)
        time_rect = time_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(time_surface, time_rect)
        
        stats_window_width = 300
        stats_window_height = 400
        stats_window_y = 100
        
        player1_window = pygame.Surface((stats_window_width, stats_window_height))
        player1_window.fill((0, 0, 0, 128)) 
        player1_window.set_alpha(128)
        surface.blit(player1_window, (50, stats_window_y))
        
        player1_title = small_font.render("Player 1", True, WHITE)
        player1_title_rect = player1_title.get_rect(center=(50 + stats_window_width // 2, stats_window_y + 30))
        surface.blit(player1_title, player1_title_rect)
        
        stats_y = stats_window_y + 80
        stats_spacing = 40
        
        level_text = small_font.render(f"Level: {self.player1.level}", True, WHITE)
        surface.blit(level_text, (70, stats_y))
        
        gold_text = small_font.render(f"Gold: {self.player1.total_gold_received}", True, WHITE)
        surface.blit(gold_text, (70, stats_y + stats_spacing))
        
        xp_text = small_font.render(f"XP: {self.player1.total_xp_collected}", True, WHITE)
        surface.blit(xp_text, (70, stats_y + stats_spacing * 2))
        
        player2_window = pygame.Surface((stats_window_width, stats_window_height))
        player2_window.fill((0, 0, 0, 128)) 
        player2_window.set_alpha(128)
        surface.blit(player2_window, (SCREEN_WIDTH - 50 - stats_window_width, stats_window_y))
        
        player2_title = small_font.render("Player 2", True, WHITE)
        player2_title_rect = player2_title.get_rect(center=(SCREEN_WIDTH - 50 - stats_window_width // 2, stats_window_y + 30))
        surface.blit(player2_title, player2_title_rect)
        
        if hasattr(self, 'player2'): 
            level_text = small_font.render(f"Level: {self.player2.level}", True, WHITE)
            surface.blit(level_text, (SCREEN_WIDTH - 50 - stats_window_width + 20, stats_y))
            
            gold_text = small_font.render(f"Gold: {self.player2.total_gold_received}", True, WHITE)
            surface.blit(gold_text, (SCREEN_WIDTH - 50 - stats_window_width + 20, stats_y + stats_spacing))
            
            xp_text = small_font.render(f"XP: {self.player2.total_xp_collected}", True, WHITE)
            surface.blit(xp_text, (SCREEN_WIDTH - 50 - stats_window_width + 20, stats_y + stats_spacing * 2))
        
        menu_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 100, 300, 50, "Menu")
        
        mouse_pos = get_virtual_mouse_pos()
        menu_button.check_hover(mouse_pos)
        
        menu_button.draw(surface)
        
        if custom_cursor:
            surface.blit(custom_cursor, (mouse_pos[0] - 16, mouse_pos[1] - 16))
        
        if pygame.mouse.get_pressed()[0] and menu_button.is_clicked(mouse_pos, True):
            if self.menu_selection_sound:
                self.menu_selection_sound.play(0)
            
            if self.game_over_sound:
                self.game_over_sound.stop()
            self.state = "menu"
            self.play_menu_music()

    def handle_hero_selection_events(self, event):
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = get_virtual_mouse_pos()
            self.hero_selection.select_button.check_hover(mouse_pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = get_virtual_mouse_pos()
            if self.hero_selection.handle_click(mouse_pos):
                if self.menu_selection_sound:
                    self.menu_selection_sound.play()
            elif self.hero_selection.select_button.is_clicked(mouse_pos, True):
                if self.menu_selection_sound:
                    self.menu_selection_sound.play()
                self.start_game(self.next_state)

class DamageText:
    def __init__(self, x, y, amount, is_crit=False):
        self.x = x
        self.y = y
        self.amount = amount
        self.is_crit = is_crit
        self.lifetime = 1.0  
        self.age = 0
        self.offset_y = 0
        self.alpha = 255  
        self.font = pygame.font.Font(None, 36)  
        
    def update(self, dt):
        self.age += dt
        self.offset_y -= 50 * dt  
        self.alpha = int(255 * (1 - self.age / self.lifetime)) 
        
        return self.age < self.lifetime
        
    def draw(self, surface):
        if self.is_crit:
            text_color = (255, 0, 0, self.alpha)  
            outline_color = (0, 0, 0, self.alpha) 
        else:
            text_color = (255, 255, 255, self.alpha) 
            outline_color = (0, 0, 0, self.alpha)  
        
        text = self.font.render(str(self.amount), True, text_color)
        
        pos_x = self.x - text.get_width() // 2
        pos_y = self.y + self.offset_y - text.get_height() // 2
        pos_x, pos_y = world_to_screen(pos_x, pos_y)
        
        if outline_color:
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                outline = self.font.render(str(self.amount), True, outline_color)
                surface.blit(outline, (pos_x + dx, pos_y + dy))
        
        surface.blit(text, (pos_x, pos_y))

game = Game()
if not hasattr(game, "algorithm_selector_open"):
    game.algorithm_selector_open = False
if not hasattr(game, "algorithm_selector_index"):
    game.algorithm_selector_index = 0
if not hasattr(game, "selected_algorithms"):
    game.selected_algorithms = {
        "slime1": "direct",
        "slime2": "astar",
        "slime3": "hill_climbing",
    }
if not hasattr(game, "show_path_debug"):
    game.show_path_debug = SHOW_PATH_DEBUG
if not hasattr(game, "algorithm_comparison_mode"):
    game.algorithm_comparison_mode = False
if not hasattr(game, "toast_message"):
    game.toast_message = ""
if not hasattr(game, "toast_expire_time"):
    game.toast_expire_time = 0.0
if not hasattr(game, "arena_zone_algorithms"):
    game.arena_zone_algorithms = ARENA_ALGORITHMS[:]
if not hasattr(game, "arena_mode_same_target"):
    game.arena_mode_same_target = True
if not hasattr(game, "arena_time_scale_index"):
    game.arena_time_scale_index = 0
if not hasattr(game, "arena_time_scale"):
    game.arena_time_scale = ARENA_SLOW_MOTION_LEVELS[0]
if not hasattr(game, "arena_locked_camera"):
    game.arena_locked_camera = True

running = True
current_time = 0
while running:
    dt = clock.tick(FPS) / 1000.0
    current_time += dt
    game.current_time = current_time
    
    if game.state in ["singleplayer", "coop"]:
        if game.upgrade_menu.is_open or game.algorithm_selector_open:
            pass
        else:
            game.game_time = current_time - game.game_start_time - game.total_pause_time
    
    for event in pygame.event.get():
        if not game.handle_events(event):
            running = False
    
    if not game.upgrade_menu.is_open and not game.algorithm_selector_open:
        if game.state in ["singleplayer", "coop"]:
            game.spawn_monster(current_time)
    
    game_surface.fill(BLACK)
    game.draw(game_surface)
    present_frame()

pygame.quit()

