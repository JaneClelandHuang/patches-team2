from patches.board import Board
from patches.puzzle import load_puzzle
from patches.rules import Rect

from test_rules import SAMPLE_SOLUTION


def make_board():
    return Board(load_puzzle("puzzles/sample.json"))


def test_place_assigns_to_the_contained_drone():
    board = make_board()
    assert board.place(SAMPLE_SOLUTION["drone_1"]) == "drone_1"
    assert board.region_at(0, 0) == "drone_1"


def test_place_rejects_region_with_no_seed_or_two_seeds():
    board = make_board()
    assert board.place(Rect(0, 0, 7, 7)) is None
    assert board.regions == {}


def test_new_region_replaces_overlapping_ones():
    board = make_board()
    board.place(SAMPLE_SOLUTION["drone_1"])
    board.place(SAMPLE_SOLUTION["drone_2"])
    # A region for drone_2 that overlaps drone_1's region wipes drone_1's.
    widened = Rect(0, 1, 4, 4)
    assert board.place(widened) == "drone_2"
    assert "drone_1" not in board.regions
    assert board.regions["drone_2"] == widened


def test_remove_and_reset():
    board = make_board()
    board.place(SAMPLE_SOLUTION["drone_1"])
    assert board.remove_at(1, 1) == "drone_1"
    assert board.remove_at(1, 1) is None
    board.place(SAMPLE_SOLUTION["drone_1"])
    board.reset()
    assert board.regions == {}


def test_full_solution_is_solved():
    board = make_board()
    for rect in SAMPLE_SOLUTION.values():
        board.place(rect)
    assert board.solved
    assert board.covered_cells() == 49


def test_place_then_undo_leaves_board_empty():
    board = make_board()
    board.place(SAMPLE_SOLUTION["drone_1"])
    assert board.undo() is True
    assert board.regions == {}


def test_undo_brings_back_regions_a_placement_replaced():
    board = make_board()
    board.place(SAMPLE_SOLUTION["drone_1"])
    board.place(SAMPLE_SOLUTION["drone_2"])
    before = dict(board.regions)
    board.place(Rect(0, 1, 4, 4))  # replaces drone_1's region
    assert "drone_1" not in board.regions
    assert board.undo() is True
    assert board.regions == before


def test_remove_then_undo_restores_the_region():
    board = make_board()
    board.place(SAMPLE_SOLUTION["drone_1"])
    board.remove_at(1, 1)
    assert board.undo() is True
    assert board.regions == {"drone_1": SAMPLE_SOLUTION["drone_1"]}


def test_reset_then_undo_restores_previous_regions():
    board = make_board()
    board.place(SAMPLE_SOLUTION["drone_1"])
    board.place(SAMPLE_SOLUTION["drone_2"])
    before = dict(board.regions)
    board.reset()
    assert board.undo() is True
    assert board.regions == before


def test_undo_on_fresh_board_returns_false():
    board = make_board()
    assert board.undo() is False
    assert board.regions == {}


def test_rejected_placement_and_no_op_changes_add_no_history():
    board = make_board()
    board.place(Rect(0, 0, 7, 7))  # no single seed
    board.remove_at(1, 1)          # nothing there
    board.reset()                  # already empty
    assert board.undo() is False


def test_placing_the_same_region_again_adds_no_history_step():
    board = make_board()
    board.place(SAMPLE_SOLUTION["drone_1"])
    board.place(SAMPLE_SOLUTION["drone_1"])
    assert board.undo() is True
    assert board.regions == {}
    assert board.undo() is False
