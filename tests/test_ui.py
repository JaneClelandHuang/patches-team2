import matplotlib

matplotlib.use("Agg")  # headless: no window needed

from matplotlib.patches import Circle  # noqa: E402

from patches.puzzle import load_puzzle  # noqa: E402
from patches.ui import PatchesApp  # noqa: E402

from test_rules import PROBLEM1_SOLUTION  # noqa: E402


class FakeEvent:
    """Stand-in for a matplotlib mouse/key event."""

    def __init__(self, inaxes=None, xdata=None, ydata=None, button=None, key=None):
        self.inaxes = inaxes
        self.xdata = xdata
        self.ydata = ydata
        self.button = button
        self.key = key


def make_app():
    return PatchesApp(load_puzzle("puzzles/problem1.json"))


def click_cell(app, row, col, button=1):
    """Build a FakeEvent for a click/release on the given cell."""
    return FakeEvent(inaxes=app.ax, xdata=col + 0.5, ydata=row + 0.5, button=button)


def test_clues_shown_while_unsolved():
    app = make_app()
    assert len(app.ax.texts) == len(app.puzzle.drones)


def test_clues_become_drones_when_solved():
    app = make_app()
    for rect in PROBLEM1_SOLUTION.values():
        app.board.place(rect)
    app.redraw()
    assert len(app.ax.texts) == 0
    circles = [p for p in app.ax.patches if isinstance(p, Circle)]
    assert len(circles) == 5 * len(app.puzzle.drones)


def test_clues_return_after_unsolving():
    app = make_app()
    for rect in PROBLEM1_SOLUTION.values():
        app.board.place(rect)
    app.board.remove_at(0, 0)
    app.redraw()
    assert len(app.ax.texts) == len(app.puzzle.drones)


def test_moves_start_at_zero_and_successful_placement_adds_one():
    app = make_app()
    assert app.moves == 0
    app.drag_start = (0, 0)  # drone_1's seed
    app.on_release(click_cell(app, 0, 0))
    assert app.moves == 1


def test_rejected_placement_does_not_count():
    app = make_app()
    app.drag_start = (1, 1)  # no drone seed here
    app.on_release(click_cell(app, 1, 1))
    assert app.moves == 0


def test_reset_sets_moves_back_to_zero():
    app = make_app()
    app.drag_start = (0, 0)
    app.on_release(click_cell(app, 0, 0))
    assert app.moves == 1

    app.on_key(FakeEvent(key="r"))
    assert app.moves == 0
    assert app.start_time is None


def test_time_formatter():
    assert PatchesApp.format_time(65) == "1:05"


def draw(app, row, col):
    app.drag_start = (row, col)
    app.on_release(click_cell(app, row, col))


def test_undo_takes_back_the_move_it_undoes():
    app = make_app()
    draw(app, 0, 0)
    assert app.moves == 1
    app.on_key(FakeEvent(key="u"))
    assert app.moves == 0
    assert app.start_time is None


def test_undo_after_two_moves_leaves_one_move():
    app = make_app()
    draw(app, 0, 0)
    drone_2 = app.puzzle.drones[1]
    draw(app, drone_2.row, drone_2.col)
    assert app.moves == 2
    app.on_key(FakeEvent(key="u"))
    assert app.moves == 1
    assert app.start_time is not None


def test_undoing_a_removal_takes_back_its_move():
    app = make_app()
    draw(app, 0, 0)
    app.on_press(click_cell(app, 0, 0, button=3))
    assert app.moves == 2
    app.on_key(FakeEvent(key="u"))
    assert app.moves == 1


def test_undoing_a_reset_restores_the_move_count():
    app = make_app()
    draw(app, 0, 0)
    drone_2 = app.puzzle.drones[1]
    draw(app, drone_2.row, drone_2.col)
    app.on_key(FakeEvent(key="r"))
    assert app.moves == 0
    app.on_key(FakeEvent(key="u"))
    assert app.moves == 2
    assert app.start_time is not None


def test_undo_with_nothing_to_undo_keeps_the_moves():
    app = make_app()
    app.on_key(FakeEvent(key="u"))
    assert app.moves == 0
    assert app.message == "Nothing to undo."


def test_rejected_placement_adds_no_stats_step():
    app = make_app()
    draw(app, 1, 1)  # no seed here
    assert app.stats_history == []
