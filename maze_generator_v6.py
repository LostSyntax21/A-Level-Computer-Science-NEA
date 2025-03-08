import pygame
import random
import sys
from collections import defaultdict

pygame.init()

# Constants
MAZE_ROWS = 40
MAZE_COLS = 40
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
WALL_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
START_COLOR = (0, 255, 0)
END_COLOR = (255, 0, 0)
PATH_COLOR = (0, 0, 255)

class Cell:
    __slots__ = ['row', 'col', 'walls', 'visited']
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.walls = {'top': True, 'right': True, 'bottom': True, 'left': True}
        self.visited = False

class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}
        
    def find(self, cell):
        if self.parent[cell] != cell:
            self.parent[cell] = self.find(self.parent[cell])
        return self.parent[cell]
    
    def union(self, cell1, cell2):
        root1 = self.find(cell1)
        root2 = self.find(cell2)
        if root1 != root2:
            if self.rank[root1] > self.rank[root2]:
                self.parent[root2] = root1
            else:
                self.parent[root1] = root2
                if self.rank[root1] == self.rank[root2]:
                    self.rank[root2] += 1

def generate_maze(rows, cols):
    grid = [[Cell(r, c) for c in range(cols)] for r in range(rows)]
    uf = UnionFind()
    walls = []
    
    # initialise Union-Find
    for r in range(rows):
        for c in range(cols):
            uf.parent[(r, c)] = (r, c)
            uf.rank[(r, c)] = 0
            if r < rows - 1:
                walls.append(('v', r, c))
            if c < cols - 1:
                walls.append(('h', r, c))
    
    random.shuffle(walls)
    
    # process walls until start and end are connected
    start = (0, 0)
    end = (rows-1, cols-1)
    
    for wall in walls:
        if uf.find(start) == uf.find(end):
            break
            
        if wall[0] == 'v':
            r, c = wall[1], wall[2]
            cell1 = (r, c)
            cell2 = (r + 1, c)
        else:
            r, c = wall[1], wall[2]
            cell1 = (r, c)
            cell2 = (r, c + 1)
        
        if uf.find(cell1) != uf.find(cell2):
            uf.union(cell1, cell2)
            if wall[0] == 'v':
                grid[r][c].walls['bottom'] = False
                grid[r + 1][c].walls['top'] = False
            else:
                grid[r][c].walls['right'] = False
                grid[r][c + 1].walls['left'] = False

    # force connection if not already connected
    if uf.find(start) != uf.find(end):
        grid[-1][-1].walls['right'] = False
        grid[-2][-1].walls['bottom'] = False

    # ensure entry/exit paths
    grid[0][0].walls['top'] = False
    grid[-1][-1].walls['right'] = False
    
    return grid

def draw_maze(screen, grid, start_x, start_y, cell_size):
    screen.fill(BACKGROUND_COLOR)
    
    for row in grid:
        for cell in row:
            x = start_x + cell.col * cell_size
            y = start_y + cell.row * cell_size

            if cell.walls['top']:
                pygame.draw.line(screen, WALL_COLOR, (x, y), (x+cell_size, y), 2)
            if cell.walls['right']:
                pygame.draw.line(screen, WALL_COLOR, (x+cell_size, y), (x+cell_size, y+cell_size), 2)
            if cell.walls['bottom']:
                pygame.draw.line(screen, WALL_COLOR, (x, y+cell_size), (x+cell_size, y+cell_size), 2)
            if cell.walls['left']:
                pygame.draw.line(screen, WALL_COLOR, (x, y), (x, y+cell_size), 2)

    # draw start/end markers
    cs = cell_size
    pygame.draw.rect(screen, START_COLOR, (start_x + cs//4, start_y - cs//4, cs//2, cs//2))
    pygame.draw.rect(screen, END_COLOR, (start_x + (MAZE_COLS-1)*cs + cs//4, 
                                    start_y + (MAZE_ROWS-1)*cs + cs//4, 
                                    cs//2, cs//2))

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Kruskal's Maze Generator with Guaranteed Path")

cell_size = min(
    (SCREEN_WIDTH - 200) // MAZE_COLS,
    (SCREEN_HEIGHT - 100) // MAZE_ROWS
)
cell_size = max(cell_size, 8)

# right-align maze with padding
maze_width = MAZE_COLS * cell_size
maze_height = MAZE_ROWS * cell_size
start_x = SCREEN_WIDTH - maze_width - 20
start_y = (SCREEN_HEIGHT - maze_height) // 2

maze_grid = generate_maze(MAZE_ROWS, MAZE_COLS)

# main loop
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw_maze(screen, maze_grid, start_x, start_y, cell_size)
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
