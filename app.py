#!/usr/bin/env python3
"""
Math Blaster Ultra - Pygame Version
A space math shooter game where you solve problems to blast aliens!
Controls: Arrow Keys / A,D = Move | SPACE = Shoot | Type answer + ENTER = Solve | ESC = Pause
Requires: pip install pygame numpy
"""

import pygame
import random
import math
import json
import os
from datetime import datetime
from enum import Enum, auto

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 720
FPS = 60

COLOR_BG = (10, 10, 26)
COLOR_BG_TOP = (10, 10, 46)
COLOR_BG_MID = (26, 10, 62)
COLOR_BG_BOT = (10, 10, 30)
COLOR_GREEN = (0, 255, 136)
COLOR_GREEN_DARK = (0, 136, 68)
COLOR_BLUE = (68, 136, 255)
COLOR_BLUE_LIGHT = (136, 204, 255)
COLOR_YELLOW = (255, 221, 0)
COLOR_ORANGE = (255, 136, 68)
COLOR_RED = (255, 68, 68)
COLOR_RED_DARK = (170, 0, 0)
COLOR_PURPLE = (170, 68, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (136, 170, 187)
COLOR_DARK_GRAY = (102, 119, 136)

def get_font(size):
    for font_name in ['Courier New', 'Consolas', 'DejaVu Sans Mono', 'Liberation Mono', 'monospace']:
        font = pygame.font.SysFont(font_name, size, bold=True)
        return font
    return pygame.font.Font(None, size)

class SaveSystem:
    SAVE_FILE = 'mathblaster_save.json'
    def __init__(self):
        self.data = {'coins': 0, 'owned': [], 'equipped': 'default', 'achievements': {},
            'high_scores': [], 'stats': {'games_played': 0, 'total_score': 0, 'total_aliens': 0, 'max_combo': 0, 'max_level': 1},
            'audio_muted': False}
        self.load()
    def load(self):
        try:
            if os.path.exists(self.SAVE_FILE):
                with open(self.SAVE_FILE, 'r') as f:
                    self.data.update(json.load(f))
        except Exception as e:
            print(f"Save load error: {e}")
    def save(self):
        try:
            with open(self.SAVE_FILE, 'w') as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"Save error: {e}")
    def add_coins(self, n):
        self.data['coins'] += n; self.save()
    def spend_coins(self, n):
        if self.data['coins'] >= n:
            self.data['coins'] -= n; self.save(); return True
        return False
    def own_item(self, item_id):
        if item_id not in self.data['owned']:
            self.data['owned'].append(item_id); self.save()
    def equip(self, item_id):
        self.data['equipped'] = item_id; self.save()
    def unlock_achievement(self, ach_id):
        if ach_id not in self.data['achievements']:
            self.data['achievements'][ach_id] = {'unlocked': True, 'date': datetime.now().isoformat()}
            self.save(); return True
        return False
    def add_high_score(self, score, level, diff):
        self.data['high_scores'].append({'score': score, 'level': level, 'difficulty': diff, 'date': datetime.now().isoformat()})
        self.data['high_scores'].sort(key=lambda x: x['score'], reverse=True)
        self.data['high_scores'] = self.data['high_scores'][:20]; self.save()
    def update_stats(self, stats):
        self.data['stats']['games_played'] += 1
        self.data['stats']['total_score'] += stats['score']
        self.data['stats']['total_aliens'] += stats['aliens_destroyed']
        self.data['stats']['max_combo'] = max(self.data['stats']['max_combo'], stats['max_combo'])
        self.data['stats']['max_level'] = max(self.data['stats']['max_level'], stats['level'])
        self.save()
    def set_audio_muted(self, muted):
        self.data['audio_muted'] = muted; self.save()

save_sys = SaveSystem()

class AudioSystem:
    def __init__(self):
        self.muted = save_sys.data['audio_muted']
        self.sounds = {}
        self.init_sounds()
    def init_sounds(self):
        try:
            import numpy as np
            def generate_tone(freq, duration, volume=0.3, wave_type='square'):
                sample_rate = 44100
                t = np.linspace(0, duration, int(sample_rate * duration), False)
                if wave_type == 'square':
                    wave = np.sign(np.sin(2 * np.pi * freq * t))
                elif wave_type == 'sawtooth':
                    wave = 2 * (t * freq - np.floor(t * freq + 0.5))
                elif wave_type == 'sine':
                    wave = np.sin(2 * np.pi * freq * t)
                else:
                    wave = np.sin(2 * np.pi * freq * t)
                attack = int(0.01 * sample_rate)
                decay = int(0.1 * sample_rate)
                envelope = np.ones(len(t))
                envelope[:attack] = np.linspace(0, 1, attack)
                envelope[-decay:] = np.linspace(1, 0, decay)
                wave = wave * envelope * volume
                stereo = np.column_stack((wave, wave))
                stereo = (stereo * 32767).astype(np.int16)
                return pygame.sndarray.make_sound(stereo)
            self.sounds['shoot'] = generate_tone(880, 0.08, 0.15, 'square')
            self.sounds['correct'] = generate_tone(523, 0.12, 0.15, 'square')
            self.sounds['wrong'] = generate_tone(180, 0.25, 0.12, 'sawtooth')
            self.sounds['explode'] = generate_tone(120, 0.4, 0.2, 'sawtooth')
            self.sounds['powerup'] = generate_tone(440, 0.15, 0.15, 'sine')
            self.sounds['boss_hit'] = generate_tone(200, 0.12, 0.15, 'sawtooth')
            self.sounds['shield_hit'] = generate_tone(350, 0.18, 0.12, 'sine')
            self.sounds['coin'] = generate_tone(1200, 0.06, 0.1, 'sine')
            self.sounds['level_up'] = generate_tone(523, 0.2, 0.15, 'square')
            self.sounds['game_over'] = generate_tone(400, 0.35, 0.15, 'sawtooth')
            self.sounds['wave_start'] = generate_tone(330, 0.15, 0.12, 'square')
            self.sounds['combo'] = generate_tone(600, 0.08, 0.12, 'square')
            self.sounds['alien_shoot'] = generate_tone(300, 0.1, 0.08, 'square')
            self.sounds['boss_appear'] = generate_tone(100, 0.6, 0.18, 'sawtooth')
            self.sounds['bomb'] = generate_tone(80, 0.5, 0.2, 'sawtooth')
            self.sounds['life_up'] = generate_tone(880, 0.15, 0.15, 'sine')
        except ImportError:
            print("NumPy not available, audio will be limited")
        except Exception as e:
            print(f"Audio init error: {e}")
    def play(self, name):
        if self.muted or name not in self.sounds:
            return
        try:
            self.sounds[name].play()
        except:
            pass
    def toggle_mute(self):
        self.muted = not self.muted
        save_sys.set_audio_muted(self.muted)
        return self.muted
    def shoot(self): self.play('shoot')
    def correct(self): self.play('correct')
    def wrong(self): self.play('wrong')
    def explode(self): self.play('explode')
    def powerup(self): self.play('powerup')
    def boss_hit(self): self.play('boss_hit')
    def shield_hit(self): self.play('shield_hit')
    def coin(self): self.play('coin')
    def level_up(self): self.play('level_up')
    def game_over(self): self.play('game_over')
    def wave_start(self): self.play('wave_start')
    def combo(self): self.play('combo')
    def alien_shoot(self): self.play('alien_shoot')
    def boss_appear(self): self.play('boss_appear')
    def bomb(self): self.play('bomb')
    def life_up(self): self.play('life_up')

audio = AudioSystem()

SHOP_ITEMS = [
    {'id': 'ship_red', 'name': 'Crimson Fighter', 'icon': '*', 'desc': 'Red ship skin', 'price': 500, 'type': 'skin'},
    {'id': 'ship_gold', 'name': 'Golden Ace', 'icon': '^', 'desc': 'Gold ship skin', 'price': 1500, 'type': 'skin'},
    {'id': 'ship_purple', 'name': 'Void Walker', 'icon': 'O', 'desc': 'Purple UFO skin', 'price': 3000, 'type': 'skin'},
    {'id': 'extra_life', 'name': 'Extra Life', 'icon': '+', 'desc': 'Start with +1 life', 'price': 800, 'type': 'upgrade'},
    {'id': 'shield_boost', 'name': 'Shield Boost', 'icon': 'S', 'desc': 'Start with shield', 'price': 1000, 'type': 'upgrade'},
    {'id': 'coin_magnet', 'name': 'Coin Magnet', 'icon': 'M', 'desc': 'Attract nearby coins', 'price': 1200, 'type': 'upgrade'},
    {'id': 'rapid_fire', 'name': 'Rapid Fire', 'icon': 'R', 'desc': 'Faster shooting', 'price': 1500, 'type': 'upgrade'},
    {'id': 'double_xp', 'name': 'Double XP', 'icon': 'X', 'desc': '2x XP gain', 'price': 2000, 'type': 'upgrade'},
]

