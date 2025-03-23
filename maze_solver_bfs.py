"""
Weighted Randomised Kruskal Maze Generation with Animated Solution
"""
import pygame
import random
import math

# =============================================================================
# Constants
# =============================================================================
RESOLUTION_CONTROL = 15          # resolution scaling as a percentage
SPEED_CONTROL = 16               # controls the animation speed

# weight values for wall types (used for weighted random selection)
W_LOW = 1 
W_LOW_MED = 2
W_MED = 5
W_MED_HIGH = 10
W_HIGH = 15
W_MAX = 17

WHITE = (255, 255, 255)          # for drawing cells
BLACK = (0, 0, 0)                # for background and walls
PATH_COLOUR = (46, 204, 0)  # colour for the solution path

# canvas dimensions in pixels
CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 700

# grid dimensions (number of cells) based on resolution 
GRID_WIDTH = math.floor(CANVAS_WIDTH * RESOLUTION_CONTROL / 100)
GRID_HEIGHT = math.floor(CANVAS_HEIGHT * RESOLUTION_CONTROL / 100)

# wall width in pixels calculated based on resolution
WALL_WIDTH = math.floor(100 / (RESOLUTION_CONTROL * 3))

# =============================================================================
# Global Variables for Maze Generation
# =============================================================================
union_find = []  # list for union-find (disjoint set) structure
# pre-calculate weights for 9 wall types using a power function
weights = [math.pow(2.0, w * 0.5) for w in 
           [W_MAX, W_HIGH, W_MED, W_HIGH, W_MED_HIGH, W_LOW_MED, W_MED, W_LOW_MED, W_LOW]]
wall_queues = [[] for _ in range(9)]
walls_by_index = []  # list holding wall objects (or None) by calculated index

start_x = None   # start cell (top row)
finish_x = None  # finish cell (bottom row)

progress_time = 0   # timer to pace the maze-generation steps

# =============================================================================
# Global Variables for Solution Animation
# =============================================================================
solution_state = None  # 2D list tracking the "depth" a cell was reached
solution_level = None  # current frontier of cells (list of (x, y))
solution_depth = 0
solution_colours = [
    (255, 255, 208), (255, 255, 176), (255, 255, 144),
    (255, 255, 112), (255, 255, 80), (255, 255, 48), (255, 255, 16)
]

phase = "generation"

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
    # ensure the union_find list is large enough to include the current cell
    while len(union_find) <= cell:
        union_find.append(-1)
    src = cell
    # traverse to find the root
    while union_find[cell] >= 0:
        cell = union_find[cell]
    # path compression: update intermediate nodes to point directly to the root
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
        # attach the smaller tree to the larger tree
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

    # calculate cell indices for the cells adjacent to this wall
    cell_index1 = wall['y'] * GRID_WIDTH + wall['x']
    cell_index2 = cell_index1 + (1 if wall['dr'] else GRID_WIDTH)

    # attempt to union the two cells; if already connected, do not remove the wall
    if not union(cell_index1, cell_index2):
        return False

    # mark the wall as removed
    wall['clr'] = True
    fill_cell(wall['x'], wall['y'], (1 if wall['dr'] else 0), (0 if wall['dr'] else 1), WHITE, screen)

    # update the wall types of adjacent neighbours
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

    # determine which wall queue to select from based on weighted random choice
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
    
    # randomly determine start and finish positions
    start_x = rand_int(GRID_WIDTH)
    finish_x = rand_int(GRID_WIDTH)
    
    # draw start (top row) and finish (bottom row) cells
    fill_cell(start_x, 0, 0, -1, WHITE, screen)
    fill_cell(finish_x, GRID_HEIGHT - 1, 0, 1, WHITE, screen)
    
    # create cells and associated walls
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            # draw the cell background
            fill_cell(x, y, 0, 0, WHITE, screen)
            
            # create a horizontal wall (if not on the right boundary)
            if x < GRID_WIDTH - 1:
                wall = {'x': x, 'y': y, 'dr': True, 'typ': 0, 'clr': False}
                walls_by_index.append(wall)
                push_rand(wall_queues[0], wall)
            else:
                walls_by_index.append(None)
            
            # create a vertical wall (if not on the bottom boundary)
            if y < GRID_HEIGHT - 1:
                wall = {'x': x, 'y': y, 'dr': False, 'typ': 0, 'clr': False}
                walls_by_index.append(wall)
                push_rand(wall_queues[0], wall)
            else:
                walls_by_index.append(None)
    
    progress_time = pygame.time.get_ticks()

