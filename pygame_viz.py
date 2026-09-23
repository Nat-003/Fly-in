"""
Standalone pygame visualizer for the fly-in simulation.

This is a DEBUG / VISUALIZATION tool — it is not part of the graded
project and is intentionally kept separate from main.py and the
terminal Visualiser. It reads live state from the Graph and the
drones after each turn (the same "Option 1" approach as the terminal
visualiser: it inspects, it never drives the scheduling).

Usage:
    python3 pygame_viz.py <map_file>

Controls:
    SPACE / RIGHT ARROW : advance one simulation turn
    R                   : reset to the initial state
    ESC / window close  : quit
"""

import sys
import pygame

from parser import Parser
from pathfind import Pathfinder
from classes import Simulation, Graph, Zone


# ---- window / layout constants -----------------------------------
WIDTH, HEIGHT = 1100, 720
MARGIN = 90                 # keep nodes away from the window edges
ZONE_RADIUS = 34
DRONE_RADIUS = 11
FPS = 60

# ---- colours (R, G, B) -------------------------------------------
BG = (24, 26, 32)
EDGE = (90, 96, 110)
EDGE_LABEL = (150, 156, 170)
TEXT = (235, 237, 242)
ZONE_OUTLINE = (230, 232, 238)
DRONE_FILL = (255, 210, 70)
DRONE_TEXT = (20, 20, 20)

# Map the map-file colour names to RGB. Unknown names fall back to grey.
NAMED_COLORS = {
    "red": (200, 70, 70),
    "green": (80, 170, 90),
    "blue": (70, 110, 200),
    "yellow": (210, 190, 70),
    "orange": (220, 150, 60),
    "gray": (120, 124, 134),
    "grey": (120, 124, 134),
    "cyan": (80, 190, 200),
    "purple": (150, 90, 190),
    "white": (220, 222, 228),
}
ZONE_TYPE_FALLBACK = {
    "normal": (70, 110, 200),
    "restricted": (200, 70, 70),
    "priority": (80, 170, 90),
    "blocked": (90, 92, 100),
}


def zone_color(zone: Zone) -> tuple[int, int, int]:
    """Colour a zone by its map colour, else by its type, else grey."""
    if zone.color and zone.color.lower() in NAMED_COLORS:
        return NAMED_COLORS[zone.color.lower()]
    return ZONE_TYPE_FALLBACK.get(zone.zone_type, (120, 124, 134))