ACHIEVEMENTS = [
    {'id': 'first_blood', 'name': 'First Blood', 'desc': 'Destroy your first alien', 'icon': '*'},
    {'id': 'combo_5', 'name': 'On Fire', 'desc': 'Reach a 5x combo', 'icon': 'F'},
    {'id': 'combo_10', 'name': 'Unstoppable', 'desc': 'Reach a 10x combo', 'icon': 'U'},
    {'id': 'combo_20', 'name': 'Math God', 'desc': 'Reach a 20x combo', 'icon': 'G'},
    {'id': 'level_5', 'name': 'Space Cadet', 'desc': 'Reach level 5', 'icon': '5'},
    {'id': 'level_10', 'name': 'Space Captain', 'desc': 'Reach level 10', 'icon': 'T'},
    {'id': 'level_20', 'name': 'Galactic Emperor', 'desc': 'Reach level 20', 'icon': 'E'},
    {'id': 'score_5000', 'name': 'High Scorer', 'desc': 'Score 5,000 points', 'icon': 'H'},
    {'id': 'score_10000', 'name': 'Legend', 'desc': 'Score 10,000 points', 'icon': 'L'},
    {'id': 'boss_slayer', 'name': 'Boss Slayer', 'desc': 'Defeat a boss', 'icon': 'B'},
    {'id': 'perfect_wave', 'name': 'Perfect Wave', 'desc': 'Clear a wave without damage', 'icon': 'P'},
    {'id': 'speed_demon', 'name': 'Speed Demon', 'desc': 'Answer 10 problems in 30s', 'icon': 'D'},
    {'id': 'collector', 'name': 'Collector', 'desc': 'Collect 50 coins in one game', 'icon': 'C'},
    {'id': 'survivor', 'name': 'Survivor', 'desc': 'Survive 5 minutes', 'icon': 'V'},
    {'id': 'shopaholic', 'name': 'Shopaholic', 'desc': 'Buy 5 items from the shop', 'icon': '$'},
]

SKINS = {
    'default': {'body': COLOR_GREEN, 'glow': COLOR_GREEN, 'cockpit': COLOR_BLUE_LIGHT, 'flame': COLOR_ORANGE},
    'ship_red': {'body': COLOR_RED, 'glow': COLOR_RED, 'cockpit': (255, 170, 170), 'flame': COLOR_YELLOW},
    'ship_gold': {'body': COLOR_YELLOW, 'glow': COLOR_YELLOW, 'cockpit': (255, 255, 170), 'flame': COLOR_ORANGE},
    'ship_purple': {'body': COLOR_PURPLE, 'glow': COLOR_PURPLE, 'cockpit': (221, 170, 255), 'flame': (255, 68, 255)},
}

DIFFICULTY = {
    'easy': {'lives': 5, 'alien_speed': 0.6, 'spawn_rate': 0.005, 'ops': ['+', '-'], 'max_num': 8},
    'medium': {'lives': 3, 'alien_speed': 1.0, 'spawn_rate': 0.008, 'ops': ['+', '-', '*'], 'max_num': 12},
    'hard': {'lives': 2, 'alien_speed': 1.4, 'spawn_rate': 0.012, 'ops': ['+', '-', '*', '/'], 'max_num': 15},
    'insane': {'lives': 1, 'alien_speed': 1.8, 'spawn_rate': 0.015, 'ops': ['+', '-', '*', '/'], 'max_num': 20},
}

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    LEVEL_UP = auto()
    SHOP = auto()
    ACHIEVEMENTS = auto()
    LEADERBOARD = auto()

class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.uniform(0.5, 3)
        self.speed = random.uniform(0.2, 1.2)
        self.brightness = random.random()
        self.layer = random.randint(0, 2)
    def update(self, dt):
        self.y += self.speed * self.layer * dt
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)
    def draw(self, screen):
        alpha = self.brightness * (0.4 + math.sin(pygame.time.get_ticks() * 0.001 + self.x) * 0.4)
        alpha = max(0, min(1, alpha))
        size = self.size * (self.layer + 1) / 2
        color = (170, 187, 255) if self.layer == 2 else COLOR_WHITE
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(size))

class Particle:
    def __init__(self, x, y, color, speed=5, size=4, ptype='normal'):
        angle = random.uniform(0, math.pi * 2)
        spd = random.uniform(2, speed)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.life = 1.0
        self.decay = random.uniform(0.015, 0.035)
        self.color = color
        self.size = size
        self.type = ptype
        self.max_size = 150 if ptype == 'shockwave' else 0
    def update(self, dt):
        if self.type == 'shockwave':
            self.life -= self.decay
        else:
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.vy += 0.05
            self.life -= self.decay
    def draw(self, screen):
        if self.type == 'shockwave':
            alpha = int(self.life * 128)
            r = int(self.max_size * (1 - self.life))
            if r > 0:
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, alpha), (r, r), r, max(1, int(3 * self.life)))
                screen.blit(s, (int(self.x - r), int(self.y - r)))
        else:
            alpha = int(self.life * 255)
            s = self.size * self.life
            if s > 0:
                color_with_alpha = (*self.color, alpha)
                surf = pygame.Surface((int(s*2), int(s*2)), pygame.SRCALPHA)
                pygame.draw.circle(surf, color_with_alpha, (int(s), int(s)), int(s))
                screen.blit(surf, (int(self.x - s), int(self.y - s)))

class FloatingText:
    def __init__(self, x, y, text, color, size=14):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.life = 1.0
        self.vy = -2.5
        self.font = get_font(size)
    def update(self):
        self.y += self.vy
        self.life -= 0.02
    def draw(self, screen):
        if self.life > 0:
            alpha = int(self.life * 255)
            text_surf = self.font.render(self.text, True, self.color)
            text_surf.set_alpha(alpha)
            rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(text_surf, rect)

class Bullet:
    def __init__(self, x, y, is_boss=False, vx=0, vy=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy if vy is not None else (3 if is_boss else -10)
        self.is_boss = is_boss
        self.width = 6
        self.height = 16
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
    def draw(self, screen):
        color = COLOR_RED if self.is_boss else COLOR_GREEN
        pygame.draw.rect(screen, color, (int(self.x - 3), int(self.y - 8), 6, 16))
        glow_color = (255, 170, 170) if self.is_boss else (204, 255, 238)
        pygame.draw.rect(screen, glow_color, (int(self.x - 1), int(self.y - 6), 2, 12))

class PowerUp:
    def __init__(self, x, y, ptype):
        self.x = x
        self.y = y
        self.type = ptype
        self.icons = {'shield': 'S', 'rapid': 'R', 'slow': 'Z', 'bomb': 'B', 'life': 'L', 'coin': '$'}
        self.colors = {'shield': COLOR_BLUE, 'rapid': COLOR_YELLOW, 'slow': COLOR_BLUE_LIGHT,
                       'bomb': COLOR_RED, 'life': COLOR_RED, 'coin': COLOR_YELLOW}
        self.icon = self.icons.get(ptype, '*')
        self.color = self.colors.get(ptype, COLOR_WHITE)
        self.vy = -3
        self.vy2 = 0.5
        self.life = 300
    def update(self):
        self.vy2 += 0.05
        self.y += self.vy + self.vy2
        self.life -= 1
    def draw(self, screen):
        s = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 50), (20, 20), 18)
        screen.blit(s, (int(self.x - 20), int(self.y - 20)))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 18, 2)
        font = get_font(16)
        text = font.render(self.icon, True, self.color)
        rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, rect)

class Coin:
    def __init__(self, x, y, value=1):
        self.x = x
        self.y = y
        self.value = value
        self.vy = -2
        self.vx = random.uniform(-2, 2)
        self.life = 400
    def update(self):
        self.vy += 0.08
        self.y += self.vy
        self.x += self.vx
        self.life -= 1
    def draw(self, screen):
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(s, (*COLOR_YELLOW, 80), (12, 12), 10)
        screen.blit(s, (int(self.x - 12), int(self.y - 12)))
        pygame.draw.circle(screen, COLOR_YELLOW, (int(self.x), int(self.y)), 8)
        font = get_font(10)
        text = font.render('$', True, (170, 136, 0))
        rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, rect)

