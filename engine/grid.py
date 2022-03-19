from platform import node
from engine.node import Node
import numpy as np
from engine.kinematics import meters_to_lat, meters_to_long, get_vincenty_x, get_vincenty_y
from enum import Enum


class Grid:
    """
    Instances represent the current grid of the robot's traversal.

    INSTANCE ATTRIBUTES:
        # nodes: 2D Node List representing all the Node objects that make up the grid. [[Node List] List]
        # waypoints: Ordered list of Node objects to travel to that have not yet been traversed by the robot.

        # nodes_dict: Dictionary of all Node objects in the grid
            - Keys are (y,x), aka (latitude, longitude), tuples.
            - Values are Node objects

        # lat_min, lat_max, long_min, long_max: // doesn't make sense to have this be the actual map should just be of our grid
            minimum/maximum latitude/longitude boundary points of the actual map. [float]

        #num_rows: Number of rows of Nodes in the grid [int]
        #num_cols: Number of columns of Nodes in the grid. [int]

        #leftmost_node: the leftmost active node in the Grid which is used as the starting node in lawnmower and spiral traversal.
        #leftmost_node_pos: the (row,col) position of the leftmost node
        #border_nodes: all active nodes which either exist on the edge of the grid or have a neighbor that is an inactive node
    """

    def __init__(self, lat_min, lat_max, long_min, long_max):
        STEP_SIZE_METERS = 2

        # ----------- HELPER FUNCTIONS FOR GRID INITIALIZATION ------------#
        def calc_step(lat_min, lat_max, long_min, long_max, step_size_m):
            """
            Returns the number of rows and columns needed for a grid, given
            latitude and longitude boundaries and a desired step size between
            nodes in meters.

            Parameters:
            -----------
            # lat_min, lat_max, long_min, long_max: desired latitude and longitude boundaries of the grid [float]
            # step_size_m: step size in between nodes of the grid [float]
            """
            y_range = get_vincenty_y((lat_min, long_min), (lat_max, long_max))
            x_range = get_vincenty_x((lat_min, long_min), (lat_max, long_max))

            num_y_steps = int(y_range // step_size_m)
            num_x_steps = int(x_range // step_size_m)

            num_rows = num_y_steps + 1  # to account for starting node
            num_cols = num_x_steps + 1

            return num_rows, num_cols

        def generate_nodes(start_lat, start_long, rows, cols, step_size_m):
            """
            Returns a list of Node objects that make up the entire grid. [Node list]

            Parameters:
            -----------
            # start_lat: latitude coordinate of the robot's starting position [float]
            # start_long: longitude coordinate of the robot's starting position [float]
            # rows: # of rows in the grid [int]
            # cols: # of cols in the grid [int]
            # step_size_m: step size in between nodes of the grid (in meters) [float]
            """
            node_list = np.empty([rows, cols], dtype=np.object)

            gps_origin = (start_lat, start_long)

            lat_step = meters_to_lat(step_size_m)
            long_step = meters_to_long(step_size_m, start_lat)

            # Develop the gps grid and gps traversal path in order of lawnmower
            # traversal.
            for i in range(cols):
                for j in range(rows):
                    #is_border = (j == 0 or j == rows - 1)
                    if i % 2 == 0:
                        lat = gps_origin[0] + j * lat_step
                        long = gps_origin[1] + i * long_step
                        x = get_vincenty_x(gps_origin, (lat, long))
                        y = get_vincenty_y(gps_origin, (lat, long))
                        node = Node(lat, long, x, y)  # , is_border)
                        node_list[j, i] = node
                    elif i % 2 == 1:
                        lat = gps_origin[0] + \
                            ((rows - 1) * lat_step) - j * lat_step
                        long = gps_origin[1] + i * long_step
                        x = get_vincenty_x(gps_origin, (lat, long))
                        y = get_vincenty_y(gps_origin, (lat, long))
                        node = Node(lat, long, x, y)  # , is_border)
                        row_index = rows - (j + 1)
                        node_list[row_index, i] = node

            return node_list

        # ----------------- GRID INITIALIZATION BEGINS ------------------- #
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.long_min = long_min
        self.long_max = long_max

        self.num_rows, self.num_cols = calc_step(
            lat_min, lat_max, long_min, long_max, STEP_SIZE_METERS)

        self.nodes = generate_nodes(
            lat_min, long_min, self.num_rows, self.num_cols, STEP_SIZE_METERS)
        self.border_nodes = None
        self.leftmost_node = None
        self.leftmost_node_pos = None

    def get_num_rows(self):
        return self.num_rows

    def get_num_cols(self):
        return self.num_cols

    # --------------------- METHODS TO ACTIVATE NODES ON THE GRID -------------- #

    def activate_node(self, row, col):
        """
        Activates the node at the given location.
        """
        self.nodes[row][col].activate_node()

    def activate_nodes(self, row, col, row_limit, col_limit):
        """
        Activates all the nodes in the given range.
        """
        for y in range(row, row_limit):
            for x in range(col, col_limit):
                self.activate_node(y, x)

    # --------------------- METHODS TO FINISH INITIALIZATION OF ACTIVATED GRID -------------- #

    def is_on_border(self, row, col, row_limit, col_limit):
        """
        Returns whether a particular activated node is on the border.

        An activated node is on the border if any of the following conditions hold:
        1. Any of its neighboring nodes are inactive.
        2. It exists on the very edge of the grid.
        """
        min_col = max(0, col-1)
        min_row = max(0, row-1)
        max_col = min(col_limit, col+1)
        max_row = min(row_limit, row+1)

        # If this node is on the very edge of the grid, it is automatically a border node
        if min_col == 0 or min_row == 0 or max_col == col_limit or max_row == row_limit:
            return True

        # If the node has a neighboring node that is inactive, it is a border node
        for col in range(min_col, max_col):
            for row in range(min_row, max_row):
                if not self.nodes[row][col].is_active_node():
                    return True
        return False

    def find_border_nodes(self):
        """
        Find all activated border nodes on the grid.

        This function loops through all the nodes, checks if a particular node has
        been activated, and if so checks to see if that node is a border node. At the
        end of the function call, fields 'leftmost_node', 'leftmost_node_pos', and
        'border_nodes' will be initialized.
        """
        node_list = self.nodes
        border_list = []
        cols = node_list.shape[1]
        rows = node_list.shape[0]
        leftmost_node = None
        leftmost_node_pos = None
        for row in range(rows):
            for col in range(cols):
                node = node_list[row][col]
                if node.is_active() and self.is_on_border(row, col, rows-1, cols-1):
                    # check if this is an active node and on the border
                    node.set_border_node()
                    border_list.append(node)
                    if leftmost_node_pos is None or col < leftmost_node_pos[1]:
                        leftmost_node = node
                        leftmost_node_pos = (row, col)
        self.border_nodes = border_list
        self.leftmost_node = leftmost_node
        self.leftmost_node_pos = leftmost_node_pos

    # --------------------- ADJUSTABLE TRAVERSAL ALGORITHMS -------------- #

    def get_neighbor_node(self, row, col, row_max, col_max):
        """
        Returns the active neighbor node at the given row and col position.

        If the row/col position is out of bounds or no active node exists at the
        given location, None is returned.
        """
        if row < 0 or row >= row_max or col < 0 or col >= col_max:
            return None

        node_list = self.nodes
        neighbor_node = node_list[row][col]
        if not neighbor_node.is_active_node():
            return None
        else:
            return neighbor_node

    def get_all_lawnmower_waypoints_adjustable(self):
        class WaypointPhase(Enum):
            UP = 1
            DOWN = 2
            UP_RIGHT = 3
            DOWN_RIGHT = 4
            TERMINATE = 5

        node_list = self.nodes
        rows = node_list.shape[0]
        cols = node_list.shape[1]
        row, col = self.leftmost_node_pos
        current_node = self.leftmost_node
        waypoints = [current_node]
        phase = WaypointPhase.DOWN

        while (phase != WaypointPhase.TERMINATE):
            if (phase == WaypointPhase.UP):
                top_neighbor = self.get_neighbor_node(row-1, col, rows, cols)
                if top_neighbor is None:
                    phase = WaypointPhase.DOWN_RIGHT
                else:
                    node_list.append(top_neighbor)
                    row = row - 1
            elif (phase == WaypointPhase.DOWN):
                bottom_neighbor = self.get_neighbor_node(
                    row+1, col, rows, cols)
                if bottom_neighbor is None:
                    phase = WaypointPhase.UP_RIGHT
                else:
                    node_list.append(bottom_neighbor)
                    row = row + 1
            elif (phase == WaypointPhase.UP_RIGHT):
                right_neighbor = self.get_neighbor_node(row, col+1, rows, cols)
                if right_neighbor is None:
                    rows = rows - 1
                else:
                    node_list.append(right_neighbor)
                    col = col + 1
                    phase = WaypointPhase.UP
            elif (phase == WaypointPhase.DOWN_RIGHT):
                right_neighbor = self.get_neighbor_node(row, col+1, rows, cols)
                if right_neighbor is None:
                    rows = rows + 1
                else:
                    node_list.append(right_neighbor)
                    col = col + 1
                    phase = WaypointPhase.DOWN

    # --------------------- STANDARD TRAVERSAL ALGORITHMS -------------- #

    def get_spiral_waypoints(self):
        """
        Returns the robot's spiral traversal path for the current grid using every
        single node of the grid. [Node list].
        """
        waypoints = []
        node_list = self.nodes
        rows = node_list.shape[0]
        cols = node_list.shape[1]

        col = 0  # start at bottom left corner
        row = 0

        # these tuples simulate the robot's next movement based on turn state
        step_col = (1, 0, -1, 0)
        step_row = (0, 1, 0, -1)
        turn_state = 0  # turn_state is a variable that must be between 0..3

        for _ in range(rows * cols):  # for loop over all nodes
            node = node_list[row, col]
            waypoints.append(node)
            next_col = col + step_col[turn_state]
            next_row = row + step_row[turn_state]
            if 0 <= next_col < cols and 0 <= next_row < rows and not node_list[next_row, next_col] in waypoints:
                col = next_col
                row = next_row
            else:
                turn_state = (turn_state + 1) % 4
                next_col = col + step_col[turn_state]
                next_row = row + step_row[turn_state]
                col = next_col
                row = next_row
        waypoints.reverse()
        return waypoints

    def get_all_lawnmower_waypoints(self):
        """
        Returns the robot's lawnmower traversal path for the current grid using every
        single node of the grid. Starting node is the bottom left node of the list. Node list].
        """
        waypoints = []
        node_list = self.nodes
        rows = node_list.shape[0]
        cols = node_list.shape[1]
        for i in range(cols):
            for j in range(rows):
                if i % 2 == 0:
                    node = node_list[j, i]
                    waypoints.append(node)
                elif i % 2 == 1:
                    row_index = rows - (j + 1)
                    node = node_list[row_index, i]
                    waypoints.append(node)
        return waypoints

    def get_border_lawnmower_waypoints(self):
        """
        Returns the robot's lawnmower border traversal path for the current grid using
        only nodes in the top/bottom row of the grid. Starting node is the bottom left
        node of the list. [Node list].
        """
        waypoints = []
        node_list = self.nodes
        rows = node_list.shape[0]
        cols = node_list.shape[1]
        for i in range(cols):
            if i % 2 == 0:
                node1 = node_list[0, i]
                node2 = node_list[rows - 1, i]
                waypoints.append(node1)
                waypoints.append(node2)
            elif i % 2 == 1:
                node1 = node_list[rows - 1, i]
                node2 = node_list[0, i]
                waypoints.append(node1)
                waypoints.append(node2)
        return waypoints

    def get_waypoints(self, mode):
        """
        Returns the robot's traversal path for the current grid. [Node list].
        Returns empty list if [mode] is not one of [ControlMode.LAWNMOWER],
        [ControlMODE.LAWNMOWER_B], or [ControlMODE.SPIRAL].

        Parameters:
        -----------
        # mode: The type of traversal path that is desired. [ControlMode].
            LAWNMOWER:
                - lawnmower traversal using every single node of the grid
                - starting node is the bottom left node of the grid

            LAWNMOWER_B:
                - lawnmower traversal using only the nodes in the top/bottom row of the grid
                - starting node is the bottom left node of the grid

            SPIRAL:
                -spiral traversal using every single node of the grid
                -starting node varies based on the width/height of the grid
                -ending node is the bottom left node of the grid
        """
        from engine.mission import ControlMode  # import placed here to avoid circular import
        if mode == ControlMode.LAWNMOWER_FULL:
            waypoints = self.get_all_lawnmower_waypoints()
        elif mode == ControlMode.LAWNMOWER_BORDERS:
            waypoints = self.get_border_lawnmower_waypoints()
        elif mode == ControlMode.SPIRAL:
            waypoints = self.get_spiral_waypoints()
        else:
            return []
        return waypoints