# =============================================================================
# Solution Functions
# =============================================================================
def init_solution(screen):
    """
    Initialise the solution drawing process for the generated maze.

    This function creates a 2D list (solution_state) to track the depth at which
    each cell is reached, sets the starting frontier for the solution search at the
    maze start cell, and draws that initial cell in the designated solution path colour.
    It also resets the solution depth counter and synchronises the progress timer.
    """
    global solution_state, solution_level, solution_depth, progress_time
    # create a 2D array to record the "depth" (or distance) each cell is reached
    solution_state = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    
    # set the starting frontier of the solution with the starting cell
    solution_level = [(start_x, 0)]
    
    # mark the start cell as reached with a depth value of 1
    solution_state[0][start_x] = 1
    
    # draw the start cell using the solution path colour
    fill_cell(start_x, 0, 0, 0, PATH_COLOUR, screen)
    
    # initialise the solution depth counter
    solution_depth = 1
    
    # set the progress timer to the current time
    progress_time = pygame.time.get_ticks()

def solution_step(screen):
    """
    Execute a single step of the solution path animation.

    This function expands the current frontier of solution cells by exploring
    adjacent cells that are reachable (i.e., where the wall has been removed).
    It updates the solution_state with the depth value for each new cell and draws
    each cell with a colour based on the current solution depth. Once the finish cell
    is reached, the function backtracks from finish to start to highlight the correct
    solution path.

    Returns:
        True if further animation steps are required, or False if the solution
        animation is complete.
    """
    global solution_state, solution_level, solution_depth, progress_time
    # increment the solution depth as we expand the search frontier
    solution_depth += 1
    
    # select a drawing colour based on the current solution depth
    clr = solution_colours[solution_depth % len(solution_colours)]
    
    # store the current frontier and prepare a new list for the next frontier
    old_level = solution_level
    solution_level = []
    
    # define relative wall index differences for neighbour lookup
    walldiff = [-GRID_WIDTH * 2 + 1, 0, -2, 1]
    
    # process each cell in the current frontier
    for (cx, cy) in old_level:
        # calculate the base wall index for the current cell
        wallr = (cy * GRID_WIDTH + cx) * 2
        # check all four potential directions (neighbours)
        for n in range(4):
            # compute the neighbour's grid coordinates
            ty = cy - 1 + (n - 1 if n >= 2 else n)
            tx = cx + (n & 1) - ((n >> 1) & 1)
            # ensure the neighbour is within bounds and not yet visited
            if 0 <= tx < GRID_WIDTH and 0 <= ty < GRID_HEIGHT and solution_state[ty][tx] == 0:
                wall_index = wallr + walldiff[n]
                # verify that the corresponding wall exists and has been removed
                if (0 <= wall_index < len(walls_by_index) and 
                    walls_by_index[wall_index] is not None and 
                    walls_by_index[wall_index]['clr']):
                    # add the neighbour to the new frontier
                    solution_level.append((tx, ty))
                    # mark the neighbour with the current depth
                    solution_state[ty][tx] = solution_depth
                    # draw the neighbour cell with the selected colour
                    fill_cell(tx, ty, 0, 0, clr, screen)
    
    # update the progress timer based on the number of new frontier cells
    progress_time += int((len(solution_level) + 5) * (20.0 - SPEED_CONTROL) * 250.0 / (GRID_WIDTH * GRID_HEIGHT))
    
    # check if the finish cell (bottom row at finish_x) has been reached
    if solution_state[GRID_HEIGHT - 1][finish_x] == 0:
        # if not reached and there are still frontier cells, continue animation
        if solution_level:
            return True
        else:
            # no frontier cells remain and finish cell is not reached
            return False

    # backtracking from finish to start to trace the solution path
    x, y = finish_x, GRID_HEIGHT - 1
    while True:
        # draw the current cell in the final solution path colour
        fill_cell(x, y, 0, 0, PATH_COLOUR, screen)
        d = solution_state[y][x]
        wallr = (y * GRID_WIDTH + x) * 2
        found = False
        # search for a neighbouring cell with a lower depth (closer to the start)
        for n in range(4):
            ty = y - 1 + (n - 1 if n >= 2 else n)
            tx = x + (n & 1) - ((n >> 1) & 1)
            if 0 <= tx < GRID_WIDTH and 0 <= ty < GRID_HEIGHT and solution_state[ty][tx] != 0 and solution_state[ty][tx] < d:
                wall_index = wallr + walldiff[n]
                if (0 <= wall_index < len(walls_by_index) and 
                    walls_by_index[wall_index] is not None and 
                    walls_by_index[wall_index]['clr']):
                    # move to the neighbour cell with a lower depth
                    x, y = tx, ty
                    found = True
                    break
        # if no neighbour with a lower depth is found, backtracking is complete
        if not found:
            break

    # return False to indicate the solution animation is complete
    return False

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
pygame.display.set_caption("Weighted Randomised Kruskal Maze Generation with Solution")
clock = pygame.time.Clock()

init(screen)
# set current_state to the maze generation function
current_state = step
phase = "generation"

running = True
while running:
    # handle events (e.g., window close)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = pygame.time.get_ticks()
    # process steps if it's time to update the maze.
    while progress_time < current_time and current_state is not None:
        finished = current_state(screen)
        if not finished:
            # if the function signals completion, set current_state to None
            current_state = None
            break

    # transition to solution animation after maze generation is complete
    if phase == "generation" and current_state is None:
        phase = "solution"
        init_solution(screen)
        current_state = solution_step

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