class Alien:
    def __init__(self, problem, level, difficulty):
        margin = 100
        self.x = margin + random.random() * (SCREEN_WIDTH - margin * 2)
        self.y = -70
        self.width = 55
        self.height = 55
        diff = DIFFICULTY[difficulty]
        self.speed = diff['alien_speed'] * (0.8 + random.random() * 0.4) * (1 + level * 0.05)
        self.problem = problem
        self.wobble = random.random() * math.pi * 2
        self.wobble_speed = 0.02 + random.random() * 0.02
        self.health = 1
        self.flash = 0
        self.type = random.randint(0, 3)
        self.shoot_timer = random.randint(100, 200)
        self.alien_colors = [COLOR_RED, COLOR_ORANGE, (255, 68, 255), (68, 255, 136)]
    def update(self, dt, slow_motion):
        actual_dt = dt * 0.3 if slow_motion > 0 else dt
        self.y += self.speed * actual_dt
        self.wobble += self.wobble_speed
        self.x += math.sin(self.wobble) * 0.5
        self.shoot_timer -= 1
        if self.flash > 0:
            self.flash -= 1
    def draw(self, screen):
        main_color = self.alien_colors[self.type]
        if self.flash > 0:
            main_color = tuple(min(255, c + 100) for c in main_color)
        s = pygame.Surface((self.width + 30, self.height + 30), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (*main_color, 60), (0, 0, self.width + 30, self.height + 30))
        screen.blit(s, (int(self.x - self.width/2 - 15), int(self.y - self.height/2.5 - 15)))
        pygame.draw.ellipse(screen, main_color, 
                           (int(self.x - self.width/2), int(self.y - self.height/2.5), 
                            self.width, int(self.height/1.25)))
        cockpit_rect = pygame.Rect(int(self.x - self.width/3.5), int(self.y - self.height/5),
                                   int(self.width/1.75), int(self.height/4))
        pygame.draw.ellipse(screen, COLOR_BLUE_LIGHT, cockpit_rect)
        eye_offset = math.sin(self.wobble) * 3
        pygame.draw.circle(screen, COLOR_YELLOW, (int(self.x - self.width/5 + eye_offset), int(self.y - self.height/10)), 5)
        pygame.draw.circle(screen, COLOR_YELLOW, (int(self.x + self.width/5 + eye_offset), int(self.y - self.height/10)), 5)
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x - self.width/5 + eye_offset), int(self.y - self.height/10)), 2)
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x + self.width/5 + eye_offset), int(self.y - self.height/10)), 2)
        pygame.draw.line(screen, main_color, 
                        (int(self.x - self.width/4), int(self.y - self.height/2.5)),
                        (int(self.x - self.width/3), int(self.y - self.height/1.8)), 2)
        pygame.draw.line(screen, main_color,
                        (int(self.x + self.width/4), int(self.y - self.height/2.5)),
                        (int(self.x + self.width/3), int(self.y - self.height/1.8)), 2)
        font = get_font(11)
        text = font.render(self.problem['text'], True, COLOR_WHITE)
        rect = text.get_rect(center=(int(self.x), int(self.y + self.height/2 + 20)))
        screen.blit(text, rect)

