import pygame
import math
import random
import time
from move import HillClimbingPathfinder, slime4_hill_climbing_movement

class Slime4:
   
    def __init__(self, x, y, target, game_time):
        # Đường dẫn đến sprites (giả định đã tạo thư mục slime4)
        self.run_sprite_sheet = pygame.image.load('sprites/monster/slime3/Run/run_anim.png').convert_alpha()  
        self.attack_sprite_sheet = pygame.image.load('sprites/monster/slime3/Attack/attack_anim.png').convert_alpha()
        self.hurt_sprite_sheet = pygame.image.load('sprites/monster/slime3/Hurt/hurt_anim.png').convert_alpha()
        
        # Sound effect
        self.hit_sound = pygame.mixer.Sound('sounds/hit.mp3')
        self.hit_sound.set_volume(0.5)
        
        # Thuộc tính vị trí và mục tiêu
        self.x = x
        self.y = y
        self.target = target
        
        # Thuộc tính di chuyển và chiến đấu
        self.base_speed = 2
        self.speed = self.base_speed * 1.1  # Nhanh hơn slime3 một chút
        self.damage = 3  # Sát thương cao hơn
        
        # Hồi máu mỗi phút
        self.heal_rate = int(game_time / 30)  # Hồi máu nhanh hơn slime3
        
        # Lưu speed gốc để phục hồi sau khi hết hiệu ứng chậm
        self.original_speed = self.speed
        self.is_slowed = False
        self.slow_effect_end_time = 0
        
        # Tính máu dựa trên thời gian chơi
        minutes_played = game_time / 60
        self.health = 15 + int(minutes_played * 15)  # Nhiều máu hơn slime3
        self.max_health = self.health
        
        # Các thuộc tính cho va chạm và tấn công
        self.radius = 38  # Lớn hơn slime3
        self.max_overlap = 0.7
        self.attack_cooldown = 1.0
        self.attack_range = 150  # Tấn công từ xa hơn slime3
        self.last_attack_time = 0
        self.is_attacking = False
        self.attack_duration = 0.5
        self.attack_timer = 0
        self.damage_cooldown = 1.0
        self.last_damage_time = 0
        self.last_heal_time = 0
        
        # Kích thước và animation
        self.sprite_width = 64
        self.sprite_height = 64
        self.columns = 8
        self.rows = 4
        self.scale_factor = 3.0  # Lớn hơn slime3
        
        self.current_frame = 0
        self.animation_speed = 0.1
        self.animation_timer = 0
        self.direction = 0
        
        # Các khung hình animation
        self.run_frames = []
        self.attack_frames = []
        self.hurt_frames = []
        self.load_frames()
        
        # Damage text
        self.damage_texts = []
        
        # Trạng thái
        self.is_dying = False
        self.death_timer = 0
        self.death_duration = 0.3
        self.hurt_animation_speed = 0.1
        self.hurt_frame = 0
        self.hurt_row = 0
        self.hurt_animation_played = False
        self.is_dead = False
        self.attack_sound_played = False
        self.show_path_debug = False
        
        # Các thuộc tính cho Leo Đồi (Hill Climbing)
        self.hill_climbing = HillClimbingPathfinder(2000, 2000, 32)  # Thay thế kích thước thực của màn chơi
        self.path = []
        self.path_index = 0
        self.path_update_time = 0
        self.path_update_interval = 0.3  # Cập nhật đường đi mỗi 0.3 giây
        
        # Khả năng đặc biệt của slime4
        self.can_spawn_minions = True
        self.teleport_cooldown = 10.0
        self.last_teleport_time = 0
        self.projectiles = []
    
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
        
        # Hiển thị sát thương
        center_x = self.x + (self.sprite_width * self.scale_factor) / 2
        center_y = self.y + (self.sprite_height * self.scale_factor) / 2
        self.damage_texts.append(DamageText(center_x, center_y, amount, is_crit))
        
        self.hurt_animation_played = False
        self.hurt_frame = 0
        self.hurt_row = self.direction
        
        # Xử lý khi chết
        if self.health <= 0 and not self.is_dying:
            self.is_dying = True
            self.death_timer = 0
            self.is_dead = True
            
            # Chức năng đặc biệt: Tạo slime nhỏ khi chết
            if self.can_spawn_minions:
                return self.spawn_minions()
    
    def spawn_minions(self):
        minion_count = random.randint(2, 4)
        minions = []
        
        for i in range(minion_count):
            angle = 2 * math.pi * i / minion_count
            distance = 50
            spawn_x = self.x + math.cos(angle) * distance
            spawn_y = self.y + math.sin(angle) * distance
            
            minions.append((spawn_x, spawn_y))
            
        return minions
    
    def apply_slow_effect(self, slow_factor, duration):
        self.is_slowed = True
        self.speed = self.original_speed * slow_factor
        self.slow_effect_end_time = time.time() + duration
        self.animation_speed = self.animation_speed * 1.5
    
    def try_teleport(self, current_time, field_width, field_height):
        if current_time - self.last_teleport_time >= self.teleport_cooldown:
            # Tìm vị trí xung quanh người chơi trong khoảng cách nhất định
            teleport_distance = random.randint(100, 200)
            angle = random.uniform(0, 2 * math.pi)
            
            new_x = self.target.x + math.cos(angle) * teleport_distance
            new_y = self.target.y + math.sin(angle) * teleport_distance
            
            # Đảm bảo vị trí nằm trong khu vực chơi
            new_x = max(0, min(field_width, new_x))
            new_y = max(0, min(field_height, new_y))
            
            self.x = new_x
            self.y = new_y
            self.last_teleport_time = current_time
            
            # Trả về True nếu đã dịch chuyển thành công
            return True
        
        return False
    
    def update(self, dt, players, monsters, current_time, field_width, field_height):
        return slime4_hill_climbing_movement(self, players, monsters, current_time, field_width, field_height)
    
    def draw_health_bar(self, surface):
        bar_width = (self.sprite_width * self.scale_factor) * 0.75
        bar_height = 6
        bar_x = self.x + (self.sprite_width * self.scale_factor - bar_width) // 2
        bar_y = self.y - 4
        
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
                    pygame.draw.rect(surface, (0, 0, 255), (block_x, bar_y, green_width, bar_height))  # Thanh máu màu xanh dương
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
                pygame.draw.rect(surface, (0, 0, 255), (block_x, bar_y, block_width_with_spacing, bar_height))  # Thanh máu màu xanh dương
            
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
            
        # Hiệu ứng chậm - overlay màu xanh
        if self.is_slowed:
            slowed_sprite = current_sprite.copy()
            blue_overlay = pygame.Surface(slowed_sprite.get_size(), pygame.SRCALPHA)
            blue_overlay.fill((0, 0, 255, 40))  # Light blue transparent overlay
            slowed_sprite.blit(blue_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            current_sprite = slowed_sprite
            
        # Thêm hiệu ứng đặc biệt cho slime4 - ánh sáng màu tím
        special_sprite = current_sprite.copy()
        purple_outline = pygame.Surface(special_sprite.get_size(), pygame.SRCALPHA)
        purple_outline.fill((128, 0, 128, 20))  # Ánh sáng tím
        special_sprite.blit(purple_outline, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        current_sprite = special_sprite
        
        surface.blit(current_sprite, (self.x, self.y))
            
        for text in self.damage_texts:
            text.draw(surface)
        
        # Vẽ đường đi Leo Đồi (cho debug)
        if self.show_path_debug:
            self.draw_path(surface)
    
    def draw_path(self, surface):
        if self.path and self.path_index < len(self.path):
            # Vẽ vật cản của Hill Climbing
            if hasattr(self, "hill_climbing") and getattr(self.hill_climbing, "obstacles", None):
                overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
                for obstacle_x, obstacle_y, obstacle_width, obstacle_height in self.hill_climbing.obstacles:
                    pygame.draw.rect(
                        overlay,
                        (120, 120, 120, 70),
                        (obstacle_x, obstacle_y, obstacle_width, obstacle_height),
                    )
                surface.blit(overlay, (0, 0))

            # Vẽ đường đi
            for i in range(self.path_index, len(self.path) - 1):
                start_pos = self.path[i]
                end_pos = self.path[i + 1]
                pygame.draw.line(surface, (128, 0, 128), start_pos, end_pos, 2)
            
            # Vẽ điểm đang hướng đến
            target_pos = self.path[self.path_index]
            pygame.draw.circle(surface, (255, 0, 255), target_pos, 5)
            
            # Vẽ text "Hill Climbing" ở trên đầu slime4
            font = pygame.font.Font(None, 20)
            text = font.render("Hill Climbing", True, (255, 0, 255))
            text_pos = (self.x + (self.sprite_width * self.scale_factor) // 2 - text.get_width() // 2, 
                       self.y - 30)
            surface.blit(text, text_pos)


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
        
        if outline_color:
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                outline = self.font.render(str(self.amount), True, outline_color)
                surface.blit(outline, (pos_x + dx, pos_y + dy))
        
        surface.blit(text, (pos_x, pos_y))
