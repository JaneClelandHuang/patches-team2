"""Matplotlib front end.

Controls:
  left-drag     draw a region (corner cell to corner cell)
  right-click   remove the region under the cursor
  r             reset the board
  u             undo the last change
"""

import math
import time

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle

from .board import Board
from .rules import Rect

SHAPE_SYMBOLS = {
    "square": "□",
    "vertical-rectangle": "↕",    # taller than wide
    "horizontal-rectangle": "↔",  # wider than tall
    "any": "",
}


def draw_drone(ax, drone):
    """Draw a small top-down quadcopter on the drone's seed cell."""
    cx, cy = drone.col + 0.5, drone.row + 0.5
    arm = 0.28
    for dx, dy in ((arm, arm), (arm, -arm)):
        ax.add_line(Line2D([cx - dx, cx + dx], [cy - dy, cy + dy],
                           color="#333333", lw=3, zorder=3))
    for dx in (-arm, arm):
        for dy in (-arm, arm):
            ax.add_patch(Circle((cx + dx, cy + dy), 0.13, facecolor="white",
                                edgecolor="#333333", lw=1.5, zorder=4))
    ax.add_patch(Circle((cx, cy), 0.12, facecolor=drone.color,
                        edgecolor="black", lw=1.5, zorder=4))


class PatchesApp:
    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.board = Board(puzzle)
        self.colors = {d.id: d.color for d in puzzle.drones}
        self.drag_start = None   # (row, col) where the current drag began
        self.preview = None      # Rectangle artist shown while dragging

        self.moves = 0
        self.stats_history = []  # (moves, start_time, end_time) before each board.history step
        self.start_time = None   # time.monotonic() of the first move, or None
        self.end_time = None     # time.monotonic() when solved, or None

        self.fig, self.ax = plt.subplots(figsize=(6, 6.6))
        self.fig.canvas.manager.set_window_title("Patches")
        self.fig.canvas.mpl_connect("button_press_event", self.on_press)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.timer = self.fig.canvas.new_timer(interval=1000)
        self.timer.add_callback(self.redraw)
        self.message = "Drag from corner to corner to draw a region."
        self.redraw()

    # ---- coordinates -------------------------------------------------------

    def cell_at(self, event):
        """Grid (row, col) under the mouse, or None if outside the board."""
        if event.inaxes is not self.ax or event.xdata is None:
            return None
        row, col = math.floor(event.ydata), math.floor(event.xdata)
        n = self.puzzle.grid_size
        if 0 <= row < n and 0 <= col < n:
            return row, col
        return None

    # ---- event handlers ----------------------------------------------------

    def on_press(self, event):
        cell = self.cell_at(event)
        if cell is None:
            return
        if event.button == 1:
            self.drag_start = cell
            self.update_preview(cell)
        elif event.button == 3:
            before = self.stats_snapshot()
            removed = self.board.remove_at(*cell)
            if removed:
                self.message = f"Removed {removed}'s region."
                self.register_move()
            self.keep_stats(before)
            self.redraw()

    def on_motion(self, event):
        if self.drag_start is None:
            return
        cell = self.cell_at(event)
        if cell is not None:
            self.update_preview(cell)

    def on_release(self, event):
        if self.drag_start is None or event.button != 1:
            return
        end = self.cell_at(event) or self.drag_start
        rect = Rect.from_corners(*self.drag_start, *end)
        self.drag_start = None
        before = self.stats_snapshot()
        drone_id = self.board.place(rect)
        if drone_id is None:
            self.message = "A region must contain exactly one drone."
        else:
            self.register_move()
            if self.board.is_valid(drone_id):
                self.message = f"Assigned region to {drone_id}."
            else:
                self.message = f"{drone_id}'s region breaks its shape/size rule."
            self.keep_stats(before)
        self.redraw()

    def on_key(self, event):
        if event.key == "r":
            before = self.stats_snapshot()
            self.board.reset()
            self.moves = 0
            self.start_time = None
            self.end_time = None
            self.timer.stop()
            self.keep_stats(before)
            self.message = "Board reset."
            self.redraw()
        elif event.key == "u":
            if self.board.undo():
                self.moves, self.start_time, self.end_time = self.stats_history.pop()
                self.timer.stop()
                if self.start_time is not None and self.end_time is None:
                    self.timer.start()
                self.message = "Undid last move."
            else:
                self.message = "Nothing to undo."
            self.redraw()

    # ---- stats ---------------------------------------------------------------

    def stats_snapshot(self):
        """The board's history length and the stats, taken before a change."""
        return len(self.board.history), (self.moves, self.start_time, self.end_time)

    def keep_stats(self, snapshot):
        """If the change added a board history step, remember the stats from before it."""
        history_length, stats = snapshot
        if len(self.board.history) > history_length:
            self.stats_history.append(stats)

    def register_move(self):
        """Count a move made by the player and start the timer on the first one."""
        self.moves += 1
        if self.start_time is None:
            self.start_time = time.monotonic()
            self.timer.start()

    def elapsed_seconds(self):
        """Seconds since the first move, frozen once the puzzle is solved."""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.monotonic()
        return end - self.start_time

    @staticmethod
    def format_time(seconds):
        minutes, secs = divmod(int(seconds), 60)
        return f"{minutes}:{secs:02d}"

    # ---- drawing -----------------------------------------------------------

    def update_preview(self, end):
        rect = Rect.from_corners(*self.drag_start, *end)
        if self.preview is None:
            self.preview = Rectangle((0, 0), 0, 0, fill=False, lw=3, ls="--", ec="black", zorder=5)
            self.ax.add_patch(self.preview)
        self.preview.set_bounds(rect.left, rect.top, rect.width, rect.height)
        self.fig.canvas.draw_idle()

    def redraw(self):
        ax = self.ax
        ax.clear()
        self.preview = None
        n = self.puzzle.grid_size

        for drone_id, rect in self.board.regions.items():
            valid = self.board.is_valid(drone_id)
            ax.add_patch(Rectangle(
                (rect.left, rect.top), rect.width, rect.height,
                facecolor=self.colors[drone_id], alpha=0.55 if valid else 0.25,
                hatch=None if valid else "//", edgecolor="black", lw=2.5, zorder=2))

        solved = self.board.solved
        for drone in self.puzzle.drones:
            if solved:
                draw_drone(ax, drone)
                continue
            ax.add_patch(Rectangle((drone.col + 0.15, drone.row + 0.15), 0.7, 0.7,
                                   facecolor="white", edgecolor=drone.color, lw=3, zorder=3))
            size = "?" if drone.size is None else str(drone.size)
            label = f"{size}{SHAPE_SYMBOLS[drone.shape]}"
            ax.text(drone.col + 0.5, drone.row + 0.5, label, ha="center", va="center",
                    fontsize=12, fontweight="bold", zorder=4)

        ax.set_xlim(0, n)
        ax.set_ylim(n, 0)  # row 0 at the top
        ax.set_aspect("equal")
        ax.set_xticks(range(n + 1))
        ax.set_yticks(range(n + 1))
        ax.tick_params(length=0, labelbottom=False, labelleft=False)
        ax.grid(True, color="gray", lw=0.8)

        if self.board.solved:
            if self.end_time is None and self.start_time is not None:
                self.end_time = time.monotonic()
                self.timer.stop()
            status = "SOLVED! Every cell is searched exactly once."
            stats = f"SOLVED in {self.format_time(self.elapsed_seconds())} with {self.moves} moves!"
        else:
            status = (f"{len(self.board.regions)}/{len(self.puzzle.drones)} drones assigned, "
                      f"{self.board.covered_cells()}/{n * n} cells covered")
            stats = f"Moves: {self.moves} · Time: {self.format_time(self.elapsed_seconds())}"
        ax.set_title(f"{status}\n{stats}\n{self.message}", fontsize=10)
        self.fig.canvas.draw_idle()

    def run(self):
        plt.show()
