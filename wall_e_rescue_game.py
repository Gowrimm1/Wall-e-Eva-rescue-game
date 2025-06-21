import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
WORLD_WIDTH = 2000  # Shorter world for quicker gameplay

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
DARK_BLUE = (0, 0, 139)
BROWN = (139, 69, 19)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)
LIME = (50, 205, 50)

class GameState:
    INTRO = 0
    PLAYING = 1
    BOSS_FIGHT = 2
    GAME_OVER = 3
    VICTORY = 4

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.on_ground = False
        self.vel_y = 0
        self.jump_power = -15
        self.gravity = 0.8
        self.world_x = x  # Position in the world
        
    def update(self, obstacles, camera_x):
        keys = pygame.key.get_pressed()
        
        # Horizontal movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.world_x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.world_x += self.speed
            
        # Jumping
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
            
        # Apply gravity
        self.vel_y += self.gravity
        self.y += self.vel_y
        
        # Ground collision
        if self.y >= SCREEN_HEIGHT - 100 - self.height:
            self.y = SCREEN_HEIGHT - 100 - self.height
            self.vel_y = 0
            self.on_ground = True
            
        # World boundaries
        self.world_x = max(0, min(self.world_x, WORLD_WIDTH - self.width))
        
        # Screen position relative to camera
        self.x = self.world_x - camera_x
        
        # Check obstacle collisions
        player_rect = pygame.Rect(self.world_x, self.y, self.width, self.height)
        for obstacle in obstacles:
            if player_rect.colliderect(obstacle.get_world_rect()):
                if obstacle.type == "fire":
                    self.health -= 0.3  # Reduced damage
                elif obstacle.type == "water":
                    self.health -= 0.2  # Reduced damage
                elif obstacle.type == "trap":
                    self.health -= 0.5  # Reduced damage
                    
        # Clamp health
        self.health = max(0, min(self.health, self.max_health))
        
    def draw(self, screen):
        # Only draw if on screen
        if -50 <= self.x <= SCREEN_WIDTH + 50:
            # Draw Wall-E as a simple robot shape
            pygame.draw.rect(screen, GRAY, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, YELLOW, (self.x + 5, self.y + 5, 10, 10))  # Eyes
            pygame.draw.rect(screen, YELLOW, (self.x + 25, self.y + 5, 10, 10))
            pygame.draw.rect(screen, BLACK, (self.x + 10, self.y + 20, 20, 5))  # Mouth
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_world_rect(self):
        return pygame.Rect(self.world_x, self.y, self.width, self.height)

class Obstacle:
    def __init__(self, x, y, width, height, obstacle_type):
        self.world_x = x  # Position in world coordinates
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.animation_timer = 0
        self.x = 0  # Screen position (calculated during draw)
        
    def update(self):
        self.animation_timer += 1
        
    def draw(self, screen, camera_x):
        # Calculate screen position
        self.x = self.world_x - camera_x
        
        # Only draw if on screen
        if -100 <= self.x <= SCREEN_WIDTH + 100:
            if self.type == "fire":
                # Simple fire effect
                pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))
                pygame.draw.rect(screen, ORANGE, (self.x + 5, self.y + 5, self.width - 10, self.height - 10))
            elif self.type == "water":
                pygame.draw.rect(screen, BLUE, (self.x, self.y, self.width, self.height))
                pygame.draw.rect(screen, CYAN, (self.x, self.y, self.width, 5))
            elif self.type == "trap":
                pygame.draw.rect(screen, PURPLE, (self.x, self.y, self.width, self.height))
            
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_world_rect(self):
        return pygame.Rect(self.world_x, self.y, self.width, self.height)

