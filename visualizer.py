# from classes import Graph, Drone
from typing import Any

# from classes import Graph, Drone


class Visualiser:
    COLORS = {
        "black": "30", "red": "31", "green": "32", "yellow": "33",
        "blue": "34", "magenta": "35", "purple": "35", "cyan": "36",
        "white": "37", "gray": "90", "grey": "90", "orange": "33",
    }

    def __init__(self, graph: Any, drones: list[Any]) -> None:
        self.graph = graph
        self.drones = drones

    def colorize(self, text: str, color_name: str | None) -> str:
        if color_name is None or color_name not in self.COLORS:
            return text
        return f"\033[{self.COLORS[color_name]}m{text}\033[0m"

    def render(self, turn_number: int, moves: list[str]) -> None:
        line = " ".join(moves)
        print(f"Turn {turn_number} | {line}")
        print("--- ZONES ---")
        for z in self.graph.zones.values():
            if z is self.graph.start:
                remaining = sum(
                    1 for d in self.drones
                    if d.path_index == 0 and not d.is_in_transit()
                )
                state = f"remaining: {remaining}"
            elif z is self.graph.end:
                delivered = sum(1 for d in self.drones if d.has_arrived())
                state = f"delivered: {delivered}/{len(self.drones)}"
            else:
                here = " ".join(f"D{i}" for i in z.occupants)
                inbound = " ".join(
                    f"-> D{d.id} (transit)" for d in self.drones
                    if d.is_in_transit() and d.get_next_zone() is z
                )
                parts = [p for p in (here, inbound) if p]
                state = " ".join(parts) if parts else "."
            padded = f"{z.name:<12}"
            colored_name = self.colorize(padded, z.color)
            print(f"  {colored_name} {state}")