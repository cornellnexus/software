import unittest
import matplotlib.pyplot as plt

from engine.grid import Grid
from engine.kinematics import get_vincenty_x, get_vincenty_y

'''
Visualization and unit tests for grid.py
'''


def graph_traversal_path(g, map_name, distance_type, mode):
    """
    Plots both the gps and meters grid generated by Grid.py
    """
    gps_traversal_path = g.gps_waypoints
    meters_traversal_path = g.get_waypoints(mode)
    print('----------METERS TRAVERSAL PATH--------')
    print(meters_traversal_path)
    gps_xlist = []
    gps_ylist = []
    m_xlist = []
    m_ylist = []

    for node in gps_traversal_path:
        coords = node.get_coords()
        gps_xlist.append(coords[1])
        gps_ylist.append(coords[0])

    for node in meters_traversal_path:
        coords = node.get_coords()
        m_xlist.append(coords[0])
        m_ylist.append(coords[1])

    # Plotting gps grid
    plot1 = plt.figure(1)
    plt.plot(gps_xlist, gps_ylist, marker='o', markerfacecolor='blue')
    plt.plot(gps_xlist[0], gps_ylist[0], marker='o', markerfacecolor='red')
    plt.ylim(min(gps_ylist) - 0.000001, max(gps_ylist) + 0.000001)
    plt.xlim(min(gps_xlist) - 0.000001, max(gps_xlist) + 0.000001)
    plt.title('Grid in GPS coordinates')

    # Plotting meters grid
    plot2 = plt.figure(2)
    plt.plot(m_xlist, m_ylist, marker='o', markerfacecolor='blue')
    plt.ylim(min(m_ylist) - 1, max(m_ylist) + 1)
    plt.xlim(min(m_xlist) - 1, max(m_xlist) + 1)
    plt.title(map_name + ' Grid Converted to Meters ' + '(' + distance_type + ')')

    plt.show()
    plt.close()


class VisualizeGrid(unittest.TestCase):
    # def test_jessica_house(self):
    # # g = Grid(34.23117305494089, 34.23120742746021, -119.00640453979496, -119.00629523978851)
    # g = Grid(-76.483682, -76.483276, 42.444250, 42.444599)
    # graph_traversal_path(g.gps_traversal_path)

    # def test_pike_room(self):
    #     g = Grid(-76.488495, -76.488419, 42.444496, 42.444543)
    #     graph_traversal_path(g, 'Pike Room', 'Vincenty')

    def test_engineering_quad(self):
        g = Grid(42.444250, 42.444599, -76.483682, -76.483276)
        # g = Grid(42.444000, 42.444600, -76.483600, -76.483000)
        graph_traversal_path(g, 'Engineering Quad', 'Vincenty', 'full')


class TestGrid(unittest.TestCase):
    def test_borders_mode(self):
        count = 0
        g = Grid(42.444250, 42.444599, -76.483682, -76.483276)
        full_waypoints = g.get_waypoints('full')
        for nd in full_waypoints:
            if nd.is_border_node():
                count += 1
        self.assertNotEqual(count, g.get_num_rows() * g.get_num_cols(), 'is_border_node flag is set correctly')
        self.assertEqual(count, g.get_num_cols() * 2, 'is_border_node flag is set correctly')
        border_waypoints = g.get_waypoints('borders')
        border_node_count = (g.get_num_cols()*2)
        self.assertEqual(len(border_waypoints), border_node_count)

    def test_node_boundaries(self):
        lat_min, lat_max, long_min, long_max = 42.444250, 42.444599, -76.483682, -76.483276
        g = Grid(lat_min, lat_max, long_min, long_max)
        full_waypoints = g.get_waypoints('full')

        y_range = get_vincenty_y((lat_min, long_min), (lat_max, long_max))
        x_range = get_vincenty_x((lat_min, long_min), (lat_max, long_max))
        m_grid = g.meters_grid
        upper_right_node_m = m_grid[g.get_num_rows()-1][g.get_num_cols()-1]
        self.assertLessEqual(upper_right_node_m.get_coords()[0], x_range, "The meters grid shouldn't be larger than the lat bounds")
        self.assertLessEqual(upper_right_node_m.get_coords()[1], y_range, "The meters grid shouldn't be larger than the long bounds")


if __name__ == '__main__':
    unittest.main()
