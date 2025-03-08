import pygame
import random
import sys
from heapq import heappush, heappop

pygame.init()

# Constants
MAZE_SIZE = 51
SCREEN_SIZE = 750
WALL_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
PATH_COLOR = (200, 200, 200)
START_COLOR = (0, 255, 0)
END_COLOR = (255, 0, 0)

class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.walls = {'top': True, 'right': True, 'bottom': True, 'left': True}
        self.is_main_path = False
        self.visited = False

def create_main_path(grid):
    rows = len(grid)
    cols = len(grid[0])
    path = []
    
    current = (1, 1)
    end = (rows-2, cols-2)
    grid[current[0]][current[1]].is_main_path = True
    path.append(current)
    
    while current != end:
        neighbors = []
        # prefer moving towards exit
        if current[0] < end[0]:
            neighbors.append((1, 0))
        if current[1] < end[1]:
            neighbors.append((0, 1))
        if not neighbors:
            neighbors = [(1, 0), (0, 1)]
            
        # randomly choose direction with bias
        dx, dy = random.choice(neighbors)
        next_cell = (current[0] + dx, current[1] + dy)
        
        if 0 < next_cell[0] < rows-1 and 0 < next_cell[1] < cols-1:
            # remove walls between current and next cell
            curr_cell = grid[current[0]][current[1]]
            next_cell_obj = grid[next_cell[0]][next_cell[1]]
            
            if dx == 1:  # moving down
                curr_cell.walls['bottom'] = False
                next_cell_obj.walls['top'] = False
            elif dx == -1:  # moving up
                curr_cell.walls['top'] = False
                next_cell_obj.walls['bottom'] = False
            elif dy == 1:  # moving right
                curr_cell.walls['right'] = False
                next_cell_obj.walls['left'] = False
            elif dy == -1:  # moving left
                curr_cell.walls['left'] = False
                next_cell_obj.walls['right'] = False
                
            current = next_cell
            grid[current[0]][current[1]].is_main_path = True
            path.append(current)
    
    return path

def generate_maze(rows, cols):
    grid = [[Cell(r, c) for c in range(cols)] for r in range(rows)]
    
    # create main path with connected walls
    main_path = create_main_path(grid)
    
    # initialise priority queue
    heap = []
    start_r, start_c = main_path[0]
    grid[start_r][start_c].visited = True
    
    # add initial frontiers
    for r, c in main_path:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if not grid[nr][nc].visited:
                    weight = 1 if grid[nr][nc].is_main_path else random.randint(5, 15)
                    heappush(heap, (weight, (r, c), (nr, nc)))
    
    # process frontiers
    while heap:
        weight, (from_r, from_c), (to_r, to_c) = heappop(heap)
        to_cell = grid[to_r][to_c]
        
        if to_cell.visited:
            continue
            
        # remove walls between cells
        if from_r == to_r:
            if from_c < to_c:  # right
                grid[from_r][from_c].walls['right'] = False
                to_cell.walls['left'] = False
            else:  # left
                grid[from_r][from_c].walls['left'] = False
                to_cell.walls['right'] = False
        else:
            if from_r < to_r:  # down
                grid[from_r][from_c].walls['bottom'] = False
                to_cell.walls['top'] = False
            else:  # up
                grid[from_r][from_c].walls['top'] = False
                to_cell.walls['bottom'] = False
        
        to_cell.visited = True
        
        # add new frontiers
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = to_r + dr, to_c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if not grid[nr][nc].visited:
                    new_weight = random.randint(5, 20)
                    heappush(heap, (new_weight, (to_r, to_c), (nr, nc)))
    
    # ensure openings
    grid[1][1].walls['top'] = False
    grid[rows-2][cols-2].walls['bottom'] = False
    
    return grid

def draw_maze(screen, grid, cell_size):
    screen.fill(BACKGROUND_COLOR)
    rows = len(grid)
    cols = len(grid[0])
    
    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            x = c * cell_size
            y = r * cell_size
            
            # draw cell background
            if cell.is_main_path:
                pygame.draw.rect(screen, PATH_COLOR, (x, y, cell_size, cell_size))
            
            # draw walls
            if cell.walls['top']:
                pygame.draw.line(screen, WALL_COLOR, (x, y), (x+cell_size, y), 2)
            if cell.walls['right']:
                pygame.draw.line(screen, WALL_COLOR, 
                               (x+cell_size, y), (x+cell_size, y+cell_size), 2)
            if cell.walls['bottom']:
                pygame.draw.line(screen, WALL_COLOR, 
                               (x, y+cell_size), (x+cell_size, y+cell_size), 2)
            if cell.walls['left']:
                pygame.draw.line(screen, WALL_COLOR, (x, y), (x, y+cell_size), 2)
    
    # draw start/end markers
    marker_size = cell_size // 3
    pygame.draw.rect(screen, START_COLOR, 
                    (cell_size//2 - marker_size//2, 
                     cell_size//2 - marker_size//2,
                     marker_size, marker_size))
    pygame.draw.rect(screen, END_COLOR, 
                    ((cols-1)*cell_size + cell_size//2 - marker_size//2,
                     (rows-1)*cell_size + cell_size//2 - marker_size//2,
                     marker_size, marker_size))

screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption("Maze with Guaranteed Path")
cell_size = SCREEN_SIZE // MAZE_SIZE

maze = generate_maze(MAZE_SIZE, MAZE_SIZE)

# main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    draw_maze(screen, maze, cell_size)
    pygame.display.flip()

pygame.quit()
sys.exit()
