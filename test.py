from models import Game

# TODO figure out how to run this standalone
# Currently I have to copy+paste to Interactive Console
# To get the protorpc library to resolve

# Win Check
game = Game()
game.winning_length = 3
game.cols = 4
game.rows = 5
game.board = [[1, 0, 0, 0],
              [0, 1, 0, 0],
              [0, 0, 1, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0]]
game.whos_turn = 1
is_won = game.check_did_win(1, 2, 2)
is_draw = game.check_is_draw()

print '{} - {}'.format(is_won, is_draw)

assert is_won is True, "Game was supposed to be won but is not reflecting this"
assert is_draw is False, "Game was supposed to be won but is showing as a draw"

# Draw Check
game = Game()
game.winning_length = 5
game.cols = 4
game.rows = 5
game.board = [[1, 2, 1, 2],
              [2, 1, 2, 1],
              [1, 2, 1, 2],
              [2, 1, 2, 1],
              [1, 2, 1, 2]]
game.whos_turn = 1
is_won = game.check_did_win(1, 2, 2)
is_draw = game.check_is_draw()

print '{} - {}'.format(is_won, is_draw)

assert is_won is False,\
    "Game was supposed to be a draw and is showing that a player won"

assert is_draw is True,\
    "Game was supposed to be a draw and is not reflecting this"
