from models import Game

# TODO figure out how to run this standalone
# Currently I have to copy+paste to Interactive Console
# To get the protorpc library to resolve
game = Game()
game.winning_length = 3
game.cols = 4
game.rows = 5
game.board = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,0], [0,0,0,0]]
game.whos_turn = 1
gameover = game.check_game_over(1, 2, 2)

print gameover
