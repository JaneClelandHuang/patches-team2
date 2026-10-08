"""Backtracking solver: find the full solution to a puzzle.

Used by the hint feature, so a hint can show a piece of the real solution
rather than just any rectangle that happens to follow a drone's rules.
"""

from .rules import Rect, is_solved, region_errors


def candidate_rects(puzzle, drone):
    """Every rectangle on the grid that is a valid region for `drone`."""
    n = puzzle.grid_size
    rects = []
    for top in range(n):
        for left in range(n):
            for height in range(1, n - top + 1):
                for width in range(1, n - left + 1):
                    rect = Rect(top, left, height, width)
                    if not region_errors(puzzle, drone, rect):
                        rects.append(rect)
    return rects


def solve(puzzle):
    """Return {drone_id: Rect} solving `puzzle`, or None if there is no solution."""
    options = [(drone, candidate_rects(puzzle, drone)) for drone in puzzle.drones]
    regions = {}
    used = set()

    def place_from(index):
        if index == len(options):
            return is_solved(puzzle, regions)
        drone, rects = options[index]
        for rect in rects:
            cells = rect.cells()
            if cells & used:
                continue
            regions[drone.id] = rect
            used.update(cells)
            if place_from(index + 1):
                return True
            used.difference_update(cells)
            del regions[drone.id]
        return False

    return regions if place_from(0) else None
