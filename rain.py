import curses
import os
import time
import random
import argparse

RAIN_CHARS = ['|', '.', '`']
RAIN_PAIR_COLOR = 1
LIGHTNING_PAIR_COLOR = 2

CURSES_COLOR_MAP = {
    
    'black': curses.COLOR_BLACK,
    'red': curses.COLOR_RED,
    'green': curses.COLOR_GREEN,
    'yellow': curses.COLOR_YELLOW,
    'blue': curses.COLOR_BLUE,
    'magenta': curses.COLOR_MAGENTA,
    'cyan': curses.COLOR_CYAN,
    'white': curses.COLOR_WHITE,
}


class Raindrop:
    def __init__(self, x, y, speed, char):
        self.x = x
        self.y = y
        self.speed = speed
        self.char = char

# --- LIGHTNING ---
LIGHTNING_CHAR = ['*', '+', '#']

LIGHTNING_CHANCES = 0.007
LIGHTNING_GROWTH_DELAY = 0.002
LIGHTNING_MAX_BRANCHES = 3
LIGHTNING_BRANCH_CHANCES = 0.3
LIGHTNING_LIFESPAN = 0.7

class Lightningbolts:
    def __init__(self, st_x, st_y, max_x, max_y):
        self.max_x = max_x
        self.max_y = max_y
        
        self.is_growing = True
        self.last_growing = time.time()
        
        self.target_len = random.randint(max_x // 3, max_x // 2) + 5
        self.segments = [(st_x, st_y, time.time())]
    
    @property
    def height(self):
        return self.segments[-1][0] - self.segments[0][0] + 1
    
    def gen(self, x, y, mi:int, ma:int, new_segments):
        
        def inside(x, y):
            return 0 <= x < self.max_x and 0 <= y < self.max_y  
        
        offset = random.randint(mi, ma);
        new_branch = (x + 1, y + offset, time.time())
        
        if not (new_branch in new_segments) and inside(x + 1, y + offset): 
            new_segments.append(new_branch)
    
    
    def update(self):
        
        currentTime = time.time()
        
        if self.is_growing and currentTime - self.last_growing >= LIGHTNING_GROWTH_DELAY: 
            
            self.last_growing = currentTime
            last_x = self.segments[-1][0]

            new_segments = []
            for segment in self.segments:
                x, y, _ = segment
                
                if x != last_x: continue
                N_branches  = random.randint(1, LIGHTNING_MAX_BRANCHES)
                
                for _ in range(N_branches):
                    if random.random() > LIGHTNING_BRANCH_CHANCES: continue
                    self.gen(x, y, -3, 3, new_segments)
            
            if len(new_segments) == 0 and self.height < self.target_len:
                for x, y, _ in self.segments:
                    if x != last_x: continue
                    self.gen(x, y, -1, 1, new_segments)
            
            if len(new_segments) == 0 or self.segments[-1][0] >= self.max_x:
                self.is_growing = False;
                        
            for x in new_segments:
                self.segments.append(x)
                
        return currentTime - self.segments[-1][2] <= LIGHTNING_LIFESPAN 
        
    def Draw(self, stdscr: curses.window):
        currentTime = time.time()
        
        for x, y, creationTime in self.segments:
            age = currentTime - creationTime
            if age >= LIGHTNING_LIFESPAN: continue
            
            norm_age = age / LIGHTNING_LIFESPAN
            if norm_age <= 6/10:
                char = '#'
            elif norm_age <= 9/10:
                char = '*'
            else:
                char = '+'
            
            try:
                attr = curses.A_BOLD | curses.color_pair(LIGHTNING_PAIR_COLOR);
                stdscr.addstr(x, y, char, attr)
            except curses.error:
                pass
        
        
        
def Setup_color(rainColor = 'cyan', lightningColor = 'yellow'):
    curses.start_color()
    
    bg = curses.COLOR_BLACK
    
    rain_fg = CURSES_COLOR_MAP.get(rainColor.lower(), curses.COLOR_CYAN)
    curses.init_pair(RAIN_PAIR_COLOR, rain_fg, bg)
    
    lightning_fg = CURSES_COLOR_MAP.get(lightningColor.lower(), curses.COLOR_YELLOW)
    curses.init_pair(LIGHTNING_PAIR_COLOR, lightning_fg, bg)


def DrawRain(stdscr:curses.window, raindrops):
    rows, cols = stdscr.getmaxyx()
    for rdrop in raindrops:
        try:
            attr = curses.color_pair(RAIN_PAIR_COLOR);
            if(rdrop.speed < 0.8): attr |= curses.A_DIM
            
            stdscr.addstr(int(rdrop.x), rdrop.y, rdrop.char, attr)
        except curses.error:
            pass        

def DrawLightningBolts(stdscr:curses.window, activeBolts):
    for bolts in activeBolts:
        bolts.Draw(stdscr)

def SimulateRain(stdscr: curses.window, rainColor = 'cyan', lightningColor = 'yellow', thunder = False):
    curses.curs_set(0) 
    stdscr.nodelay(True) 
    stdscr.timeout(1)
    
    Setup_color(rainColor, lightningColor)
    
    raindrops = []
    rows, cols = stdscr.getmaxyx()
    minRainSpeed = 0.3
    maxRainSpeed = 1.0 if thunder else 0.6
    
    max_active_bolts = 3
    activeBolts = []
    
    UPDATE_INTERVAL = 0.015
    last_update_time = time.time()
    
    while True:
        
        # --- Framerate ---
        if(time.time() - last_update_time < UPDATE_INTERVAL):
            delta = time.time() - last_update_time;
            time.sleep(UPDATE_INTERVAL - delta)
        
        last_update_time = time.time()
        
        # --- LIGHTNING ---
        
        if len(activeBolts) < max_active_bolts and random.random() <= LIGHTNING_CHANCES:
            x = random.randint(0, rows // 3)
            y = random.randint(cols // 5, 4 * cols // 5)
            activeBolts.append(Lightningbolts(x, y, rows, cols))
            
        notdeadbolts = []
        for bolts in activeBolts:
            if bolts.update():
                notdeadbolts.append(bolts)
        
        activeBolts = notdeadbolts  
        
        # --- RAINS ---
        generation_rate = 0.5 if thunder else 0.3
        next_raindrops = []
        
        if(random.random() < generation_rate):
            cnt = random.randint(1, max(1, cols//8 if thunder else cols//15))
            for _ in range(cnt):
                x = 0
                y = random.randint(0, cols - 1)
                speed = random.uniform(minRainSpeed, maxRainSpeed)
                char = random.choice(RAIN_CHARS)
                
                next_raindrops.append(Raindrop(x, y, speed, char))
        
        for rdrop in raindrops:
            if int(rdrop.x + rdrop.speed) >= rows:
                continue
            rdrop.x += rdrop.speed
            next_raindrops.append(rdrop)
            
        raindrops = next_raindrops
        
        #--- Draws ---
        stdscr.clear()
        
        DrawRain(stdscr, raindrops)
        
        if(thunder): DrawLightningBolts(stdscr, activeBolts)
        
        stdscr.noutrefresh()
        curses.doupdate()


parser = argparse.ArgumentParser()

parser.add_argument(
    '--rc',
    type = str,
    default = 'cyan',
)

parser.add_argument(
    '--lc',
    type = str,
    default = 'yellow',
)

parser.add_argument(
    '--thunder',
    action='store_true'
)

arg = parser.parse_args()

try:
    curses.wrapper(SimulateRain, arg.rc, arg.lc, arg.thunder)
except KeyboardInterrupt:
    print("bye!")
    
    
    