"""
Weighted Randomised Kruskal Maze Generation

This code uses Pygame to generate a maze using a weighted randomised version of
Kruskal's algorithm. It uses a union-find data structure to keep track of connected
cells and progressively removes walls to form the maze.
"""
import pygame
import random
import math

# =============================================================================
# Constants
# =============================================================================
RESOLUTION_CONTROL = 15          # resolution scaling
SPEED_CONTROL = 15               # controls the animation speed

# weight values for wall types (used for weighted random selection)
W_LOW = 1 
W_LOW_MED = 2
W_MED = 5
W_MED_HIGH = 10
W_HIGH = 15
W_MAX = 17

WHITE = (255, 255, 255)          # for drawing cells
BLACK = (0, 0, 0)                # for background and walls

# canvas dimensions in pixels
CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 700

# grid dimensions (number of cells) based on resolution 
GRID_WIDTH = math.floor(CANVAS_WIDTH * RESOLUTION_CONTROL / 100)
GRID_HEIGHT = math.floor(CANVAS_HEIGHT * RESOLUTION_CONTROL / 100)

# wall width in pixels calculated based on resolution
WALL_WIDTH = math.floor(100 / (RESOLUTION_CONTROL * 3))

# =============================================================================
# Global Variables for maze Generation
# =============================================================================
union_find = []            # list for union-find (disjoint set) structure
# pre-calculate weights for 9 wall types using a power function
weights = [math.pow(2.0, w * 0.5) for w in 
           [W_MAX, W_HIGH, W_MED, W_HIGH, W_MED_HIGH, W_LOW_MED, W_MED, W_LOW_MED, W_LOW]]
# wall queues: one list per wall type (0-8)
wall_queues = [[] for _ in range(9)]
walls_by_index = []        # list holding wall objects (or None) by calculated index

# start and finish positions (x-coordinate in the grid)
start_x = None
finish_x = None

# timing and state control variables
progress_time = 0          # timer to pace the maze-generation steps
current_state = None       # pointer to the current state function (used to step through the algorithm)

# =============================================================================
# Utility Functions
# =============================================================================
def rand_int(n):
    """
    Return a random integer in the range [0, n).
    """
    return random.randrange(n)

def push_rand(arr, item):
    """
    Insert an item at a random position in the list.
    """
    arr.insert(rand_int(len(arr) + 1), item)

# =============================================================================
# Union-Find (Disjoint Set) Functions
# =============================================================================
def ufind(cell):
    """
    Find the root of a given cell using path compression in the union-find structure.
    """
    global union_find
    # ensure the union_find list is large enough to include the current cell.
    while len(union_find) <= cell:
        union_find.append(-1)
    src = cell
    # traverse to find the root.
    while union_find[cell] >= 0:
        cell = union_find[cell]
    # path compression: update intermediate nodes to point directly to the root.
    while union_find[src] >= 0 and union_find[src] != cell:
        temp = union_find[src]
        union_find[src] = cell
        src = temp
    return cell

def union(cell_i, cell_j):
    """
    Merge the sets containing cell_i and cell_j using union by sise.
    """
    global union_find
    i = ufind(cell_i)
    j = ufind(cell_j)
    if i != j:
        # attach the smaller tree to the larger tree.
        if union_find[i] >= union_find[j]:
            union_find[j] += union_find[i]
            union_find[i] = j
        else:
            union_find[i] += union_find[j]
            union_find[j] = i
        return True
    return False

# =============================================================================
# Wall and Neighbour Functions
# =============================================================================
def get_wall(x, y, is_horizontal):
    """
    Retrieve a wall based on its grid coordinates and orientation.

    Each cell has two associated walls (horizontal and vertical). The index is
    calculated to retrieve the correct wall from the global walls_by_index list.
    """
    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
        index = (y * GRID_WIDTH + x) * 2 + (0 if is_horizontal else 1)
        return walls_by_index[index]
    return None

