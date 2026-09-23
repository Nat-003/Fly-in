from classes import Simulation
from parser import Parser
from pathfind import Pathfinder
import sys


def main():
    if len(sys.argv) != 2:
        print("Please provide a map path; usage: python main.py <map_file>")
    else:
        try:
            parser = Parser(sys.argv[1])
            graph =  parser.parse()
            pathfinder = Pathfinder(graph)
            sim = Simulation(graph, pathfinder)
            sim.run()
        except (ValueError, FileNotFoundError, PermissionError) as e:
            print(e)

if __name__ == "__main__":
    main()
