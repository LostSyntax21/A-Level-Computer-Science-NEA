import pygame
import random
import math

# ---------------------------
# Constants
# ---------------------------
rescontrol = 15
speedctrl = 14
PV11 = 1
PV12 = 2
PV13 = 5
PV22 = 10
PV23 = 15
PV33 = 17
PATHCOLOR = (46, 204, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# canvas dimensions
cwid = 1200
chei = 700

# grid dimensions and wall width
wid = math.floor(cwid * rescontrol / 100)
hei = math.floor(chei * rescontrol / 100)
wallwid = math.floor(100 / (rescontrol * 3))

ufarray = []            # union-find array
weights = [math.pow(2.0, w * 0.5) for w in [PV33, PV23, PV13, PV23, PV22, PV12, PV13, PV12, PV11]]
wallqs = [[] for _ in range(9)]  # 9 queues for walls
wallsbynum = []                 # list to hold wall objects

# start and finish x positions
startx = None
finishx = None

# timing and state (for animations)
doneTo = 0
state = None

# ---------------------------
# Helper Functions
# ---------------------------
def randInt(n):
    return random.randrange(n)

def pushrand(arr, item):
    if len(arr) < 1:
        arr.append(item)
        return
    i = randInt(len(arr) + 1)
    if i >= len(arr):
        arr.append(item)
    else:
        arr.append(arr[i])
        arr[i] = item
'''
def pushrand(arr, item):
    arr.insert(random.randint(0, len(arr)), item)
'''

# ---------------------------
# Union-Find Functions
# ---------------------------
def ufind(cell):
    global ufarray
    # extend the ufarray as needed
    while len(ufarray) <= cell:
        ufarray.append(-1)
    src = cell
    while ufarray[cell] >= 0:
        cell = ufarray[cell]
    # path compression
    while ufarray[src] >= 0 and ufarray[src] != cell:
        temp = ufarray[src]
        ufarray[src] = cell
        src = temp
    return cell

def union(celli, cellj):
    global ufarray
    i = ufind(celli)
    j = ufind(cellj)
    if i != j:
        if ufarray[i] >= ufarray[j]:
            ufarray[j] += ufarray[i]
            ufarray[i] = j
        else:
            ufarray[i] += ufarray[j]
            ufarray[j] = i
        return True
    return False

# ---------------------------
# Wall and Neighbour Functions
# ---------------------------
def getWall(x, y, dr):
    if 0 <= x < wid and 0 <= y < hei:
        index = (y * wid + x) * 2 + (0 if dr else 1)
        return wallsbynum[index]
    return None

def getNeighbour(wall, n):
    offsets = {
        True: [  # if wall['dr'] is True
            (-1, 0, False), (-1, 0, True), (0, -1, False),
            (0, 0, False), (0, 1, True), (1, 0, False)
        ],
        False: [  # if wall['dr'] is False
            (-1, 0, True), (-1, 0, False), (-1, 1, True),
            (0, 0, True), (1, 0, False), (0, 1, True)
        ]
    }

    dx, dy, dr = offsets[wall['dr']][n]
    return getWall(wall['x'] + dx, wall['y'] + dy, dr)


def getWallEndType(w1, w2, w3):
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

def updateWallType(wall):
    t1 = getWallEndType(getNeighbour(wall, 0), getNeighbour(wall, 1), getNeighbour(wall, 2))
    t2 = getWallEndType(getNeighbour(wall, 3), getNeighbour(wall, 4), getNeighbour(wall, 5))
    typ = t1 * 3 + t2
    if typ > wall['typ']:
        wall['typ'] = typ
        pushrand(wallqs[typ], wall)

# ---------------------------
# Drawing Function
# ---------------------------
def fill(x, y, wx, wy, clr, screen):
    wx = wx + 1
    wy = wy + 1
    x = x + (wx >> 1)
    wx = wx & 1
    y = y + (wy >> 1)
    wy = wy & 1
    if wx:
        ex = math.floor((x + 1) * (cwid - wallwid) / wid)
        x_coord = math.floor(x * (cwid - wallwid) / wid) + wallwid
    else:
        x_coord = math.floor(x * (cwid - wallwid) / wid)
        ex = x_coord + wallwid
    if wy:
        ey = math.floor((y + 1) * (chei - wallwid) / hei)
        y_coord = math.floor(y * (chei - wallwid) / hei) + wallwid
    else:
        y_coord = math.floor(y * (chei - wallwid) / hei)
        ey = y_coord + wallwid
    rect = pygame.Rect(x_coord, y_coord, ex - x_coord, ey - y_coord)
    pygame.draw.rect(screen, clr, rect)

# ---------------------------
# Wall Removal Function
# ---------------------------
def tryWall(wall, screen):
    if wall['clr']:
        return False
    c1 = wall['y'] * wid + wall['x']
    c2 = c1 + (1 if wall['dr'] else wid)
    if not union(c1, c2):
        return False
    wall['clr'] = True
    # clear the wall by drawing a white rectangle over it
    fill(wall['x'], wall['y'], (1 if wall['dr'] else 0), (0 if wall['dr'] else 1), WHITE, screen)
    for i in range(6):
        neighbour = getNeighbour(wall, i)
        if neighbour:
            updateWallType(neighbour)
    return True

# ---------------------------
# Maze Generation Step Function
# ---------------------------
def step(screen):
    global doneTo
    # select a wall from the queues, weighted by the number of items and their weights.
    total_weight = sum(len(wallqs[i]) * weights[i] for i in range(9))
    if total_weight <= 0:
        return False  # no more walls to check, maze generation finished
    w = total_weight * random.random()
    for i in range(9):
        chunk = len(wallqs[i]) * weights[i]
        if w < chunk:
            queue_index = i
            break
        w -= chunk
    else:
        queue_index = 0  # fallback
    if not wallqs[queue_index]:
        return True
    wall = wallqs[queue_index].pop()
    if wall and wall['typ'] == queue_index and tryWall(wall, screen):
        doneTo += (20.0 - speedctrl) * 250.0 / (wid * hei)
    return True

# ---------------------------
# Initialisation Function
# ---------------------------
def init(screen):
    global ufarray, wallqs, wallsbynum, startx, finishx, doneTo
    ufarray = []
    wallqs = [[] for _ in range(9)]
    wallsbynum = []
    screen.fill(BLACK)
    startx = randInt(wid)
    finishx = randInt(wid)
    # draw the entrance and exit
    fill(startx, 0, 0, -1, WHITE, screen)
    fill(finishx, hei - 1, 0, 1, WHITE, screen)
    
    # create grid cells and add walls between them
    for y in range(hei):
        for x in range(wid):
            fill(x, y, 0, 0, WHITE, screen)
            if x < wid - 1:
                wall = {'x': x, 'y': y, 'dr': True, 'typ': 0, 'clr': False}
                wallsbynum.append(wall)
                pushrand(wallqs[0], wall)
            else:
                wallsbynum.append(None)
            if y < hei - 1:
                wall = {'x': x, 'y': y, 'dr': False, 'typ': 0, 'clr': False}
                wallsbynum.append(wall)
                pushrand(wallqs[0], wall)
            else:
                wallsbynum.append(None)
    doneTo = pygame.time.get_ticks()

# ---------------------------
# Main Loop
# ---------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((cwid, chei))
    pygame.display.set_caption("Weighted Randomised Kruskal Maze Generation")
    
    init(screen)
    # generate the entire maze
    while step(screen):
        pass
    pygame.display.flip()
    
    # wait for user to close the window
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    pygame.quit()

if __name__ == "__main__":
    main()