class Alien:
    def __init__(self, x, y):
        self.world_x = x
        self.y = y
        self.width = 60
        self.height = 80
        self.health = 250  # Much higher health for challenging fight
        self.max_health = 250
        self.speed = 3  # Faster movement
        self.attack_timer = 0
        self.attack_cooldown = 45  # Faster attacks (0.75 seconds)
        self.projectiles = []
        self.x = 0  # Screen position
        self.phase = 1  # Boss phases for escalating difficulty
        self.special_attack_timer = 0
        self.teleport_timer = 0
        self.shield_timer = 0
        self.shield_active = False
        self.rage_mode = False
        
    def update(self, player, camera_x):
        self.x = self.world_x - camera_x
        
        # Determine boss phase based on health
        if self.health <= self.max_health * 0.3:  # 30% health
            self.phase = 3
            self.rage_mode = True
        elif self.health <= self.max_health * 0.6:  # 60% health
            self.phase = 2
        else:
            self.phase = 1
        
        # Enhanced movement patterns based on phase
        if self.phase == 1:
            # Phase 1: Floating movement
            self.y += math.sin(pygame.time.get_ticks() * 0.005) * 2
        elif self.phase == 2:
            # Phase 2: More aggressive movement + occasional teleport
            self.y += math.sin(pygame.time.get_ticks() * 0.008) * 3
            self.teleport_timer += 1
            if self.teleport_timer >= 300:  # Teleport every 5 seconds
                self.teleport_timer = 0
                # Teleport to random position near player
                self.world_x = player.world_x + random.randint(-200, 200)
                self.world_x = max(WORLD_WIDTH - 400, min(self.world_x, WORLD_WIDTH - 50))
        else:
            # Phase 3: Rage mode - erratic movement
            self.y += math.sin(pygame.time.get_ticks() * 0.012) * 4
            self.world_x += math.sin(pygame.time.get_ticks() * 0.003) * 2
            self.world_x = max(WORLD_WIDTH - 400, min(self.world_x, WORLD_WIDTH - 50))
        
        # Shield mechanic (Phase 2+)
        if self.phase >= 2:
            self.shield_timer += 1
            if self.shield_timer >= 600:  # Shield every 10 seconds
                self.shield_active = True
                self.shield_timer = 0
            elif self.shield_timer >= 180:  # Shield lasts 3 seconds
                self.shield_active = False
        
        # Attack patterns based on phase
        self.attack_timer += 1
        attack_frequency = self.attack_cooldown // self.phase  # Faster attacks in higher phases
        
        if self.attack_timer >= attack_frequency:
            self.attack_timer = 0
            if self.phase == 1:
                self.create_single_projectile(player)
            elif self.phase == 2:
                self.create_triple_shot(player)
            else:  # Phase 3
                self.create_spread_shot(player)
        
        # Special attacks
        self.special_attack_timer += 1
        if self.phase >= 2 and self.special_attack_timer >= 240:  # Every 4 seconds
            self.special_attack_timer = 0
            if self.phase == 2:
                self.create_homing_missile(player)
            else:  # Phase 3
                self.create_laser_beam(player)
                
        # Update projectiles
        for proj in self.projectiles[:]:
            if proj['type'] == 'homing':
                # Homing missile behavior
                dx = player.world_x - proj['x']
                dy = player.y - proj['y']
                distance = math.sqrt(dx*dx + dy*dy)
                if distance > 0:
                    homing_strength = 0.3
                    proj['dx'] += (dx / distance) * homing_strength
                    proj['dy'] += (dy / distance) * homing_strength
                    # Limit speed
                    speed = math.sqrt(proj['dx']**2 + proj['dy']**2)
                    if speed > 6:
                        proj['dx'] = (proj['dx'] / speed) * 6
                        proj['dy'] = (proj['dy'] / speed) * 6
            elif proj['type'] == 'laser':
                # Laser beam - faster and straight
                pass
            
            proj['x'] += proj['dx']
            proj['y'] += proj['dy']
            
            # Remove if off screen or expired
            if (proj['x'] < camera_x - 100 or proj['x'] > camera_x + SCREEN_WIDTH + 100 or 
                proj['y'] < 0 or proj['y'] > SCREEN_HEIGHT):
                self.projectiles.remove(proj)
            elif 'lifetime' in proj:
                proj['lifetime'] -= 1
                if proj['lifetime'] <= 0:
                    self.projectiles.remove(proj)
                
        # Check projectile collision with player
        player_rect = player.get_world_rect()
        for proj in self.projectiles[:]:
            proj_size = 12 if proj['type'] == 'homing' else 8
            proj_rect = pygame.Rect(proj['x'] - proj_size, proj['y'] - proj_size, proj_size*2, proj_size*2)
            if player_rect.colliderect(proj_rect):
                damage = 15 if proj['type'] == 'homing' else 12 if proj['type'] == 'laser' else 8
                player.health -= damage
                self.projectiles.remove(proj)
    
    def create_single_projectile(self, player):
        dx = player.world_x - self.world_x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            proj_speed = 5
            proj_dx = (dx / distance) * proj_speed
            proj_dy = (dy / distance) * proj_speed
            
            projectile = {
                'x': self.world_x + self.width // 2,
                'y': self.y + self.height // 2,
                'dx': proj_dx,
                'dy': proj_dy,
                'type': 'normal'
            }
            self.projectiles.append(projectile)
    
    def create_triple_shot(self, player):
        # Create three projectiles in a spread pattern
        dx = player.world_x - self.world_x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            base_angle = math.atan2(dy, dx)
            proj_speed = 5
            
            for i, angle_offset in enumerate([-0.3, 0, 0.3]):  # Spread angles
                angle = base_angle + angle_offset
                proj_dx = math.cos(angle) * proj_speed
                proj_dy = math.sin(angle) * proj_speed
                
                projectile = {
                    'x': self.world_x + self.width // 2,
                    'y': self.y + self.height // 2,
                    'dx': proj_dx,
                    'dy': proj_dy,
                    'type': 'normal'
                }
                self.projectiles.append(projectile)
    
    def create_spread_shot(self, player):
        # Create five projectiles in a wide spread (rage mode)
        center_x = self.world_x + self.width // 2
        center_y = self.y + self.height // 2
        proj_speed = 6
        
        for i in range(5):
            angle = (i - 2) * 0.4  # Spread from -0.8 to 0.8 radians
            proj_dx = math.cos(angle) * proj_speed
            proj_dy = math.sin(angle) * proj_speed
            
            projectile = {
                'x': center_x,
                'y': center_y,
                'dx': proj_dx,
                'dy': proj_dy,
                'type': 'normal'
            }
            self.projectiles.append(projectile)
    
    def create_homing_missile(self, player):
        # Special homing projectile
        projectile = {
            'x': self.world_x + self.width // 2,
            'y': self.y + self.height // 2,
            'dx': 2,
            'dy': 2,
            'type': 'homing'
        }
        self.projectiles.append(projectile)
    
    def create_laser_beam(self, player):
        # Fast laser beam attack
        dx = player.world_x - self.world_x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            proj_speed = 8
            proj_dx = (dx / distance) * proj_speed
            proj_dy = (dy / distance) * proj_speed
            
            projectile = {
                'x': self.world_x + self.width // 2,
                'y': self.y + self.height // 2,
                'dx': proj_dx,
                'dy': proj_dy,
                'type': 'laser',
                'lifetime': 120  # Lasts 2 seconds
            }
            self.projectiles.append(projectile)
                
    def draw(self, screen, camera_x):
        # Only draw if on screen
        if -100 <= self.x <= SCREEN_WIDTH + 100:
            # Draw shield effect if active
            if self.shield_active:
                shield_color = (0, 255, 255, 100)  # Cyan with transparency
                shield_surface = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
                pygame.draw.ellipse(shield_surface, shield_color, (0, 0, self.width + 20, self.height + 20))
                screen.blit(shield_surface, (self.x - 10, self.y - 10))
            
            # Change alien color based on phase
            if self.phase == 1:
                alien_color = GREEN
            elif self.phase == 2:
                alien_color = (255, 165, 0)  # Orange
            else:  # Phase 3 - rage mode
                alien_color = (255, 0, 0) if pygame.time.get_ticks() % 200 < 100 else (255, 100, 100)  # Flashing red
            
            # Draw alien with phase-appropriate color
            pygame.draw.ellipse(screen, alien_color, (self.x, self.y, self.width, self.height))
            
            # Eyes - more menacing in higher phases
            eye_color = RED if self.phase < 3 else (255, 255, 0)  # Yellow eyes in rage mode
            pygame.draw.circle(screen, eye_color, (self.x + 15, self.y + 20), 8)
            pygame.draw.circle(screen, eye_color, (self.x + 45, self.y + 20), 8)
            
            # Add spikes/details for higher phases
            if self.phase >= 2:
                # Draw spikes
                for i in range(3):
                    spike_x = self.x + 10 + i * 20
                    spike_y = self.y - 5
                    pygame.draw.polygon(screen, BLACK, [(spike_x, spike_y), (spike_x + 5, spike_y - 10), (spike_x + 10, spike_y)])
        
        # Draw projectiles with different colors based on type
        for proj in self.projectiles:
            proj_screen_x = proj['x'] - camera_x
            if -20 <= proj_screen_x <= SCREEN_WIDTH + 20:
                if proj['type'] == 'homing':
                    # Homing missiles are larger and red
                    pygame.draw.circle(screen, RED, (int(proj_screen_x), int(proj['y'])), 12)
                    pygame.draw.circle(screen, YELLOW, (int(proj_screen_x), int(proj['y'])), 6)
                elif proj['type'] == 'laser':
                    # Laser beams are bright and elongated
                    pygame.draw.circle(screen, WHITE, (int(proj_screen_x), int(proj['y'])), 6)
                    pygame.draw.circle(screen, CYAN, (int(proj_screen_x), int(proj['y'])), 3)
                else:
                    # Normal projectiles
                    pygame.draw.circle(screen, PURPLE, (int(proj_screen_x), int(proj['y'])), 8)
            
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_world_rect(self):
        return pygame.Rect(self.world_x, self.y, self.width, self.height)
    
    def take_damage(self, damage):
        # Shield blocks damage
        if not self.shield_active:
            self.health -= damage
        else:
            # Visual feedback that shield blocked the attack
            pass

