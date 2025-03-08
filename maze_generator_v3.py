import pygame
import random
import sys

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

class Cell:
    __slots__ = ['row', 'col', 'walls', 'visited']
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.walls = {'top': True, 'right': True, 'bottom': True, 'left': True}
        self.visited = False

def generate_maze(rows, cols):
    grid = [[Cell(r, c) for c in range(cols)] for r in range(rows)]
    walls = []
    
    # choose initial cell (0,0)
    start_cell = grid[0][0]
    start_cell.visited = True
    
    # add all possible walls of the initial cell to the walls list
    for direction in ['top', 'right', 'bottom', 'left']:
        walls.append( (start_cell, direction) )
    
    while walls:
        # randomly select a wall from the walls list
        index = random.randint(0, len(walls) - 1)
        current_wall = walls[index]
        # remove the wall from the list to avoid processing again
        del walls[index]
        
        current_cell, direction = current_wall
        
        # calculate neighbor's position based on direction
        if direction == 'top':
            neighbor_row = current_cell.row - 1
            neighbor_col = current_cell.col
        elif direction == 'right':
            neighbor_row = current_cell.row
            neighbor_col = current_cell.col + 1
        elif direction == 'bottom':
            neighbor_row = current_cell.row + 1
            neighbor_col = current_cell.col
        elif direction == 'left':
            neighbor_row = current_cell.row
            neighbor_col = current_cell.col - 1
        else:
            continue
        
        # check if neighbor is within grid bounds
        if neighbor_row < 0 or neighbor_row >= rows or neighbor_col < 0 or neighbor_col >= cols:
            continue
        
        neighbor_cell = grid[neighbor_row][neighbor_col]
        
        # check if the neighbor is not visited
        if not neighbor_cell.visited:
            # remove the walls between current_cell and neighbor_cell
            if direction == 'top':
                current_cell.walls['top'] = False
                neighbor_cell.walls['bottom'] = False
            elif direction == 'right':
                current_cell.walls['right'] = False
                neighbor_cell.walls['left'] = False
            elif direction == 'bottom':
                current_cell.walls['bottom'] = False
                neighbor_cell.walls['top'] = False
            elif direction == 'left':
                current_cell.walls['left'] = False
                neighbor_cell.walls['right'] = False
            
            # mark the neighbor as visited
            neighbor_cell.visited = True
            
            # add all walls of the neighbor to the walls list
            for dir in ['top', 'right', 'bottom', 'left']:
                walls.append( (neighbor_cell, dir) )
    
    # create entry and exit
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
pygame.display.set_caption("Perfect Maze Generator")

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
