import pygame
import random
import sys

pygame.init()

# Constants
MAZE_ROWS = 30
MAZE_COLS = 30
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
    stack = []
    current = grid[0][0]
    current.visited = True
    stack.append(current)

    while stack:
        current = stack[-1]
        neighbors = []

        # check neighbors in all directions
        if current.row > 0 and not grid[current.row-1][current.col].visited:
            neighbors.append(grid[current.row-1][current.col])
        if current.col < cols-1 and not grid[current.row][current.col+1].visited:
            neighbors.append(grid[current.row][current.col+1])
        if current.row < rows-1 and not grid[current.row+1][current.col].visited:
            neighbors.append(grid[current.row+1][current.col])
        if current.col > 0 and not grid[current.row][current.col-1].visited:
            neighbors.append(grid[current.row][current.col-1])

        if neighbors:
            next_cell = random.choice(neighbors)
            # remove walls between current and next cell
            if next_cell.row == current.row - 1:
                current.walls['top'] = False
                next_cell.walls['bottom'] = False
            elif next_cell.row == current.row + 1:
                current.walls['bottom'] = False
                next_cell.walls['top'] = False
            elif next_cell.col == current.col - 1:
                current.walls['left'] = False
                next_cell.walls['right'] = False
            elif next_cell.col == current.col + 1:
                current.walls['right'] = False
                next_cell.walls['left'] = False
            
            next_cell.visited = True
            stack.append(next_cell)
        else:
            stack.pop()

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
