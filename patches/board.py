"""Game state: which region each drone currently has. No drawing code here."""

from .rules import Rect, is_solved, region_errors


class Board:
    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.regions = {}  # drone id -> Rect
        self.history = []  # earlier `regions` states, most recent last

    def place(self, rect):
        """Try to place a region drawn by the player.

        The region is assigned to the single drone whose seed it contains.
        Returns that drone's id, or None (and changes nothing) if the region
        contains no seed or more than one. A drone's previous region and any
        regions the new one overlaps are removed.
        """
        seeds = [d for d in self.puzzle.drones if rect.contains(d.row, d.col)]
        if len(seeds) != 1:
            return None
        drone = seeds[0]
        new_regions = {did: r for did, r in self.regions.items()
                       if did != drone.id and not r.overlaps(rect)}
        new_regions[drone.id] = rect
        if new_regions != self.regions:
            self.history.append(dict(self.regions))
        self.regions = new_regions
        return drone.id

    def region_at(self, row, col):
        """Return the id of the drone whose region covers (row, col), or None."""
        for drone_id, rect in self.regions.items():
            if rect.contains(row, col):
                return drone_id
        return None

    def remove_at(self, row, col):
        """Remove the region covering (row, col). Returns the removed drone id."""
        drone_id = self.region_at(row, col)
        if drone_id is not None:
            self.history.append(dict(self.regions))
            del self.regions[drone_id]
        return drone_id

    def reset(self):
        if self.regions:
            self.history.append(dict(self.regions))
        self.regions = {}

    def undo(self):
        """Restore the regions from before the last change.

        Returns True, or False (and changes nothing) if there is nothing to undo.
        """
        if not self.history:
            return False
        self.regions = self.history.pop()
        return True

    def is_valid(self, drone_id):
        """True if the drone's current region satisfies its shape/size rules."""
        drone = next(d for d in self.puzzle.drones if d.id == drone_id)
        rect = self.regions.get(drone_id)
        return rect is not None and not region_errors(self.puzzle, drone, rect)

    def covered_cells(self):
        return sum(r.area for r in self.regions.values())

    @property
    def solved(self):
        return is_solved(self.puzzle, self.regions)


__all__ = ["Board", "Rect"]
