"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

from protorpc import messages
from google.appengine.ext import ndb
import json


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""

    player_one = ndb.KeyProperty(required=True, kind='User')
    player_two = ndb.KeyProperty(required=True, kind='User')
    winner = ndb.KeyProperty(required=False, kind='User')
    freak_factor = ndb.IntegerProperty(required=True)
    rows = ndb.IntegerProperty(required=True)
    cols = ndb.IntegerProperty(required=True)
    winning_length = ndb.IntegerProperty(required=True)
    whos_turn = ndb.IntegerProperty(required=True, default=1)
    board = ndb.JsonProperty(required=True)
    game_over = ndb.BooleanProperty(required=True, default=False)

    @classmethod
    def new_game(cls, player_one, player_two, freak_factor):
        """Creates and returns a new game"""

        if freak_factor % 3 == 0:
            rows = 5
            cols = 5
        elif freak_factor % 2 == 0:
            rows = 4
            cols = 4
        else:
            rows = 3
            cols = 3

        # Freak factor >= 10 means take the smallest axis and make that
        # the winning length
        if freak_factor >= 10:
            winning_length = min(rows, cols)
        else:
            winning_length = 3

        # Build a board representation
        board = []
        for i in range(0, rows):

            row = []
            for j in range(0, cols):
                row.append(0)

            board.append(row)

        game = Game(player_one=player_one,
                    player_two=player_two,
                    winner=None,
                    freak_factor=freak_factor,
                    rows=rows,
                    cols=cols,
                    winning_length=winning_length,
                    whos_turn=1,
                    board=board,
                    game_over=False)
        game.put()
        return game

    def move(self, row, col):

        board = self.board

        if row + 1 > len(board) or col + 1 > len(board[0]):
            raise ValueError("You can not move here. That's not even a spot on the board!")

        if board[row][col] != 0:
            raise ValueError("You can not move here. This space is already taken!")

        board[row][col] = self.whos_turn
        self.board = board

        if self.check_did_win(self.whos_turn, row, col):
            self.winner = self.player_one if self.whos_turn == 1 else self.player_two
            if self.whos_turn == 1:
                self.end_game(self.player_one, self.player_two)
            else:
                self.end_game(self.player_two, self.player_one)
            return

        if self.check_is_draw():
            self.end_game()
            return

        if self.whos_turn == 1:
            self.whos_turn = 2
        else:
            self.whos_turn = 1

    def check_is_draw(self):

        for row in self.board:
            for col in row:
                if col != 1 and col != 2:
                    return False
        return True

    def check_did_win(self, last_move_user, last_move_row, last_move_col):

        # Check column win
        in_col = 0

        for col in range(0, self.cols):

            if self.board[last_move_row][col] != last_move_user:
                in_col = 0
            else:
                in_col += 1

            if in_col == self.winning_length:
                return True

            # Impossible to create line on this row
            if in_col + (self.cols - col) < self.winning_length:
                break

        # Check row win
        in_row = 0
        for row in xrange(0, self.rows):

            if self.board[row][last_move_col] != last_move_user:
                in_row = 0
            else:
                in_row += 1

            if in_row == self.winning_length:
                return True

            # Impossible to create line in this column
            if in_row + (self.rows - row) < self.winning_length:
                break

        # Check left diag win
        diff = abs(last_move_col - last_move_row)
        in_left_diag = 0
        for row in xrange(0, self.rows):

            col = diff + row
            if col < 0 or col >= self.cols:
                pass
            elif self.board[row][col] == last_move_user:
                in_left_diag += 1

                if in_left_diag == self.winning_length:
                    return True
            else:
                in_left_diag = 0

        # Check right diag win
        in_right_diag = 0

        for row in xrange(0, self.rows):

            col = self.cols - (diff + row)
            if col < 0 or col >= self.cols:
                pass
            elif self.board[row][col] == last_move_user:
                in_right_diag += 1

                if in_right_diag == self.winning_length:
                    return True

            else:
                in_right_diag = 0

        return False

    def to_form(self, message=""):
        """Returns a GameForm representation of the Game"""

        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.player_one_name = self.player_one.get().name
        form.player_two_name = self.player_two.get().name
        form.winner_name = self.winner.get().name if self.winner is not None else ""
        form.freak_factor = self.freak_factor
        form.rows = self.rows
        form.cols = self.cols
        form.winning_length = self.winning_length
        form.whos_turn = self.whos_turn
        form.board = json.dumps(self.board)
        form.game_over = self.game_over
        form.message = message
        return form

    def end_game(self, winner=None, loser=None):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.winner = winner

        if winner is not None:
            winner_score = Score.query(ancestor=winner).get()
            loser_score = Score.query(ancestor=loser).get()
            winner_score.wins += 1
            loser_score.losses += 1
            winner_score.put()
            loser_score.put()
        else:
            player_one_score = Score.query(ancestor=self.player_one).get()
            player_two_score = Score.query(ancestor=self.player_two).get()
            player_one_score.ties += 1
            player_two_score.ties += 1
            player_one_score.put()
            player_two_score.put()

        self.put()


class Score(ndb.Model):
    """Score object"""
    date = ndb.DateProperty(required=True, auto_now=True)
    wins = ndb.IntegerProperty(required=True)
    losses = ndb.IntegerProperty(required=True)
    ties = ndb.IntegerProperty(required=True)

    def to_form(self):

        player_name = self.key.parent().get().name
        return ScoreForm(player_name=player_name, wins=self.wins, losses=self.losses, ties=self.ties)


class GameHistory(ndb.Model):

    """Game History Object"""
    history = ndb.PickleProperty(required=True, default=[])
    messages = ndb.PickleProperty(required=True, default=[])


class GameForm(messages.Message):
    """GameForm for outbound game state information"""

    urlsafe_key = messages.StringField(1, required=True)
    player_one_name = messages.StringField(2, required=True)
    player_two_name = messages.StringField(3, required=True)
    freak_factor = messages.IntegerField(4, required=True)
    rows = messages.IntegerField(5, required=True)
    cols = messages.IntegerField(6, required=True)
    winning_length = messages.IntegerField(7, required=True)
    whos_turn = messages.IntegerField(8, required=True)
    board = messages.StringField(9, required=True)
    game_over = messages.BooleanField(10, required=True)
    message = messages.StringField(11, required=True)
    winner_name = messages.StringField(12, required=False)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""

    player_one_name = messages.StringField(1, required=True)
    player_two_name = messages.StringField(2, required=True)
    freak_factor = messages.IntegerField(3, default=1)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    player_name = messages.StringField(1, required=True)
    move_row = messages.IntegerField(2, required=True)
    move_col = messages.IntegerField(3, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    player_name = messages.StringField(1, required=True)
    wins = messages.IntegerField(2, required=True)
    losses = messages.IntegerField(3, required=True)
    ties = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
