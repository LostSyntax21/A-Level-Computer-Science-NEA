import pygame
import random

pygame.init()

# Constants
MAZE_ROWS = 30
MAZE_COLS = 30
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
WALL_THICKNESS = 1

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

class Cell:
    def __init__(self, i, j):
        self.i = i
        self.j = j
        self.walls = {'top': True, 'right': True, 'bottom': True, 'left': True}
        self.visited = False

    def get_unvisited_neighbors(self, grid):
        neighbors = []
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0

        # check all four directions
        directions = [
            (self.i-1, self.j),   # top
            (self.i, self.j+1),   # right
            (self.i+1, self.j),   # bottom
            (self.i, self.j-1)    # left
        ]

        for i, j in directions:
            if 0 <= i < rows and 0 <= j < cols and not grid[i][j].visited:
                neighbors.append(grid[i][j])

        return neighbors

    def draw(self, screen, start_x, start_y, cell_size):
        x = start_x + self.j * cell_size
        y = start_y + self.i * cell_size

        if self.walls['top']:
            pygame.draw.line(screen, BLACK, (x, y), (x + cell_size, y), WALL_THICKNESS)
        if self.walls['right']:
            pygame.draw.line(screen, BLACK, (x + cell_size, y), (x + cell_size, y + cell_size), WALL_THICKNESS)
        if self.walls['bottom']:
            pygame.draw.line(screen, BLACK, (x + cell_size, y + cell_size), (x, y + cell_size), WALL_THICKNESS)
        if self.walls['left']:
            pygame.draw.line(screen, BLACK, (x, y + cell_size), (x, y), WALL_THICKNESS)

def remove_walls(current, next_cell):
    di = next_cell.i - current.i
    dj = next_cell.j - current.j

    if di == -1:  # top
        current.walls['top'] = False
        next_cell.walls['bottom'] = False
    elif di == 1:  # bottom
        current.walls['bottom'] = False
        next_cell.walls['top'] = False
    elif dj == 1:  # right
        current.walls['right'] = False
        next_cell.walls['left'] = False
    elif dj == -1:  # left
        current.walls['left'] = False
        next_cell.walls['right'] = False

def generate_maze(rows, cols):
    grid = [[Cell(i, j) for j in range(cols)] for i in range(rows)]
    stack = []
    current = grid[0][0]
    current.visited = True
    stack.append(current)

    while stack:
        current = stack[-1]
        neighbors = current.get_unvisited_neighbors(grid)
        
        if neighbors:
            # introduce more randomness by shuffling neighbors
            random.shuffle(neighbors)
            next_cell = neighbors[0]
            remove_walls(current, next_cell)
            next_cell.visited = True
            stack.append(next_cell)
        else:
            # occasionally backtrack randomly to create dead-ends
            if random.random() < 0.2 and len(stack) > 1:
                stack.pop(random.randint(0, len(stack)-2))
            else:
                stack.pop()

    # create entry and exit
    grid[0][0].walls['top'] = False
    grid[-1][-1].walls['bottom'] = False

    return grid

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Improved Maze Generator")

# calculate cell size with right-side placement
cell_size = min(
    (SCREEN_WIDTH - 200) // MAZE_COLS,  # reserve space on left
    SCREEN_HEIGHT // MAZE_ROWS
)

# right-aligned maze position
maze_width = MAZE_COLS * cell_size
maze_height = MAZE_ROWS * cell_size
start_x = SCREEN_WIDTH - maze_width - 20  # 20px
start_y = (SCREEN_HEIGHT - maze_height) // 2

grid = generate_maze(MAZE_ROWS, MAZE_COLS)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)
    
    # draw maze
    for row in grid:
        for cell in row:
            cell.draw(screen, start_x, start_y, cell_size)
    
    # draw entry/exit markers
    entry_size = cell_size // 4
    pygame.draw.rect(screen, GREEN, 
                    (start_x + entry_size, 
                     start_y - entry_size, 
                     entry_size, entry_size))
    exit_size = cell_size // 4
    pygame.draw.rect(screen, RED, 
                    (start_x + (MAZE_COLS-1)*cell_size + exit_size, 
                     start_y + MAZE_ROWS*cell_size, 
                     exit_size, exit_size))

    pygame.display.flip()

pygame.quit()
