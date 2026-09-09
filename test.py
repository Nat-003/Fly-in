from classes import Zone, Connection, Graph
from parser import Parser

def main():
    # zone_1 = Zone('test',(0, 0), 'normal', 1, 'red')
    # zone_2 = Zone('oui',(0, 1), 'normal', 1, 'red')
    # print(zone_1.name)
    try:
        parser = Parser("maps/easy/01_linear_path.txt")
        graph =  parser.parse()
        # print(graph.nb_drones)
        start = graph.get_zone("goal")
        # print(start.coords)
    except ValueError as e:
        print(e)
if __name__ == "__main__":
    main()