class EVE:
    def __init__(self, x, y):
        self.world_x = x
        self.y = y
        self.width = 35
        self.height = 50
        self.rescued = False
        self.x = 0  # Screen position
        self.float_timer = 0
        
    def update(self):
        self.float_timer += 1
        # Floating animation
        self.y += math.sin(self.float_timer * 0.05) * 1
        
    def draw(self, screen, camera_x):
        self.x = self.world_x - camera_x
        # Only draw if on screen
        if -50 <= self.x <= SCREEN_WIDTH + 50:
            # Draw EVE as a sleek white robot with glow effect
            # Glow effect
            for i in range(3):
                glow_alpha = 50 - i * 15
                glow_surface = pygame.Surface((self.width + i*4, self.height + i*4), pygame.SRCALPHA)
                pygame.draw.ellipse(glow_surface, (*WHITE, glow_alpha), (0, 0, self.width + i*4, self.height + i*4))
                screen.blit(glow_surface, (self.x - i*2, self.y - i*2))
            
            pygame.draw.ellipse(screen, WHITE, (self.x, self.y, self.width, self.height))
            pygame.draw.circle(screen, BLUE, (self.x + 10, self.y + 15), 4)  # Eyes
            pygame.draw.circle(screen, BLUE, (self.x + 25, self.y + 15), 4)
            
            # Heart symbol to show she needs rescue
            heart_x, heart_y = self.x + self.width//2 - 5, self.y - 20
            pygame.draw.circle(screen, RED, (heart_x, heart_y), 3)
            pygame.draw.circle(screen, RED, (heart_x + 6, heart_y), 3)
            pygame.draw.polygon(screen, RED, [(heart_x - 3, heart_y + 2), (heart_x + 9, heart_y + 2), (heart_x + 3, heart_y + 8)])
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_world_rect(self):
        return pygame.Rect(self.world_x, self.y, self.width, self.height)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wall-E and Eva - Extended Rescue Mission")
        self.clock = pygame.time.Clock()
        self.state = GameState.INTRO
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 48)
        
        # Load space background
        try:
            self.space_bg = pygame.image.load("space_background.png")
        except:
            # Create a simple space background if file doesn't exist
            self.space_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.space_bg.fill((10, 10, 30))
            # Add some stars
            for _ in range(100):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                pygame.draw.circle(self.space_bg, WHITE, (x, y), 1)
        
        # Game objects
        self.player = Player(50, SCREEN_HEIGHT - 150)
        self.eve = EVE(WORLD_WIDTH - 150, SCREEN_HEIGHT - 200)
        self.alien = Alien(WORLD_WIDTH - 200, SCREEN_HEIGHT - 230)
        
        # Camera system
        self.camera_x = 0
        
        # Create obstacles
        self.obstacles = []
        self.create_obstacles()
        
        # Story variables
        self.intro_timer = 0
        self.story_phase = 0
        self.skip_intro = False
        
    def create_obstacles(self):
        # Simplified obstacle course with much wider spacing
        obstacle_types = ["fire", "water", "trap"]  # Only basic obstacles
        
        # Section 1: Learning section (0-1000) - Very wide spacing
        for i in range(5):
            x = 300 + i * 200  # Very wide spacing (200 units apart)
            obstacle_type = random.choice(["fire", "water"])
            width = 30  # Fixed smaller size
            height = 20
            y = SCREEN_HEIGHT - 100 - height
            self.obstacles.append(Obstacle(x, y, width, height, obstacle_type))
        
        # Section 2: Main course (1000-2000) - Wide spacing
        for i in range(6):
            x = 1200 + i * 150  # Wide spacing (150 units apart)
            obstacle_type = random.choice(["fire", "water", "trap"])
            width = 35
            height = 25
            y = SCREEN_HEIGHT - 100 - height
            self.obstacles.append(Obstacle(x, y, width, height, obstacle_type))
        
        # Section 3: Final approach (2000-2600) - Moderate spacing
        for i in range(4):
            x = 2100 + i * 120  # Good spacing (120 units apart)
            obstacle_type = random.choice(obstacle_types)
            width = 40
            height = 30
            y = SCREEN_HEIGHT - 100 - height
            self.obstacles.append(Obstacle(x, y, width, height, obstacle_type))
    
    def update_camera(self):
        # Camera follows player but with some offset
        target_x = self.player.world_x - SCREEN_WIDTH // 3
        self.camera_x += (target_x - self.camera_x) * 0.1  # Smooth camera movement
        self.camera_x = max(0, min(self.camera_x, WORLD_WIDTH - SCREEN_WIDTH))
        
    def draw_intro(self):
        # Use space background
        self.screen.blit(self.space_bg, (0, 0))
        
        # Add twinkling effect to stars
        for _ in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            if random.random() < 0.1:  # 10% chance to twinkle
                pygame.draw.circle(self.screen, WHITE, (x, y), 2)
        
        story_lines = [
            "In a distant galaxy, Wall-E and Eva lived peacefully...",
            "One day, a mysterious alien ship appeared in the sky.",
            "The alien abducted Eva while Wall-E was away collecting scrap!",
            "Now Wall-E must brave dangerous obstacles to rescue her.",
            "The journey is long and filled with deadly traps:",
            "Fire pits, acid pools, laser beams, and spike traps await!",
            "Help Wall-E overcome all obstacles to save Eva!",
            "Press SPACE to begin the rescue mission!",
            "Press S to SKIP intro"
        ]
        
        phase = min(self.story_phase, len(story_lines) - 1)
        
        # Title
        title_text = self.large_font.render("WALL-E'S RESCUE MISSION", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        for i in range(phase + 1):
            if i < len(story_lines):
                color = WHITE if i < len(story_lines) - 2 else YELLOW
                text = self.small_font.render(story_lines[i], True, color)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 200 + i * 35))
                self.screen.blit(text, text_rect)
        
        # Show Wall-E and Eva in intro
        if self.story_phase >= 2:
            # Wall-E
            pygame.draw.rect(self.screen, GRAY, (200, 500, 40, 40))
            pygame.draw.rect(self.screen, YELLOW, (205, 505, 10, 10))
            pygame.draw.rect(self.screen, YELLOW, (225, 505, 10, 10))
            
            # Eva (being abducted)
            eva_y = 400 - min(self.story_phase * 10, 100)
            pygame.draw.ellipse(self.screen, WHITE, (700, eva_y, 35, 50))
            pygame.draw.circle(self.screen, BLUE, (710, eva_y + 15), 3)
            pygame.draw.circle(self.screen, BLUE, (725, eva_y + 15), 3)
            
            # Alien ship
            if self.story_phase >= 3:
                ship_y = eva_y - 50
                pygame.draw.ellipse(self.screen, GREEN, (680, ship_y, 80, 30))
                pygame.draw.circle(self.screen, RED, (720, ship_y + 15), 5)
                
        # Auto-advance story
        if not self.skip_intro:
            self.intro_timer += 1
            if self.intro_timer >= 90:  # 1.5 seconds at 60 FPS
                self.intro_timer = 0
                if self.story_phase < len(story_lines) - 1:
                    self.story_phase += 1
                    
    def draw_hud(self):
        # Health bar
        health_width = 200
        health_height = 20
        health_x = 10
        health_y = 10
        
        # Background
        pygame.draw.rect(self.screen, RED, (health_x, health_y, health_width, health_height))
        
        # Health
        current_health_width = (self.player.health / self.player.max_health) * health_width
        pygame.draw.rect(self.screen, GREEN, (health_x, health_y, current_health_width, health_height))
        
        # Health text
        health_text = self.small_font.render(f"Health: {int(self.player.health)}/{self.player.max_health}", True, WHITE)
        self.screen.blit(health_text, (health_x, health_y + 25))
        
        # Progress bar
        progress = (self.player.world_x / WORLD_WIDTH) * 100
        progress_text = self.small_font.render(f"Progress: {progress:.1f}%", True, WHITE)
        self.screen.blit(progress_text, (health_x, health_y + 50))
        
        # Distance to Eva
        distance_to_eva = max(0, self.eve.world_x - self.player.world_x)
        if distance_to_eva > 0:
            distance_text = self.small_font.render(f"Distance to Eva: {int(distance_to_eva)}m", True, YELLOW)
            self.screen.blit(distance_text, (health_x, health_y + 75))
        else:
            rescue_text = self.small_font.render("Eva is near! Defeat the alien!", True, RED)
            self.screen.blit(rescue_text, (health_x, health_y + 75))
        
        # Instructions
        if self.state == GameState.PLAYING:
            instructions = [
                "Arrow Keys/WASD: Move",
                "Space/Up: Jump",
                "Avoid obstacles and reach Eva!"
            ]
            for i, instruction in enumerate(instructions):
                text = self.small_font.render(instruction, True, WHITE)
                self.screen.blit(text, (SCREEN_WIDTH - 250, 10 + i * 25))
                
    def draw_background(self):
        # Parallax scrolling background
        bg_x = -(self.camera_x * 0.5) % SCREEN_WIDTH
        self.screen.blit(self.space_bg, (bg_x, 0))
        if bg_x > 0:
            self.screen.blit(self.space_bg, (bg_x - SCREEN_WIDTH, 0))
                
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.state == GameState.INTRO:
                        if self.story_phase >= 7:  # All story shown
                            self.state = GameState.PLAYING
                    elif event.key == pygame.K_s and self.state == GameState.INTRO:
                        self.state = GameState.PLAYING  # Skip intro
                    elif event.key == pygame.K_r and (self.state == GameState.GAME_OVER or self.state == GameState.VICTORY):
                        # Restart game
                        self.__init__()
                        
            if self.state == GameState.INTRO:
                self.draw_intro()
                
            elif self.state == GameState.PLAYING:
                # Update
                self.player.update(self.obstacles, self.camera_x)
                self.eve.update()
                for obstacle in self.obstacles:
                    obstacle.update()
                
                self.update_camera()
                    
                # Check if player reached EVE (boss fight)
                if self.player.world_x >= WORLD_WIDTH - 200:
                    self.state = GameState.BOSS_FIGHT
                    
                # Check game over
                if self.player.health <= 0:
                    self.state = GameState.GAME_OVER
                    
                # Draw
                self.draw_background()
                
                # Draw ground
                ground_start = -self.camera_x % 100
                for x in range(int(ground_start), SCREEN_WIDTH + 100, 100):
                    pygame.draw.rect(self.screen, BROWN, (x, SCREEN_HEIGHT - 100, 100, 100))
                
                # Draw obstacles
                for obstacle in self.obstacles:
                    obstacle.draw(self.screen, self.camera_x)
                    
                # Draw characters
                self.player.draw(self.screen)
                
                # Only show Eva when close
                if self.player.world_x >= WORLD_WIDTH - 300:
                    self.eve.draw(self.screen, self.camera_x)
                
                self.draw_hud()
                
            elif self.state == GameState.BOSS_FIGHT:
                # Update
                self.player.update([], self.camera_x)  # No obstacles during boss fight
                self.alien.update(self.player, self.camera_x)
                self.eve.update()
                
                self.update_camera()
                
                # Check if player can attack alien (simple collision)
                if self.player.get_world_rect().colliderect(self.alien.get_world_rect()):
                    self.alien.take_damage(3)  # Increased damage to compensate for higher health
                    
                # Check victory
                if self.alien.health <= 0:
                    self.state = GameState.VICTORY
                    
                # Check game over
                if self.player.health <= 0:
                    self.state = GameState.GAME_OVER
                    
                # Draw
                self.draw_background()
                
                # Draw ground
                ground_start = -self.camera_x % 100
                for x in range(int(ground_start), SCREEN_WIDTH + 100, 100):
                    pygame.draw.rect(self.screen, BROWN, (x, SCREEN_HEIGHT - 100, 100, 100))
                
                # Draw characters
                self.player.draw(self.screen)
                self.eve.draw(self.screen, self.camera_x)
                self.alien.draw(self.screen, self.camera_x)
                
                # Boss health bar
                boss_health_width = 400
                boss_health_height = 25
                boss_health_x = SCREEN_WIDTH // 2 - boss_health_width // 2
                boss_health_y = 50
                
                # Health bar background
                pygame.draw.rect(self.screen, RED, (boss_health_x, boss_health_y, boss_health_width, boss_health_height))
                current_boss_health = (self.alien.health / self.alien.max_health) * boss_health_width
                
                # Health bar color changes based on phase
                if self.alien.phase == 1:
                    health_color = GREEN
                elif self.alien.phase == 2:
                    health_color = ORANGE
                else:
                    health_color = RED
                
                pygame.draw.rect(self.screen, health_color, (boss_health_x, boss_health_y, current_boss_health, boss_health_height))
                
                # Boss phase indicator
                phase_text = f"ALIEN BOSS - PHASE {self.alien.phase}"
                if self.alien.rage_mode:
                    phase_text += " (RAGE MODE!)"
                boss_text = self.font.render(phase_text, True, WHITE)
                boss_text_rect = boss_text.get_rect(center=(SCREEN_WIDTH // 2, boss_health_y - 25))
                self.screen.blit(boss_text, boss_text_rect)
                
                # Shield indicator
                if self.alien.shield_active:
                    shield_text = self.small_font.render("SHIELD ACTIVE!", True, CYAN)
                    shield_rect = shield_text.get_rect(center=(SCREEN_WIDTH // 2, boss_health_y + 35))
                    self.screen.blit(shield_text, shield_rect)
                
                # Enhanced instructions based on phase
                if self.alien.phase == 1:
                    fight_instructions = [
                        "Touch the alien to attack!",
                        "Avoid purple projectiles!"
                    ]
                elif self.alien.phase == 2:
                    fight_instructions = [
                        "Phase 2: Triple shots & homing missiles!",
                        "Watch out for teleportation and shields!"
                    ]
                else:
                    fight_instructions = [
                        "RAGE MODE: Spread shots & laser beams!",
                        "Maximum difficulty - stay mobile!"
                    ]
                
                for i, instruction in enumerate(fight_instructions):
                    color = WHITE if self.alien.phase == 1 else YELLOW if self.alien.phase == 2 else RED
                    text = self.small_font.render(instruction, True, color)
                    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, boss_health_y + 60 + i * 25))
                    self.screen.blit(text, text_rect)
                
                self.draw_hud()
                
            elif self.state == GameState.GAME_OVER:
                self.screen.fill(BLACK)
                game_over_text = self.large_font.render("MISSION FAILED", True, RED)
                game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
                self.screen.blit(game_over_text, game_over_rect)
                
                reason_text = self.font.render("Wall-E couldn't save Eva...", True, WHITE)
                reason_rect = reason_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(reason_text, reason_rect)
                
                restart_text = self.small_font.render("Press R to restart the rescue mission", True, YELLOW)
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                self.screen.blit(restart_text, restart_rect)
                
            elif self.state == GameState.VICTORY:
                self.screen.fill(BLACK)
                
                # Victory animation
                victory_text = self.large_font.render("MISSION ACCOMPLISHED!", True, GREEN)
                victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
                self.screen.blit(victory_text, victory_rect)
                
                success_text = self.font.render("Eva has been rescued!", True, WHITE)
                success_rect = success_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
                self.screen.blit(success_text, success_rect)
                
                # Draw happy Wall-E and Eva
                pygame.draw.rect(self.screen, GRAY, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2, 40, 40))
                pygame.draw.rect(self.screen, YELLOW, (SCREEN_WIDTH // 2 - 55, SCREEN_HEIGHT // 2 + 5, 10, 10))
                pygame.draw.rect(self.screen, YELLOW, (SCREEN_WIDTH // 2 - 35, SCREEN_HEIGHT // 2 + 5, 10, 10))
                
                pygame.draw.ellipse(self.screen, WHITE, (SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 - 5, 35, 50))
                pygame.draw.circle(self.screen, BLUE, (SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT // 2 + 10), 4)
                pygame.draw.circle(self.screen, BLUE, (SCREEN_WIDTH // 2 + 45, SCREEN_HEIGHT // 2 + 10), 4)
                
                # Hearts
                for i in range(5):
                    heart_x = SCREEN_WIDTH // 2 - 50 + i * 20
                    heart_y = SCREEN_HEIGHT // 2 - 30 + math.sin(pygame.time.get_ticks() * 0.01 + i) * 5
                    pygame.draw.circle(self.screen, RED, (int(heart_x), int(heart_y)), 3)
                    pygame.draw.circle(self.screen, RED, (int(heart_x + 6), int(heart_y)), 3)
                    pygame.draw.polygon(self.screen, RED, [(heart_x - 3, heart_y + 2), (heart_x + 9, heart_y + 2), (heart_x + 3, heart_y + 8)])
                
                restart_text = self.small_font.render("Press R to play again", True, YELLOW)
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
                self.screen.blit(restart_text, restart_rect)
                
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
