import random
import os
from pathlib import Path
from typing import Tuple, Dict, List, Any, Optional
import string

def generate_match_functions(num_cases: int, return_percentage: float, k: int, output_dir: str = "generated_functions"):
    """
    Generates k Python functions with match/case statements based on an adventure grid cell map.
    
    Args:
        num_cases: Number of case statements in each function.
        return_percentage: Percentage of cases that should have a return (0.0 to 100.0).
        k: Number of functions to generate.
        output_dir: Directory to save the generated functions.
    """
    # Constants for the grid
    GRID_ROWS = 8
    GRID_COLS = 8

    # Directions mapping
    DIRECTIONS = {
        'north': (-1, 0),
        'south': (1, 0),
        'east': (0, 1),
        'west': (0, -1)
    }

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Define the 2d gridworld (see report)
    grid = [
        [1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 0, 0, 1, 1, 1, 1],
        [1, 0, 0, 0, 1, 0, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 1],
        [1, 0, 1, 0, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1]
    ]

    def is_wall(position: Tuple[int, int]) -> bool:
        x, y = position
        return bool(grid[x][y])
    
    def get_valid_actions(position: Tuple[int, int]) -> List[str]:
        x, y = position
        return [dir for dir, (dx, dy) in DIRECTIONS.items() 
                if 0 <= x + dx < GRID_ROWS and 0 <= y + dy < GRID_COLS 
                and not is_wall((x + dx, y + dy))]
    
    def get_walls() -> List[Tuple[int, int]]:
        walls = [
            (i, j) for i in range(GRID_ROWS) for j in range(GRID_COLS) if is_wall((i, j))
        ]
        return walls
        
    """
    Example:
        num_cases = 10
        num_return_cases = int(10 * 0.3 / 100) = 3
        first_paths_len = 10 // 3 = 3  # path lengths: 3,3,4
        last_path_len = 10 - (3 - 1) * 3 = 4
    """

    num_return_cases = int(num_cases * return_percentage / 100)
    first_paths_len = num_cases // num_return_cases
    last_path_len = num_cases - (num_return_cases - 1) * first_paths_len

    func_name = f"gridworld_{num_cases}_cases_{int(return_percentage)}_percent_returns"

    walls = get_walls()
    walls_with_walkable_neighbor = [
        wall for wall in walls
        if len(get_valid_actions(wall)) > 0
    ]
    sequences = []

    for path in range(num_return_cases):
        if path == num_return_cases - 1:
            seq_length = last_path_len
        else:
            seq_length = first_paths_len

        # Generate the sequence in reverse (start at a random wall position and then take random valid actions)
        end_pos = random.choice(walls_with_walkable_neighbor)

        current_pos = end_pos
        actions = []
        for step in range(seq_length):
            direction = random.choice(get_valid_actions(current_pos))
            dx, dy = DIRECTIONS[direction]
            current_pos = (current_pos[0] + dx, current_pos[1] + dy)
            actions.append(direction)

        # Reverse the sequence
        start_pos = current_pos
        def reverse_action(action: str) -> str:
            return {"north": "south", "south": "north", "east": "west", "west": "east"}[action]
        actions = [reverse_action(action) for action in reversed(actions)]

        sequences.append({
            "start": start_pos,
            "actions": actions
        })

    # print(sequences)


    # Build the function string with internal state management
    func_str = "from typing import Dict, List, Tuple, Optional, Any\n\n"
    func_str += "def {}(current_position: Tuple[int, int], actions: List[str]) -> Dict[str, Any]:\n".format(func_name)
    func_str += "    \"\"\"\n"
    func_str += "    Processes an action sequence in a 2d gridworld using an internal state.\n\n"
    func_str += "    Args:\n"
    func_str += "        current_position (Tuple[int, int]): Position (x, y).\n"
    func_str += "        actions (List[str]): List of actions, e.g., [\"north\", \"east\"].\n\n"
    func_str += "    Returns:\n"
    func_str += "        Dict[str, any]: Contains valid_action_sequence (bool) and final_position (Tuple[int, int]).\n"
    func_str += "    \"\"\"\n"
    func_str += "    DIRECTIONS = {\n"
    func_str += "        'north': (-1, 0),\n"
    func_str += "        'south': (1, 0),\n"
    func_str += "        'east': (0, 1),\n"
    func_str += "        'west': (0, -1)\n"
    func_str += "    }\n\n"
    func_str += "    def move(position: Tuple[int, int], direction: str) -> Tuple[int, int]:\n"
    func_str += "        dx, dy = DIRECTIONS[direction]\n"
    func_str += "        return (position[0] + dx, position[1] + dy)\n\n"
    func_str += "    def get_next_action(remaining_input: List[str]) -> Optional[str]:\n"
    func_str += "        return remaining_input.pop(0) if remaining_input else None\n\n"

    # Generate if statements for each sequence
    for idx, seq in enumerate(sequences):
        current_pos = seq["start"]
        actions = seq["actions"]
        
        for action_idx, action in enumerate(actions):
            # Add comment for the if-statement
            func_str += f"    # if-statement {len(func_str.split('if ')) - 1}\n"
            func_str += f"    if current_position == {current_pos} and get_next_action(actions) == \"{action}\""
            
            if action_idx == len(actions) - 1 and idx < num_return_cases:
                # Last action in a sequence that should return (hits wall)
                func_str += ":\n        # Action bumps into a wall\n"
                func_str += "        return {\"valid_action_sequence\": False, \"final_position\": " + str(current_pos) + "}\n\n"
            else:
                # Intermediate action
                dx, dy = DIRECTIONS[action]
                current_pos = (current_pos[0] + dx, current_pos[1] + dy)
                func_str += ":\n"
                func_str += f"        current_position = move(current_position, \"{action}\")\n\n"

    func_str += "    return {\"valid_action_sequence\": True, \"final_position\": current_position}\n"

    # Save to file
    file_path = os.path.join(output_dir, f"{func_name}.py")
    with open(file_path, "w") as f:
        f.write(func_str)
    
    print(f"Generated {func_name} to {file_path}")

if __name__ == "__main__":
    
    # # Example usage
    # generate_match_functions(
    #     num_cases=8,
    #     return_percentage=75,
    #     k=1,
    #     output_dir="generated_functions"
    # )

    for num_cases in [5, 10, 15]:
        for return_percentage in [30, 50, 70]:
            generate_match_functions(
                num_cases=num_cases,
                return_percentage=return_percentage,
                k=1,
                output_dir="generated_functions"
            )

