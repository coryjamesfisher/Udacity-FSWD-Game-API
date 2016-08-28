"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
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

        # @TODO CHECK FOR EXISTING GAME


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

        if self.whos_turn == 1:
            self.whos_turn = 2
        else:
            self.whos_turn = 1

        # TODO check gameover

    def to_form(self, message=""):
        """Returns a GameForm representation of the Game"""

        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.player_one_name = self.player_one.get().name
        form.player_two_name = self.player_two.get().name
        form.freak_factor = self.freak_factor
        form.rows = self.rows
        form.cols = self.cols
        form.winning_length = self.winning_length
        form.whos_turn = self.whos_turn
        form.board = json.dumps(self.board)
        form.game_over = self.game_over
        form.message = message
        return form

    def end_game(self, winner, loser):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()

        # winnerStats = UserStats(user=winner, won=True)
        # loserStats = UserStats(user=loser, won=False)
        #
        # winnerStats.put()
        # loserStats.put()
        #


        # Add the game to the score 'board'
        # score = Score(user=self.user, date=date.today(), won=won,
        #               guesses=self.attempts_allowed - self.attempts_remaining)
        # score.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses)


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
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