class Boss:
    def __init__(self, problem, level):
        self.x = SCREEN_WIDTH / 2
        self.y = 100
        self.width = 120
        self.height = 100
        self.max_health = 5 + level * 2
        self.health = self.max_health
        self.speed = 1.5
        self.direction = 1
        self.problem = problem
        self.wobble = 0
        self.shoot_timer = 80
        self.flash = 0
        self.phase = 0
    def update(self, dt, slow_motion):
        actual_dt = dt * 0.3 if slow_motion > 0 else dt
        self.x += self.speed * self.direction * actual_dt
        if self.x < self.width/2 + 20 or self.x > SCREEN_WIDTH - self.width/2 - 20:
            self.direction *= -1
        self.wobble += 0.02
        self.shoot_timer -= 1
        if self.flash > 0:
            self.flash -= 1
    def draw(self, screen):
        s = pygame.Surface((self.width + 60, self.height + 60), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (255, 0, 0, 80), (0, 0, self.width + 60, self.height + 60))
        screen.blit(s, (int(self.x - self.width/2 - 30), int(self.y - self.height/2.2 - 30)))
        body_color = (170, 0, 0) if self.flash == 0 else (255, 100, 100)
        pygame.draw.ellipse(screen, body_color,
                           (int(self.x - self.width/2), int(self.y - self.height/2.2),
                            self.width, int(self.height/1.1)))
        for i in range(8):
            angle = (math.pi * 2 * i) / 8 + self.wobble * 0.5
            sx = math.cos(angle) * self.width/2
            sy = math.sin(angle) * self.height/2.2
            ex = math.cos(angle) * (self.width/2 + 15)
            ey = math.sin(angle) * (self.height/2.2 + 15)
            pygame.draw.polygon(screen, COLOR_RED, [
                (int(self.x + sx), int(self.y + sy)),
                (int(self.x + ex), int(self.y + ey)),
                (int(self.x + math.cos(angle + 0.3) * (self.width/2 + 10)), 
                 int(self.y + math.sin(angle + 0.3) * (self.height/2.2 + 10)))
            ])
        pygame.draw.ellipse(screen, (255, 0, 0), 
                           (int(self.x - self.width/5 - 12), int(self.y - self.height/6 - 15), 24, 30))
        pygame.draw.ellipse(screen, (255, 0, 0),
                           (int(self.x + self.width/5 - 12), int(self.y - self.height/6 - 15), 24, 30))
        pygame.draw.circle(screen, COLOR_YELLOW, (int(self.x - self.width/5), int(self.y - self.height/6)), 5)
        pygame.draw.circle(screen, COLOR_YELLOW, (int(self.x + self.width/5), int(self.y - self.height/6)), 5)
        pygame.draw.arc(screen, COLOR_RED, 
                       (int(self.x - self.width/6), int(self.y), int(self.width/3), int(self.height/3)),
                       0.2, math.pi - 0.2, 3)
        font = get_font(13)
        text = font.render(self.problem['text'], True, COLOR_YELLOW)
        rect = text.get_rect(center=(int(self.x), int(self.y + self.height/2 + 25)))
        screen.blit(text, rect)

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT - 90
        self.width = 50
        self.height = 50
        self.speed = 7
        self.shoot_cooldown = 0
        self.skin = 'default'
    def update(self, keys, dt, rapid_fire):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed * dt
        self.x = max(self.width/2, min(SCREEN_WIDTH - self.width/2, self.x))
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    def draw(self, screen, shield, shield_max):
        skin = SKINS.get(self.skin, SKINS['default'])
        if shield > 0:
            alpha = int(shield / shield_max * 150)
            s = pygame.Surface((84, 84), pygame.SRCALPHA)
            pygame.draw.circle(s, (68, 136, 255, alpha), (42, 42), 40, 3)
            pygame.draw.circle(s, (68, 136, 255, alpha // 3), (42, 42), 40)
            screen.blit(s, (int(self.x - 42), int(self.y - 42)))
        s = pygame.Surface((self.width + 40, self.height + 40), pygame.SRCALPHA)
        pygame.draw.polygon(s, (*skin['glow'], 80), [
            (self.width/2 + 20, 0),
            (0, self.height + 20),
            (self.width/2 + 20, self.height * 0.67 + 20),
            (self.width + 40, self.height + 20)
        ])
        screen.blit(s, (int(self.x - self.width/2 - 20), int(self.y - self.height/2 - 20)))
        pygame.draw.polygon(screen, skin['body'], [
            (int(self.x), int(self.y - self.height/2)),
            (int(self.x - self.width/2), int(self.y + self.height/2)),
            (int(self.x), int(self.y + self.height/3)),
            (int(self.x + self.width/2), int(self.y + self.height/2))
        ])
        pygame.draw.ellipse(screen, skin['cockpit'],
                           (int(self.x - 8), int(self.y - self.height/6 - 12), 16, 24))
        flame_height = 10 + random.random() * 8
        pygame.draw.polygon(screen, skin['flame'], [
            (int(self.x - 8), int(self.y + self.height/3)),
            (int(self.x), int(self.y + self.height/3 + flame_height)),
            (int(self.x + 8), int(self.y + self.height/3))
        ])
        pygame.draw.polygon(screen, COLOR_YELLOW, [
            (int(self.x - 4), int(self.y + self.height/3)),
            (int(self.x), int(self.y + self.height/3 + flame_height * 0.6)),
            (int(self.x + 4), int(self.y + self.height/3))
        ])

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color=None, text_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color or color
        self.text_color = text_color or (10, 10, 46)
        self.hovered = False
        self.font = get_font(11)
    def draw(self, screen):
        color = self.hover_color if self.hovered else self.color
        shadow_rect = self.rect.copy()
        shadow_rect.y += 4
        shadow_color = (0, 136, 68) if self.color == COLOR_GREEN else ((17, 68, 170) if self.color == COLOR_BLUE else (170, 17, 17))
        pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=6)
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class DifficultyCard:
    def __init__(self, x, y, diff_id, name, desc, color):
        self.rect = pygame.Rect(x, y, 120, 100)
        self.diff_id = diff_id
        self.name = name
        self.desc = desc
        self.color = color
        self.selected = False
        self.hovered = False
        self.title_font = get_font(11)
        self.desc_font = get_font(7)
    def draw(self, screen):
        border_color = COLOR_GREEN if self.selected else (self.color if self.hovered else (68, 68, 85))
        bg_color = (0, 255, 136, 26) if self.selected else (0, 20, 40)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=8)
        if self.selected:
            s = pygame.Surface((self.rect.width + 10, self.rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 255, 136, 30), (0, 0, self.rect.width + 10, self.rect.height + 10), border_radius=8)
            screen.blit(s, (self.rect.x - 5, self.rect.y - 5))
        title = self.title_font.render(self.name, True, self.color)
        screen.blit(title, title.get_rect(centerx=self.rect.centerx, top=self.rect.top + 10))
        lines = self.desc.split('
')
        for i, line in enumerate(lines):
            text = self.desc_font.render(line, True, COLOR_GRAY)
            screen.blit(text, text.get_rect(centerx=self.rect.centerx, top=self.rect.top + 35 + i * 18))
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Math Blaster Ultra")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU
        self.difficulty = 'medium'
        self.reset_game_vars()
        self.stars = [Star() for _ in range(150)]
        self.player = Player()
        self.aliens = []
        self.bullets = []
        self.particles = []
        self.floating_texts = []
        self.powerups = []
        self.coins_arr = []
        self.boss = None
        self.screen_shake = 0
        self.slow_motion = 0
        self.answer_input = ""
        self.notifications = []
        self.wave_indicator_timer = 0
        self.wave_indicator_text = ""
        self.init_ui()
        self.font_small = get_font(9)
        self.font_medium = get_font(11)
        self.font_large = get_font(18)
        self.font_title = get_font(32)

    def reset_game_vars(self):
        self.score = 0; self.level = 1; self.wave = 1; self.lives = 3; self.coins = 0
        self.combo = 0; self.max_combo = 0; self.xp = 0; self.xp_needed = 100
        self.aliens_destroyed = 0; self.aliens_needed = 8; self.total_answers = 0; self.correct_answers = 0
        self.game_time = 0; self.wave_start_time = 0; self.wave_damage = 0
        self.shield = 0; self.shield_max = 100; self.rapid_fire = False; self.double_xp = False
        self.coin_magnet = False; self.powerup_timers = {}; self.is_boss_level = False

    def init_ui(self):
        center_x = SCREEN_WIDTH // 2
        self.btn_start = Button(center_x - 100, 480, 200, 40, "START MISSION", COLOR_GREEN, (0, 230, 120), (10, 10, 46))
        self.btn_shop = Button(center_x - 100, 530, 95, 35, "SHOP", COLOR_BLUE, (60, 120, 240), COLOR_WHITE)
        self.btn_achievements = Button(center_x + 5, 530, 95, 35, "ACHIEVEMENTS", COLOR_BLUE, (60, 120, 240), COLOR_WHITE)
        self.btn_leaderboard = Button(center_x - 100, 575, 200, 35, "LEADERBOARD", COLOR_BLUE, (60, 120, 240), COLOR_WHITE)
        self.diff_cards = [
            DifficultyCard(center_x - 260, 350, 'easy', 'EASY', '+ Add/Sub only
Slower aliens
5 lives', (68, 255, 68)),
            DifficultyCard(center_x - 130, 350, 'medium', 'MEDIUM', '+ Mult included
Normal speed
3 lives', COLOR_YELLOW),
            DifficultyCard(center_x, 350, 'hard', 'HARD', '+ Division too
Fast aliens
2 lives', COLOR_RED),
            DifficultyCard(center_x + 130, 350, 'insane', 'INSANE', 'All operations
Very fast
1 life only', (255, 68, 255)),
        ]
        self.diff_cards[1].selected = True
        self.btn_restart = Button(center_x - 100, 520, 200, 40, "RETRY MISSION", COLOR_GREEN, (0, 230, 120), (10, 10, 46))
        self.btn_go_shop = Button(center_x - 100, 570, 200, 35, "SHOP", COLOR_BLUE, (60, 120, 240), COLOR_WHITE)
        self.btn_resume = Button(center_x - 75, 320, 150, 40, "RESUME", COLOR_GREEN, (0, 230, 120), (10, 10, 46))
        self.btn_pause_shop = Button(center_x - 75, 370, 150, 35, "SHOP", COLOR_BLUE, (60, 120, 240), COLOR_WHITE)
        self.btn_quit = Button(center_x - 75, 415, 150, 35, "QUIT", COLOR_RED, (240, 60, 60), COLOR_WHITE)
        self.btn_shop_back = Button(center_x - 75, 650, 150, 35, "BACK", COLOR_GREEN, (0, 230, 120), (10, 10, 46))
        self.btn_ach_back = Button(center_x - 75, 650, 150, 35, "BACK", COLOR_GREEN, (0, 230, 120), (10, 10, 46))
        self.btn_lb_back = Button(center_x - 75, 650, 150, 35, "BACK", COLOR_GREEN, (0, 230, 120), (10, 10, 46))
        self.btn_audio = Button(18, 12, 120, 30, "SOUND OFF" if audio.muted else "SOUND ON",
                               COLOR_GREEN if not audio.muted else COLOR_RED, None, COLOR_GREEN if not audio.muted else COLOR_RED)

    def generate_problem(self):
        diff = DIFFICULTY[self.difficulty]
        ops = diff['ops']
        op = random.choice(ops)
        max_num = min(diff['max_num'] + self.level * 2, 50)
        if op == '+':
            a = random.randint(1, max_num); b = random.randint(1, max_num); answer = a + b
        elif op == '-':
            a = random.randint(3, max_num); b = random.randint(1, min(a, max_num)); answer = a - b
        elif op == '*':
            a = random.randint(2, min(self.level + 3, 12)); b = random.randint(2, min(self.level + 3, 12)); answer = a * b
        else:
            b = random.randint(2, min(self.level + 2, 10)); answer = random.randint(1, max_num // 2); a = b * answer
        op_display = 'x' if op == '*' else '/' if op == '/' else op
        return {'text': f"{a} {op_display} {b} = ?", 'answer': answer}

    def spawn_alien(self):
        if self.boss: return
        problem = self.generate_problem()
        self.aliens.append(Alien(problem, self.level, self.difficulty))

    def spawn_boss(self):
        self.is_boss_level = True
        problem = self.generate_problem()
        self.boss = Boss(problem, self.level)
        self.show_notification('BOSS APPROACHING!')
        audio.boss_appear()

    def spawn_powerup(self, x, y):
        types = ['shield', 'rapid', 'slow', 'bomb', 'life', 'coin']
        ptype = random.choice(types)
        self.powerups.append(PowerUp(x, y, ptype))

    def spawn_coin(self, x, y, val=1):
        self.coins_arr.append(Coin(x, y, val))

    def create_explosion(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def create_shockwave(self, x, y, color):
        self.particles.append(Particle(x, y, color, ptype='shockwave'))

    def create_floating_text(self, x, y, text, color, size=14):
        self.floating_texts.append(FloatingText(x, y, text, color, size))

    def show_notification(self, text):
        self.notifications.append({'text': text, 'timer': 120, 'y': 75})

    def screen_shake_effect(self, amount):
        self.screen_shake = amount

    def activate_powerup(self, ptype):
        audio.powerup()
        if ptype == 'shield':
            self.shield = self.shield_max; self.show_notification('SHIELD RESTORED!')
        elif ptype == 'rapid':
            self.rapid_fire = True; self.powerup_timers['rapid'] = 600; self.show_notification('RAPID FIRE!')
        elif ptype == 'slow':
            self.slow_motion = 300; self.show_notification('TIME SLOWED!')
        elif ptype == 'bomb':
            for alien in self.aliens[:]: self.create_explosion(alien.x, alien.y, COLOR_ORANGE, 20); self.score += 50
            self.aliens = []; self.show_notification('ALL ALIENS DESTROYED!'); audio.bomb()
        elif ptype == 'life':
            self.lives = min(self.lives + 1, 5); self.show_notification('EXTRA LIFE!'); audio.life_up()
        elif ptype == 'coin':
            bonus = 50 + random.randint(0, 50); self.coins += bonus
            self.create_floating_text(self.player.x, self.player.y - 40, f"+${bonus}", COLOR_YELLOW, 16); audio.coin()

    def check_answer(self):
        if not self.answer_input.strip(): return
        try:
            answer = int(self.answer_input.strip())
        except ValueError:
            self.answer_input = ""; return
        self.total_answers += 1; hit = False
        for i in range(len(self.aliens) - 1, -1, -1):
            alien = self.aliens[i]
            if alien.problem['answer'] == answer:
                self.create_explosion(alien.x, alien.y, COLOR_GREEN, 15)
                self.combo += 1
                if self.combo > self.max_combo: self.max_combo = self.combo
                mult = 2 if (self.double_xp or 'double_xp' in save_sys.data['owned']) else 1
                points = 100 * self.combo * mult
                self.score += points; self.aliens_destroyed += 1; self.correct_answers += 1
                self.xp += 20 * mult
                if self.xp >= self.xp_needed:
                    self.xp = 0; self.xp_needed = int(self.xp_needed * 1.2)
                    self.show_notification('LEVEL UP! Stats boosted!')
                self.create_floating_text(alien.x, alien.y - 20, f"+{points}", COLOR_GREEN)
                if self.combo > 1:
                    self.create_floating_text(alien.x, alien.y - 40, f"{self.combo}x COMBO!", COLOR_YELLOW, 16); audio.combo()
                if random.random() < 0.15: self.spawn_powerup(alien.x, alien.y)
                if random.random() < 0.4: self.spawn_coin(alien.x, alien.y, 1 + random.randint(0, 2))
                self.aliens.pop(i); hit = True; audio.correct(); self.check_achievement('first_blood'); break
        if not hit and self.boss and self.boss.problem['answer'] == answer:
            self.boss.health -= 1; self.boss.flash = 10
            self.create_explosion(self.boss.x, self.boss.y, COLOR_RED, 20); self.score += 200; self.correct_answers += 1
            self.create_floating_text(self.boss.x, self.boss.y - 30, "DIRECT HIT!", COLOR_YELLOW, 16); audio.boss_hit()
            if self.boss.health <= 0:
                self.create_explosion(self.boss.x, self.boss.y, (255, 0, 0), 40)
                self.create_shockwave(self.boss.x, self.boss.y, COLOR_RED)
                self.create_floating_text(self.boss.x, self.boss.y - 50, "BOSS DEFEATED!", COLOR_YELLOW, 22)
                self.boss = None; self.is_boss_level = False; self.score += 500 * self.level
                self.screen_shake_effect(15); audio.explode(); self.check_achievement('boss_slayer')
                pygame.time.set_timer(pygame.USEREVENT + 1, 1500)
            else:
                self.boss.problem = self.generate_problem()
            hit = True
        if not hit:
            self.combo = 0; self.create_floating_text(self.player.x, self.player.y - 30, "WRONG!", COLOR_RED)
            self.score = max(0, self.score - 50); audio.wrong()
        self.answer_input = ""

    def check_achievement(self, ach_id):
        if save_sys.unlock_achievement(ach_id):
            ach = next((a for a in ACHIEVEMENTS if a['id'] == ach_id), None)
            if ach: self.show_notification(f"ACHIEVEMENT: {ach['name']}!")

    def level_up(self):
        self.level += 1; self.wave = 1; self.aliens_destroyed = 0; self.aliens_needed = 8 + self.level * 2
        self.aliens = []; self.bullets = []; self.boss = None; self.is_boss_level = False
        self.state = GameState.PLAYING; self.wave_start_time = self.game_time; self.wave_damage = 0
        self.show_wave_indicator(); audio.wave_start()

    def show_wave_indicator(self):
        self.wave_indicator_text = f"WAVE {self.wave}/3"; self.wave_indicator_timer = 90

    def game_over(self):
        self.state = GameState.GAME_OVER; audio.game_over()
        accuracy = round(self.correct_answers / self.total_answers * 100) if self.total_answers > 0 else 0
        coins_earned = self.score // 50 + self.coins
        save_sys.add_coins(coins_earned)
        save_sys.add_high_score(self.score, self.level, self.difficulty)
        save_sys.update_stats({'score': self.score, 'aliens_destroyed': self.aliens_destroyed,
                              'max_combo': self.max_combo, 'level': self.level})

    def start_game(self):
        audio.coin(); self.reset_game_vars()
        diff = DIFFICULTY[self.difficulty]
        self.lives = diff['lives'] + (1 if 'extra_life' in save_sys.data['owned'] else 0)
        self.shield = self.shield_max if 'shield_boost' in save_sys.data['owned'] else 0
        self.coin_magnet = 'coin_magnet' in save_sys.data['owned']
        self.rapid_fire = 'rapid_fire' in save_sys.data['owned']
        self.double_xp = 'double_xp' in save_sys.data['owned']
        self.player.skin = save_sys.data['equipped']; self.player.x = SCREEN_WIDTH / 2
        self.aliens = []; self.bullets = []; self.particles = []; self.floating_texts = []
        self.powerups = []; self.coins_arr = []; self.boss = None; self.is_boss_level = False
        self.screen_shake = 0; self.slow_motion = 0; self.answer_input = ""
        self.state = GameState.PLAYING; self.wave_start_time = self.game_time; self.wave_damage = 0
        for i in range(3): pygame.time.set_timer(pygame.USEREVENT + 2 + i, (i + 1) * 800)
        self.show_wave_indicator()

    def update(self):
        dt = 1.0
        if self.state != GameState.PLAYING: return
        if self.slow_motion > 0: dt = 0.3; self.slow_motion -= 1
        self.game_time += 1
        if self.screen_shake > 0:
            self.screen_shake *= 0.9
            if self.screen_shake < 0.5: self.screen_shake = 0
        for star in self.stars: star.update(dt)
        keys = pygame.key.get_pressed()
        self.player.update(keys, dt, self.rapid_fire)
        if keys[pygame.K_SPACE] and self.player.shoot_cooldown <= 0:
            self.bullets.append(Bullet(self.player.x, self.player.y - self.player.height/2))
            self.player.shoot_cooldown = 8 if self.rapid_fire else 15; audio.shoot()
        diff = DIFFICULTY[self.difficulty]
        if not self.is_boss_level and random.random() < diff['spawn_rate'] * dt and len(self.aliens) < 5 + self.level:
            self.spawn_alien()
        if not self.is_boss_level and self.aliens_destroyed >= self.aliens_needed and self.wave == 3 and not self.boss:
            self.spawn_boss()
        for i in range(len(self.aliens) - 1, -1, -1):
            alien = self.aliens[i]; alien.update(dt, self.slow_motion)
            if alien.shoot_timer <= 0:
                alien.shoot_timer = random.randint(150, 250)
                self.bullets.append(Bullet(alien.x, alien.y + alien.height/2, is_boss=True)); audio.alien_shoot()
            if alien.y > SCREEN_HEIGHT - 50:
                if self.shield > 0: self.shield -= 30; audio.shield_hit(); self.create_explosion(alien.x, alien.y, COLOR_BLUE, 8)
                else: self.lives -= 1; self.wave_damage += 1
                self.create_explosion(alien.x, alien.y, COLOR_RED, 10); self.aliens.pop(i); self.combo = 0
                self.screen_shake_effect(5); audio.explode()
                if self.lives <= 0: self.game_over()
        if self.boss:
            self.boss.update(dt, self.slow_motion); self.boss.shoot_timer -= 1
            if self.boss.shoot_timer <= 0:
                self.boss.shoot_timer = random.randint(60, 100)
                for a in range(-1, 2): self.bullets.append(Bullet(self.boss.x + a * 30, self.boss.y + self.boss.height/2, is_boss=True, vx=a * 0.5))
                audio.alien_shoot()
        for i in range(len(self.bullets) - 1, -1, -1):
            b = self.bullets[i]; b.update(dt)
            if b.is_boss:
                dx = b.x - self.player.x; dy = b.y - self.player.y
                if math.sqrt(dx*dx + dy*dy) < 25:
                    if self.shield > 0: self.shield -= 20; audio.shield_hit()
                    else: self.lives -= 1; self.wave_damage += 1
                    self.bullets.pop(i); self.create_explosion(b.x, b.y, COLOR_RED, 8); self.screen_shake_effect(4); audio.explode()
                    if self.lives <= 0: self.game_over()
                    continue
            if not b.is_boss:
                hit = False
                for j in range(len(self.aliens) - 1, -1, -1):
                    alien = self.aliens[j]; dx = b.x - alien.x; dy = b.y - alien.y
                    if math.sqrt(dx*dx + dy*dy) < alien.width/2 + 10:
                        alien.flash = 5; self.bullets.pop(i); alien.health -= 1
                        if alien.health <= 0:
                            self.create_explosion(alien.x, alien.y, COLOR_ORANGE, 15)
                            self.create_floating_text(alien.x, alien.y - 20, "MISS!", COLOR_RED); self.aliens.pop(j); self.combo = 0
                        hit = True; break
                if hit: continue
                if self.boss:
                    dx = b.x - self.boss.x; dy = b.y - self.boss.y
                    if math.sqrt(dx*dx + dy*dy) < self.boss.width/2 + 10:
                        self.boss.flash = 10; self.boss.health -= 1; self.bullets.pop(i); audio.boss_hit()
                        self.create_explosion(b.x, b.y, COLOR_RED, 10)
                        if self.boss.health <= 0:
                            self.create_explosion(self.boss.x, self.boss.y, (255, 0, 0), 40)
                            self.create_shockwave(self.boss.x, self.boss.y, COLOR_RED)
                            self.create_floating_text(self.boss.x, self.boss.y - 30, "BOSS DEFEATED!", COLOR_YELLOW, 20)
                            self.boss = None; self.is_boss_level = False; self.score += 500 * self.level
                            self.screen_shake_effect(15); audio.explode(); self.check_achievement('boss_slayer')
                            pygame.time.set_timer(pygame.USEREVENT + 1, 1500)
                        continue
            if b.y < -20 or b.y > SCREEN_HEIGHT + 20: self.bullets.pop(i)
        for i in range(len(self.powerups) - 1, -1, -1):
            p = self.powerups[i]; p.update(); dx = p.x - self.player.x; dy = p.y - self.player.y
            if math.sqrt(dx*dx + dy*dy) < 35: self.activate_powerup(p.type); self.powerups.pop(i)
            elif p.life <= 0 or p.y > SCREEN_HEIGHT + 50: self.powerups.pop(i)
        for i in range(len(self.coins_arr) - 1, -1, -1):
            c = self.coins_arr[i]; c.update()
            if self.coin_magnet or 'coin_magnet' in save_sys.data['owned']:
                dx = self.player.x - c.x; dy = self.player.y - c.y; dist = math.sqrt(dx*dx + dy*dy)
                if dist < 150 and dist > 0: c.x += dx/dist * 3; c.y += dy/dist * 3
            dx = c.x - self.player.x; dy = c.y - self.player.y
            if math.sqrt(dx*dx + dy*dy) < 30:
                self.coins += c.value; self.create_floating_text(c.x, c.y, f"+${c.value}", COLOR_YELLOW, 12); audio.coin(); self.coins_arr.pop(i)
            elif c.life <= 0 or c.y > SCREEN_HEIGHT + 50: self.coins_arr.pop(i)
        for i in range(len(self.particles) - 1, -1, -1):
            p = self.particles[i]; p.update(dt)
            if p.life <= 0: self.particles.pop(i)
        for i in range(len(self.floating_texts) - 1, -1, -1):
            ft = self.floating_texts[i]; ft.update()
            if ft.life <= 0: self.floating_texts.pop(i)
        if 'rapid' in self.powerup_timers:
            self.powerup_timers['rapid'] -= 1
            if self.powerup_timers['rapid'] <= 0: self.rapid_fire = False; del self.powerup_timers['rapid']
        if self.shield > 0 and self.shield < self.shield_max and self.game_time % 60 == 0: self.shield += 1
        if not self.is_boss_level and self.aliens_destroyed >= self.aliens_needed and self.wave < 3:
            self.wave += 1; self.aliens_destroyed = 0; self.aliens_needed = 8 + self.wave * 2 + self.level
            self.show_wave_indicator(); audio.wave_start()
            if self.wave_damage == 0: self.check_achievement('perfect_wave')
            self.wave_damage = 0; self.wave_start_time = self.game_time
        if self.combo >= 5: self.check_achievement('combo_5')
        if self.combo >= 10: self.check_achievement('combo_10')
        if self.combo >= 20: self.check_achievement('combo_20')
        if self.level >= 5: self.check_achievement('level_5')
        if self.level >= 10: self.check_achievement('level_10')
        if self.level >= 20: self.check_achievement('level_20')
        if self.score >= 5000: self.check_achievement('score_5000')
        if self.score >= 10000: self.check_achievement('score_10000')
        if self.coins >= 50: self.check_achievement('collector')
        if self.game_time >= 18000: self.check_achievement('survivor')

    def draw(self):
        offset_x = (random.random() - 0.5) * self.screen_shake if self.screen_shake > 0 else 0
        offset_y = (random.random() - 0.5) * self.screen_shake if self.screen_shake > 0 else 0
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            if ratio < 0.5:
                r = int(COLOR_BG_TOP[0] + (COLOR_BG_MID[0] - COLOR_BG_TOP[0]) * (ratio * 2))
                g = int(COLOR_BG_TOP[1] + (COLOR_BG_MID[1] - COLOR_BG_TOP[1]) * (ratio * 2))
                b = int(COLOR_BG_TOP[2] + (COLOR_BG_MID[2] - COLOR_BG_TOP[2]) * (ratio * 2))
            else:
                r = int(COLOR_BG_MID[0] + (COLOR_BG_BOT[0] - COLOR_BG_MID[0]) * ((ratio - 0.5) * 2))
                g = int(COLOR_BG_MID[1] + (COLOR_BG_BOT[1] - COLOR_BG_MID[1]) * ((ratio - 0.5) * 2))
                b = int(COLOR_BG_MID[2] + (COLOR_BG_BOT[2] - COLOR_BG_MID[2]) * ((ratio - 0.5) * 2))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        for star in self.stars: star.draw(self.screen)
        if self.state in [GameState.PLAYING, GameState.PAUSED, GameState.LEVEL_UP]:
            pygame.draw.line(self.screen, (255, 68, 68), (0, SCREEN_HEIGHT - 50), (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 2)
            for alien in self.aliens: alien.draw(self.screen)
            if self.boss: self.boss.draw(self.screen)
            for bullet in self.bullets: bullet.draw(self.screen)
            for powerup in self.powerups: powerup.draw(self.screen)
            for coin in self.coins_arr: coin.draw(self.screen)
            self.player.draw(self.screen, self.shield, self.shield_max)
            for particle in self.particles: particle.draw(self.screen)
            for ft in self.floating_texts: ft.draw(self.screen)
        self.draw_ui()
        for notif in self.notifications[:]:
            notif['timer'] -= 1
            if notif['timer'] <= 0: self.notifications.remove(notif)
            else:
                alpha = min(255, int(notif['timer'] / 120 * 255))
                font = get_font(10)
                text = font.render(notif['text'], True, COLOR_YELLOW)
                text.set_alpha(alpha)
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, notif['y']))
                self.screen.blit(text, rect)
        if self.wave_indicator_timer > 0:
            self.wave_indicator_timer -= 1
            alpha = min(255, int(self.wave_indicator_timer / 90 * 255))
            font = get_font(24)
            text = font.render(self.wave_indicator_text, True, COLOR_YELLOW)
            text.set_alpha(alpha)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)

    def draw_ui(self):
        if self.state == GameState.PLAYING or self.state == GameState.PAUSED:
            pygame.draw.rect(self.screen, (0, 20, 40), (0, 0, SCREEN_WIDTH, 50))
            self.draw_ui_panel(18, 10, "SCORE", str(self.score))
            self.draw_ui_panel(200, 10, "LEVEL", str(self.level))
            self.draw_ui_panel(350, 10, "WAVE", f"{self.wave}/3")
            self.draw_ui_panel(500, 10, "LIVES", "H" * max(0, self.lives))
            self.draw_ui_panel(700, 10, "COINS", str(self.coins))
            if self.shield > 0:
                pygame.draw.rect(self.screen, (34, 34, 51), (18, 48, 100, 6), border_radius=3)
                shield_width = int(100 * self.shield / self.shield_max)
                pygame.draw.rect(self.screen, COLOR_BLUE, (18, 48, shield_width, 6), border_radius=3)
            pygame.draw.rect(self.screen, (17, 17, 34), (0, SCREEN_HEIGHT - 4, SCREEN_WIDTH, 4))
            xp_width = int(SCREEN_WIDTH * self.xp / self.xp_needed)
            pygame.draw.rect(self.screen, COLOR_YELLOW, (0, SCREEN_HEIGHT - 4, xp_width, 4))
            if self.boss:
                bar_width = 350; bar_x = (SCREEN_WIDTH - bar_width) // 2
                pygame.draw.rect(self.screen, (26, 10, 10), (bar_x, 48, bar_width, 16), border_radius=8)
                pygame.draw.rect(self.screen, COLOR_RED, (bar_x, 48, bar_width, 16), 2, border_radius=8)
                health_width = int(bar_width * self.boss.health / self.boss.max_health)
                pygame.draw.rect(self.screen, COLOR_RED, (bar_x, 48, health_width, 16), border_radius=8)
                font = get_font(10)
                text = font.render(f"MATH OVERLORD LVL {self.level}", True, COLOR_RED)
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, 35))
                self.screen.blit(text, rect)
            if self.combo > 1:
                color = (255, 68, 255) if self.combo >= 5 else COLOR_ORANGE if self.combo >= 3 else COLOR_YELLOW
                font = get_font(11)
                text = font.render(f"COMBO x{self.combo}!", True, color)
                rect = text.get_rect(right=SCREEN_WIDTH - 18, top=50)
                self.screen.blit(text, rect)
            icon_x = SCREEN_WIDTH // 2 - 30
            if self.rapid_fire: self.draw_powerup_icon(icon_x, 50, "R", COLOR_YELLOW); icon_x += 30
            if self.shield > 0: self.draw_powerup_icon(icon_x, 50, "S", COLOR_BLUE); icon_x += 30
            if self.double_xp: self.draw_powerup_icon(icon_x, 50, "X", COLOR_YELLOW)
            if self.state == GameState.PLAYING:
                input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 55, 200, 35)
                pygame.draw.rect(self.screen, (0, 20, 40), input_rect, border_radius=6)
                pygame.draw.rect(self.screen, COLOR_GREEN, input_rect, 2, border_radius=6)
                font = get_font(14)
                cursor = "|" if pygame.time.get_ticks() % 1000 < 500 else ""
                text = font.render(self.answer_input + cursor, True, COLOR_GREEN)
                rect = text.get_rect(center=input_rect.center)
                self.screen.blit(text, rect)
                if not self.answer_input:
                    placeholder = get_font(9).render("TYPE ANSWER + ENTER", True, (68, 102, 85))
                    ph_rect = placeholder.get_rect(center=input_rect.center)
                    self.screen.blit(placeholder, ph_rect)
        elif self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.PAUSED:
            self.draw_pause()
        elif self.state == GameState.SHOP:
            self.draw_shop()
        elif self.state == GameState.ACHIEVEMENTS:
            self.draw_achievements()
        elif self.state == GameState.LEADERBOARD:
            self.draw_leaderboard()
        elif self.state == GameState.LEVEL_UP:
            self.draw_level_up()

    def draw_ui_panel(self, x, y, label, value):
        panel_width = 120
        panel_height = 35
        pygame.draw.rect(self.screen, (0, 20, 40), (x, y, panel_width, panel_height), border_radius=6)
        pygame.draw.rect(self.screen, COLOR_GREEN, (x, y, panel_width, panel_height), 2, border_radius=6)
        font_small = get_font(7)
        font_medium = get_font(9)
        label_surf = font_small.render(label, True, COLOR_GRAY)
        value_surf = font_medium.render(str(value), True, COLOR_YELLOW)
        self.screen.blit(label_surf, label_surf.get_rect(centerx=x + panel_width//2, top=y + 3))
        self.screen.blit(value_surf, value_surf.get_rect(centerx=x + panel_width//2, top=y + 16))

    def draw_powerup_icon(self, x, y, icon, color):
        pygame.draw.circle(self.screen, color, (x + 12, y + 12), 12, 2)
        font = get_font(12)
        text = font.render(icon, True, color)
        rect = text.get_rect(center=(x + 12, y + 12))
        self.screen.blit(text, rect)

    def draw_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 240))
        self.screen.blit(overlay, (0, 0))
        title_font = get_font(32)
        title = title_font.render("MATH BLASTER", True, COLOR_GREEN)
        title2 = title_font.render("ULTRA", True, COLOR_GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        title2_rect = title2.get_rect(center=(SCREEN_WIDTH // 2, 160))
        glow = pygame.Surface((title.get_width() + 40, title.get_height() + title2.get_height() + 40), pygame.SRCALPHA)
        pygame.draw.rect(glow, (0, 255, 136, 30), glow.get_rect(), border_radius=10)
        self.screen.blit(glow, (title_rect.x - 20, title_rect.y - 20))
        self.screen.blit(title, title_rect)
        self.screen.blit(title2, title2_rect)
        sub_font = get_font(11)
        sub = sub_font.render("SPACE MATH SHOOTER", True, COLOR_BLUE_LIGHT)
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 200)))
        inst_font = get_font(8)
        instructions = [
            "Solve math problems to blast alien ships!",
            "Type answers & press ENTER | Move: LEFT/RIGHT | Shoot: SPACE",
            "ESC to pause | Collect power-ups | Defeat bosses!"
        ]
        for i, line in enumerate(instructions):
            text = inst_font.render(line, True, COLOR_GRAY)
            self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 240 + i * 20)))
        diff_label = get_font(9).render("SELECT DIFFICULTY", True, COLOR_GRAY)
        self.screen.blit(diff_label, diff_label.get_rect(center=(SCREEN_WIDTH // 2, 310)))
        for card in self.diff_cards:
            card.draw(self.screen)
        self.btn_start.draw(self.screen)
        self.btn_shop.draw(self.screen)
        self.btn_achievements.draw(self.screen)
        self.btn_leaderboard.draw(self.screen)

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 240))
        self.screen.blit(overlay, (0, 0))
        title = get_font(32).render("MISSION", True, COLOR_RED)
        title2 = get_font(32).render("FAILED", True, COLOR_RED)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 120)))
        self.screen.blit(title2, title2.get_rect(center=(SCREEN_WIDTH // 2, 160)))
        accuracy = round(self.correct_answers / self.total_answers * 100) if self.total_answers > 0 else 0
        coins_earned = self.score // 50 + self.coins
        stats = [
            ("FINAL SCORE", str(self.score)),
            ("LEVEL REACHED", str(self.level)),
            ("ACCURACY", f"{accuracy}%"),
            ("MAX COMBO", str(self.max_combo))
        ]
        for i, (label, value) in enumerate(stats):
            x = 250 + (i % 2) * 250
            y = 220 + (i // 2) * 80
            pygame.draw.rect(self.screen, (0, 20, 40), (x - 100, y - 10, 200, 70), border_radius=8)
            pygame.draw.rect(self.screen, (68, 68, 85), (x - 100, y - 10, 200, 70), 2, border_radius=8)
            val_font = get_font(18)
            lab_font = get_font(7)
            val_surf = val_font.render(value, True, COLOR_YELLOW)
            lab_surf = lab_font.render(label, True, COLOR_GRAY)
            self.screen.blit(val_surf, val_surf.get_rect(center=(x, y + 15)))
            self.screen.blit(lab_surf, lab_surf.get_rect(center=(x, y + 45)))
        coins_text = get_font(11).render(f"+${coins_earned} coins earned", True, COLOR_YELLOW)
        self.screen.blit(coins_text, coins_text.get_rect(center=(SCREEN_WIDTH // 2, 400)))
        self.btn_restart.draw(self.screen)
        self.btn_go_shop.draw(self.screen)

    def draw_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 200))
        self.screen.blit(overlay, (0, 0))
        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 120, 300, 240)
        pygame.draw.rect(self.screen, (0, 10, 30), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_GREEN, box_rect, 2, border_radius=10)
        title = get_font(18).render("PAUSED", True, COLOR_GREEN)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)))
        self.btn_resume.draw(self.screen)
        self.btn_pause_shop.draw(self.screen)
        self.btn_quit.draw(self.screen)

    def draw_level_up(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 240))
        self.screen.blit(overlay, (0, 0))
        title = get_font(32).render("WAVE", True, COLOR_YELLOW)
        title2 = get_font(32).render("CLEARED!", True, COLOR_YELLOW)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 280)))
        self.screen.blit(title2, title2.get_rect(center=(SCREEN_WIDTH // 2, 320)))
        sub = get_font(11).render(f"Get ready for wave {self.wave}...", True, COLOR_BLUE_LIGHT)
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 370)))

    def draw_shop(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 240))
        self.screen.blit(overlay, (0, 0))
        title = get_font(32).render("SHOP", True, COLOR_GREEN)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 60)))
        currency = get_font(11).render(f"${save_sys.data['coins']} coins", True, COLOR_YELLOW)
        self.screen.blit(currency, currency.get_rect(right=SCREEN_WIDTH - 18, top=18))
        cols = 3
        item_width = 180
        item_height = 120
        start_x = (SCREEN_WIDTH - cols * item_width - (cols - 1) * 20) // 2
        start_y = 120
        for i, item in enumerate(SHOP_ITEMS):
            col = i % cols
            row = i // cols
            x = start_x + col * (item_width + 20)
            y = start_y + row * (item_height + 20)
            owned = item['id'] in save_sys.data['owned']
            equipped = save_sys.data['equipped'] == item['id']
            border_color = COLOR_GREEN if owned else (68, 68, 85)
            bg_color = (0, 20, 40)
            pygame.draw.rect(self.screen, bg_color, (x, y, item_width, item_height), border_radius=8)
            pygame.draw.rect(self.screen, border_color, (x, y, item_width, item_height), 2, border_radius=8)
            icon_font = get_font(28)
            icon = icon_font.render(item['icon'], True, COLOR_WHITE)
            self.screen.blit(icon, icon.get_rect(center=(x + item_width // 2, y + 30)))
            name_font = get_font(9)
            name = name_font.render(item['name'], True, COLOR_WHITE)
            self.screen.blit(name, name.get_rect(center=(x + item_width // 2, y + 55)))
            desc_font = get_font(7)
            desc = desc_font.render(item['desc'], True, COLOR_GRAY)
            self.screen.blit(desc, desc.get_rect(center=(x + item_width // 2, y + 75)))
            price_font = get_font(9)
            if owned:
                price_text = "EQUIPPED" if equipped else "OWNED"
                price_color = COLOR_GREEN
            else:
                price_text = f"${item['price']}"
                price_color = COLOR_YELLOW
            price = price_font.render(price_text, True, price_color)
            self.screen.blit(price, price.get_rect(center=(x + item_width // 2, y + 100)))
            item['rect'] = pygame.Rect(x, y, item_width, item_height)
        self.btn_shop_back.draw(self.screen)

    def draw_achievements(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 240))
        self.screen.blit(overlay, (0, 0))
        title = get_font(32).render("ACHIEVEMENTS", True, COLOR_GREEN)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 60)))
        cols = 3
        item_width = 280
        item_height = 60
        start_x = (SCREEN_WIDTH - cols * item_width - (cols - 1) * 20) // 2
        start_y = 120
        for i, ach in enumerate(ACHIEVEMENTS):
            col = i % cols
            row = i // cols
            x = start_x + col * (item_width + 20)
            y = start_y + row * (item_height + 15)
            unlocked = ach['id'] in save_sys.data['achievements']
            border_color = COLOR_YELLOW if unlocked else (51, 51, 68)
            bg_color = (255, 221, 0, 13) if unlocked else (0, 20, 40)
            pygame.draw.rect(self.screen, bg_color, (x, y, item_width, item_height), border_radius=6)
            pygame.draw.rect(self.screen, border_color, (x, y, item_width, item_height), 2, border_radius=6)
            icon_font = get_font(20)
            icon = icon_font.render(ach['icon'], True, COLOR_WHITE)
            self.screen.blit(icon, (x + 10, y + item_height // 2 - 10))
            name_font = get_font(8)
            name_color = COLOR_YELLOW if unlocked else COLOR_WHITE
            name = name_font.render(ach['name'], True, name_color)
            self.screen.blit(name, (x + 45, y + 12))
            desc_font = get_font(6)
            desc_color = COLOR_GRAY if unlocked else (102, 119, 136)
            desc = desc_font.render(ach['desc'], True, desc_color)
            self.screen.blit(desc, (x + 45, y + 32))
        self.btn_ach_back.draw(self.screen)

    def draw_leaderboard(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 240))
        self.screen.blit(overlay, (0, 0))
        title = get_font(32).render("LEADERBOARD", True, COLOR_GREEN)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 60)))
        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 100, 400, 450)
        pygame.draw.rect(self.screen, (0, 20, 40), box_rect, border_radius=8)
        pygame.draw.rect(self.screen, (68, 68, 85), box_rect, 2, border_radius=8)
        scores = save_sys.data['high_scores']
        if not scores:
            text = get_font(10).render("No scores yet!", True, (102, 119, 136))
            self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 300)))
        else:
            for i, entry in enumerate(scores[:10]):
                y = 130 + i * 40
                colors = [COLOR_YELLOW, (204, 204, 204), (205, 127, 50)]
                color = colors[i] if i < 3 else COLOR_GRAY
                font = get_font(9)
                left_text = font.render(f"#{i+1} {entry['difficulty'].upper()} LVL {entry['level']}", True, color)
                right_text = font.render(str(entry['score']), True, color)
                self.screen.blit(left_text, (box_rect.x + 20, y))
                self.screen.blit(right_text, right_text.get_rect(right=box_rect.right - 20, top=y))
                if i < len(scores) - 1:
                    pygame.draw.line(self.screen, (34, 34, 51), (box_rect.x + 20, y + 30), (box_rect.right - 20, y + 30))
        self.btn_lb_back.draw(self.screen)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.USEREVENT + 1:
                self.level_up()
            if event.type == pygame.USEREVENT + 2:
                self.spawn_alien()
            if event.type == pygame.USEREVENT + 3:
                self.spawn_alien()
            if event.type == pygame.USEREVENT + 4:
                self.spawn_alien()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_audio.rect.collidepoint(event.pos):
                    muted = audio.toggle_mute()
                    self.btn_audio.text = "SOUND OFF" if muted else "SOUND ON"
                    self.btn_audio.color = COLOR_RED if muted else COLOR_GREEN
                    self.btn_audio.text_color = COLOR_RED if muted else COLOR_GREEN
            if self.state == GameState.MENU:
                if self.btn_start.handle_event(event):
                    self.start_game()
                if self.btn_shop.handle_event(event):
                    self.state = GameState.SHOP
                if self.btn_achievements.handle_event(event):
                    self.state = GameState.ACHIEVEMENTS
                if self.btn_leaderboard.handle_event(event):
                    self.state = GameState.LEADERBOARD
                for card in self.diff_cards:
                    if card.handle_event(event):
                        for c in self.diff_cards:
                            c.selected = False
                        card.selected = True
                        self.difficulty = card.diff_id
            elif self.state == GameState.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                    elif event.key == pygame.K_RETURN:
                        self.check_answer()
                    elif event.key == pygame.K_BACKSPACE:
                        self.answer_input = self.answer_input[:-1]
                    elif event.key == pygame.K_SPACE:
                        pass
                    elif event.unicode.isdigit() or (event.unicode == '-' and not self.answer_input):
                        if len(self.answer_input) < 6:
                            self.answer_input += event.unicode
            elif self.state == GameState.PAUSED:
                if self.btn_resume.handle_event(event):
                    self.state = GameState.PLAYING
                if self.btn_pause_shop.handle_event(event):
                    self.state = GameState.SHOP
                if self.btn_quit.handle_event(event):
                    self.state = GameState.MENU
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.PLAYING
            elif self.state == GameState.GAME_OVER:
                if self.btn_restart.handle_event(event):
                    self.start_game()
                if self.btn_go_shop.handle_event(event):
                    self.state = GameState.SHOP
            elif self.state == GameState.SHOP:
                if self.btn_shop_back.handle_event(event):
                    self.state = GameState.MENU
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for item in SHOP_ITEMS:
                        if 'rect' in item and item['rect'].collidepoint(event.pos):
                            self.buy_item(item)
            elif self.state == GameState.ACHIEVEMENTS:
                if self.btn_ach_back.handle_event(event):
                    self.state = GameState.MENU
            elif self.state == GameState.LEADERBOARD:
                if self.btn_lb_back.handle_event(event):
                    self.state = GameState.MENU

    def buy_item(self, item):
        if item['id'] in save_sys.data['owned']:
            if item['type'] == 'skin':
                save_sys.equip(item['id'])
                self.player.skin = item['id']
                self.show_notification(f"Equipped {item['name']}!")
            return
        if save_sys.spend_coins(item['price']):
            save_sys.own_item(item['id'])
            if item['type'] == 'skin':
                save_sys.equip(item['id'])
                self.player.skin = item['id']
            self.show_notification(f"Purchased {item['name']}!")
            audio.powerup()
            self.check_achievement('shopaholic')
        else:
            self.show_notification('Not enough coins!')
            audio.wrong()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