def get_neighbour(wall, n):
    """
    Return the neighbouring wall based on the current wall and neighbour index.
    """
    HORIZONTAL_OFFSETS = [(0, -1, False), (0, -1, True), (1, -1, False),
                          (0, 0, False), (0, 1, True), (1, 0, False)]
    VERTICAL_OFFSETS   = [(-1, 0, True), (-1, 0, False), (-1, 1, True),
                          (0, 0, True), (1, 0, False), (0, 1, True)]

    offsets = HORIZONTAL_OFFSETS if wall['dr'] else VERTICAL_OFFSETS
    try:
        dx, dy, is_horiz = offsets[n]
    except IndexError:
        return None
    return get_wall(wall['x'] + dx, wall['y'] + dy, is_horiz)

def get_wall_end_type(w1, w2, w3):
    """
    Determine the "end type" of a wall based on the status (coloured or not) of three neighbours.

    The function returns:
        2 if at least two of the provided walls are removed (coloured),
        1 if at least one is removed,
        0 if none are removed.
    """
    if w1 and w1['clr']:
        if w3 and w3['clr']:
            return 2
        if w2 and w2['clr']:
            return 2
        return 1
    if w3 and w3['clr']:
        if w2 and w2['clr']:
            return 2
        return 1
    return 0

def update_wall_type(wall):
    """
    Update the wall type of a given wall based on its neighbours.

    The wall type is computed as: t1 * 3 + t2, where:
        t1: End type from neighbours at indices 0, 1, 2.
        t2: End type from neighbours at indices 3, 4, 5.

    If the new type is higher than the current type, the wall is updated and
    reinserted into the corresponding wall queue.
    """
    t1 = get_wall_end_type(get_neighbour(wall, 0), get_neighbour(wall, 1), get_neighbour(wall, 2))
    t2 = get_wall_end_type(get_neighbour(wall, 3), get_neighbour(wall, 4), get_neighbour(wall, 5))
    new_type = t1 * 3 + t2
    if new_type > wall['typ']:
        wall['typ'] = new_type
        push_rand(wall_queues[new_type], wall)

# =============================================================================
# Drawing Functions
# =============================================================================
def fill_cell(x, y, wx, wy, colour, screen):
    """
    Fill a rectangular area on the screen representing a cell or wall.

    This function calculates the pixel boundaries of the cell (or wall) based on
    its grid coordinates and wall offsets, then draws a filled rectangle.
    """
    # adjust wall offsets
    wx = wx + 1
    wy = wy + 1
    x = x + (wx >> 1)
    wx = wx & 1
    y = y + (wy >> 1)
    wy = wy & 1

    # calculate x-coordinate boundaries
    if wx:
        ex = math.floor((x + 1) * (CANVAS_WIDTH - WALL_WIDTH) / GRID_WIDTH)
        x_coord = math.floor(x * (CANVAS_WIDTH - WALL_WIDTH) / GRID_WIDTH) + WALL_WIDTH
    else:
        x_coord = math.floor(x * (CANVAS_WIDTH - WALL_WIDTH) / GRID_WIDTH)
        ex = x_coord + WALL_WIDTH

    # calculate y-coordinate boundaries
    if wy:
        ey = math.floor((y + 1) * (CANVAS_HEIGHT - WALL_WIDTH) / GRID_HEIGHT)
        y_coord = math.floor(y * (CANVAS_HEIGHT - WALL_WIDTH) / GRID_HEIGHT) + WALL_WIDTH
    else:
        y_coord = math.floor(y * (CANVAS_HEIGHT - WALL_WIDTH) / GRID_HEIGHT)
        ey = y_coord + WALL_WIDTH

    rect = pygame.Rect(x_coord, y_coord, ex - x_coord, ey - y_coord)
    pygame.draw.rect(screen, colour, rect)