def compute_positions(graph: Graph) -> dict[str, tuple[int, int]]:
    """Scale the integer map coordinates to fill the window.

    Map coords are small ints (e.g. 0..10). We find their min/max and
    linearly map them into the drawable area inside the margins. If all
    zones share an x (or y), we centre that axis to avoid a divide-by-zero.
    """
    xs = [z.coords[0] for z in graph.zones.values()]
    ys = [z.coords[1] for z in graph.zones.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x or 1
    span_y = max_y - min_y or 1
    draw_w = WIDTH - 2 * MARGIN
    draw_h = HEIGHT - 2 * MARGIN

    pos: dict[str, tuple[int, int]] = {}
    for z in graph.zones.values():
        if max_x == min_x:
            px = WIDTH // 2
        else:
            px = MARGIN + int((z.coords[0] - min_x) / span_x * draw_w)
        if max_y == min_y:
            py = HEIGHT // 2
        else:
            py = MARGIN + int((z.coords[1] - min_y) / span_y * draw_h)
        pos[z.name] = (px, py)
    return pos


def drones_in_transit_on(connection: object, drones: list) -> list[int]:
    """Ids of drones currently flying on this connection."""
    return [d.id for d in drones if d.is_in_transit() and d.in_transit is connection]


def draw(
    screen: pygame.Surface,
    graph: Graph,
    drones: list,
    pos: dict[str, tuple[int, int]],
    font: pygame.font.Font,
    small: pygame.font.Font,
    turn: int,
    finished: bool,
) -> None:
    screen.fill(BG)

    # --- edges first, so nodes sit on top ---
    drawn = set()
    for name, conns in graph.adjacency.items():
        for c in conns:
            key = c.normalized_key()
            if key in drawn:
                continue
            drawn.add(key)
            a = pos[c.zone_a.name]
            b = pos[c.zone_b.name]
            pygame.draw.line(screen, EDGE, a, b, 3)
            # connection label "<from>-<to>" at the midpoint
            mid = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
            label = f"{c.zone_a.name}-{c.zone_b.name}"
            surf = small.render(label, True, EDGE_LABEL)
            rect = surf.get_rect(center=mid)
            # slight background pad so it's readable over the line
            pad = rect.inflate(6, 2)
            pygame.draw.rect(screen, BG, pad)
            screen.blit(surf, rect)

            # drones in transit on this connection: draw along the line
            transit = drones_in_transit_on(c, drones)
            for i, did in enumerate(transit):
                t = (i + 1) / (len(transit) + 1)
                dx = int(a[0] + (b[0] - a[0]) * t)
                dy = int(a[1] + (b[1] - a[1]) * t)
                pygame.draw.circle(screen, (255, 140, 140), (dx, dy), DRONE_RADIUS)
                ds = small.render(f"D{did}", True, DRONE_TEXT)
                screen.blit(ds, ds.get_rect(center=(dx, dy)))

    # --- zones ---
    for z in graph.zones.values():
        cx, cy = pos[z.name]
        pygame.draw.circle(screen, zone_color(z), (cx, cy), ZONE_RADIUS)
        pygame.draw.circle(screen, ZONE_OUTLINE, (cx, cy), ZONE_RADIUS, 2)
        # zone name just above the circle
        nlabel = font.render(z.name, True, TEXT)
        screen.blit(nlabel, nlabel.get_rect(center=(cx, cy - ZONE_RADIUS - 12)))

        # drones sitting in this zone (occupants are ids)
        occ = z.occupants
        # end zone: show a delivered count instead of every drone
        if z is graph.end:
            arrived = sum(1 for d in drones if d.has_arrived())
            clabel = small.render(f"{arrived}/{len(drones)}", True, DRONE_TEXT)
            screen.blit(clabel, clabel.get_rect(center=(cx, cy)))
        elif z is graph.start:
            remaining = sum(
                1 for d in drones
                if d.path_index == 0 and not d.is_in_transit()
            )
            clabel = small.render(f"{remaining} left", True, DRONE_TEXT)
            screen.blit(clabel, clabel.get_rect(center=(cx, cy)))
        else:
            _draw_drone_cluster(screen, small, occ, cx, cy)

    # --- HUD ---
    status = "ALL DELIVERED" if finished else "SPACE = next turn   R = reset   ESC = quit"
    hud = font.render(f"Turn {turn}    {status}", True, TEXT)
    screen.blit(hud, (20, 16))


def _draw_drone_cluster(
    screen: pygame.Surface,
    small: pygame.font.Font,
    ids: list[int],
    cx: int,
    cy: int,
) -> None:
    """Place small drone circles around the zone centre."""
    if not ids:
        return
    import math
    if len(ids) == 1:
        spots = [(cx, cy)]
    else:
        spots = []
        r = ZONE_RADIUS - DRONE_RADIUS - 2
        for i in range(len(ids)):
            ang = 2 * math.pi * i / len(ids)
            spots.append((int(cx + r * math.cos(ang)), int(cy + r * math.sin(ang))))
    for (sx, sy), did in zip(spots, ids):
        pygame.draw.circle(screen, DRONE_FILL, (sx, sy), DRONE_RADIUS)
        ds = small.render(f"D{did}", True, DRONE_TEXT)
        screen.blit(ds, ds.get_rect(center=(sx, sy)))


def build_sim(map_path: str) -> Simulation:
    graph = Parser(map_path).parse()
    pathfinder = Pathfinder(graph)
    return Simulation(graph, pathfinder)


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python3 pygame_viz.py <map_file>")
        return

    map_path = sys.argv[1]
    try:
        sim = build_sim(map_path)
    except (ValueError, FileNotFoundError, PermissionError) as e:
        print(e)
        return

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"fly-in — {map_path}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,menlo,monospace", 18)
    small = pygame.font.SysFont("consolas,menlo,monospace", 14)

    pos = compute_positions(sim.graph)
    turn = 0
    finished = sim.all_arrived()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,):
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_RIGHT):
                    if not finished:
                        sim.take_turn()
                        turn += 1
                        finished = sim.all_arrived()
                elif event.key == pygame.K_r:
                    sim = build_sim(map_path)
                    pos = compute_positions(sim.graph)
                    turn = 0
                    finished = sim.all_arrived()

        draw(screen, sim.graph, sim.drones, pos, font, small, turn, finished)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
