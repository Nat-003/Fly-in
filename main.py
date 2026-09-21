from classes import Zone, Connection, Graph, Simulation
from parser import Parser
from pathfind import Pathfinder

def main():
    # zone_1 = Zone('test',(0, 0), 'normal', 1, 'red')
    # zone_2 = Zone('oui',(0, 1), 'normal', 1, 'red')
    # print(zone_1.name)
    try:
        parser = Parser("maps/easy/01_linear_path.txt")
        graph =  parser.parse()
        pathfinder = Pathfinder(graph)
        # pathfinder.find_path()
        sim = Simulation(graph, pathfinder)
        sim.run()

        
        

    except ValueError as e:
        print(e)
if __name__ == "__main__":
    main()