def try_wall(wall, screen):
    """
    Attempt to remove a wall if it connects two previously disconnected cells.

    The wall is only removed (i.e. "coloured" white) if the union operation on the
    two adjacent cells is successful (meaning they were not already connected).
    Additionally, the function updates the wall types of the wall's neighbours.
    """
    if wall['clr']:
        return False

    # calculate cell indices for the cells adjacent to this wall.
    cell_index1 = wall['y'] * GRID_WIDTH + wall['x']
    cell_index2 = cell_index1 + (1 if wall['dr'] else GRID_WIDTH)

    # attempt to union the two cells; if already connected, do not remove the wall.
    if not union(cell_index1, cell_index2):
        return False

    # mark the wall as removed.
    wall['clr'] = True
    fill_cell(wall['x'], wall['y'], (1 if wall['dr'] else 0), (0 if wall['dr'] else 1), WHITE, screen)

    # update the wall types of adjacent neighbours.
    for i in range(6):
        neighbour = get_neighbour(wall, i)
        if neighbour:
            update_wall_type(neighbour)
    return True

# =============================================================================
# Maze Generation Step and Initialisation
# =============================================================================
def step(screen):
    """
    Execute a single step of the maze generation algorithm.

    The function selects a wall from the available wall queues using weighted
    random selection. If a wall is eligible, it attempts to remove it, thereby
    connecting two cells. The progress timer is updated accordingly.
    """
    global progress_time
    total_weight = sum(len(wall_queues[i]) * weights[i] for i in range(9))
    if total_weight <= 0:
        return False

    # determine which wall queue to select from based on weighted random choice.
    random_threshold = total_weight * random.random()
    for i in range(9):
        queue_weight = len(wall_queues[i]) * weights[i]
        if random_threshold < queue_weight:
            queue_index = i
            break
        random_threshold -= queue_weight
    else:
        queue_index = 0

    if not wall_queues[queue_index]:
        return True

    wall = wall_queues[queue_index].pop()
    if wall and wall['typ'] == queue_index and try_wall(wall, screen):
        progress_time += (20.0 - SPEED_CONTROL) * 250.0 / (GRID_WIDTH * GRID_HEIGHT)
    return True

def init(screen):
    """
    Initialise the maze by setting up the grid, walls, and union-find structure.

    This function resets all global data structures, selects random start and finish
    positions, draws the initial grid, and populates the wall queues.
    """
    global union_find, wall_queues, walls_by_index, start_x, finish_x, progress_time

    # reset global structures.
    union_find = []
    wall_queues = [[] for _ in range(9)]
    walls_by_index = []
    screen.fill(BLACK)
    
    # randomly determine start and finish positions.
    start_x = rand_int(GRID_WIDTH)
    finish_x = rand_int(GRID_WIDTH)
    
    # draw start (top row) and finish (bottom row) cells.
    fill_cell(start_x, 0, 0, -1, WHITE, screen)
    fill_cell(finish_x, GRID_HEIGHT - 1, 0, 1, WHITE, screen)
    
    # create cells and associated walls.
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            # draw the cell background.
            fill_cell(x, y, 0, 0, WHITE, screen)
            
            # create a horisontal wall (if not on the right boundary).
            if x < GRID_WIDTH - 1:
                wall = {'x': x, 'y': y, 'dr': True, 'typ': 0, 'clr': False}
                walls_by_index.append(wall)
                push_rand(wall_queues[0], wall)
            else:
                walls_by_index.append(None)
            
            # create a vertical wall (if not on the bottom boundary).
            if y < GRID_HEIGHT - 1:
                wall = {'x': x, 'y': y, 'dr': False, 'typ': 0, 'clr': False}
                walls_by_index.append(wall)
                push_rand(wall_queues[0], wall)
            else:
                walls_by_index.append(None)
    
    progress_time = pygame.time.get_ticks()

# =============================================================================
# Main Loop
# =============================================================================
"""
Main function to run the maze generation animation.

Initialises Pygame, sets up the display, and enters the main event loop
where maze generation steps are processed and drawn to the screen.
"""
pygame.init()

screen = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT))
pygame.display.set_caption("Weighted Randomised Kruskal maze Generation")
clock = pygame.time.Clock()

init(screen)
current_state = step

running = True
while running:
    # handle events (e.g., window close).
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = pygame.time.get_ticks()
    # process steps if it's time to update the maze.
    while progress_time < current_time and current_state is not None:
        result = current_state(screen)
        if not result:
            current_state = None
            break
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
