from typing import Dict, List, Tuple, Optional, Any

def gridworld_5_cases_70_percent_returns(current_position: Tuple[int, int], actions: List[str]) -> Dict[str, Any]:
    """
    Processes an action sequence in a 2d gridworld using an internal state.

    Args:
        current_position (Tuple[int, int]): Position (x, y).
        actions (List[str]): List of actions, e.g., ["north", "east"].

    Returns:
        Dict[str, any]: Contains valid_action_sequence (bool) and final_position (Tuple[int, int]).
    """
    DIRECTIONS = {
        'north': (-1, 0),
        'south': (1, 0),
        'east': (0, 1),
        'west': (0, -1)
    }

    def move(position: Tuple[int, int], direction: str) -> Tuple[int, int]:
        dx, dy = DIRECTIONS[direction]
        return (position[0] + dx, position[1] + dy)

    def get_next_action(remaining_input: List[str]) -> Optional[str]:
        return remaining_input.pop(0) if remaining_input else None

    # if-statement 1
    if current_position == (3, 6) and get_next_action(actions) == "north":
        # Action bumps into a wall
        return {"valid_action_sequence": False, "final_position": (3, 6)}

    # if-statement 2
    if current_position == (1, 2) and get_next_action(actions) == "north":
        # Action bumps into a wall
        return {"valid_action_sequence": False, "final_position": (1, 2)}

    # if-statement 3
    if current_position == (4, 1) and get_next_action(actions) == "south":
        current_position = move(current_position, "south")

    # if-statement 4
    if current_position == (5, 1) and get_next_action(actions) == "south":
        current_position = move(current_position, "south")

    # if-statement 5
    if current_position == (6, 1) and get_next_action(actions) == "south":
        # Action bumps into a wall
        return {"valid_action_sequence": False, "final_position": (6, 1)}

    return {"valid_action_sequence": True, "final_position": current_position}
