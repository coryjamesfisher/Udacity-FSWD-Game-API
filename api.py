# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import taskqueue

from models import User, Game, Score, GameHistory
from models import StringMessage, NewGameForm, GameForm, GameForms, MakeMoveForm,\
    ScoreForms
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
CREATE_USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1), email=messages.StringField(2))
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1))

MEMCACHE_NUM_ACTIVE_GAMES = 'NUM_ACTIVE_GAMES'

@endpoints.api(name='tic_tac_toe', version='v1')
class TicTacToeApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=CREATE_USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        score_id = ndb.Model.allocate_ids(size=1, parent=user.key)[0]
        score_key = ndb.Key(Score, score_id, parent=user.key)
        score = Score(key=score_key, wins=0, losses=0, ties=0)
        score.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        player_one = User.query(User.name == request.player_one_name).get()
        player_two = User.query(User.name == request.player_two_name).get()
        if not player_one:
            raise endpoints.NotFoundException(
                'Player one "' + request.player_one_name + '" does not exist!'
            )

        if not player_two:
            raise endpoints.NotFoundException(
                'Player two "' + request.player_two_name + '" does not exist!'
            )

        try:
            game = Game.new_game(player_one.key, player_two.key, request.freak_factor)

        except ValueError:
            raise endpoints.BadRequestException('You two already have a game together')

        # Increment active count of games
        taskqueue.add(url='/tasks/increment_active_games')

        message = "Game created successfully"
        game_history = GameHistory(parent=game.key)
        game_history.history.append(game)
        game_history.messages.append(message)
        game_history.put()

        return game.to_form(message)

    @endpoints.method(request_message=GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        if (game.whos_turn == 1 and game.player_one.get().name != request.player_name) or \
            (game.whos_turn == 2 and game.player_two.get().name != request.player_name):
            return game.to_form('Please wait your turn!')

        try:
            game.move(request.move_row, request.move_col)
            game.put()

        except ValueError as error:
            return game.to_form(error.message)

        if game.game_over is True:
            taskqueue.add(url='/tasks/decrement_active_games')
            message = "Thank you for playing. The match has ended and you have won!"
        else:
            message = "Move accepted. Please wait for your next turn."

        game_history = GameHistory.query(ancestor=game.key).get()
        game_history.history.append(game)
        game_history.messages.append(message)
        game_history.put()

        return game.to_form(message)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_score',
                      http_method='GET')
    def get_user_score(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(ancestor=user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=ScoreForms,
                      path='user/rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        scores = Score.query().order(-Score.wins, -Score.ties, +Score.losses)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='user/games',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of the users active games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'User name is required')
        games = Game.query(ndb.AND(ndb.OR(Game.player_one == user.key, Game.player_two == user.key), Game.game_over == False))
        return GameForms(items=[game.to_form() for game in games])

    @endpoints.method(response_message=StringMessage,
                      path='games/active_games',
                      name='get_num_active_games',
                      http_method='GET')
    def get_num_active_games(self, request):
        """Get the cached average moves remaining"""
        cached_num_games = memcache.get(MEMCACHE_NUM_ACTIVE_GAMES)

        if isinstance(cached_num_games, int) == False:
            cached_num_games = Game.query(Game.game_over == False).count()
            memcache.set(MEMCACHE_NUM_ACTIVE_GAMES, cached_num_games)
            print cached_num_games
            print "had to query for cached games"
        else:
            print "already had cached_games"

        return StringMessage(message="Found " + str(cached_num_games) + " active games.")

    @endpoints.method(request_message=GAME_REQUEST,
                      response_message=StringMessage,
                      path='games/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='POST')
    def cancel_game(self, request):
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')

        if game.game_over is True:
            raise endpoints.ForbiddenException('You can not cancel this game as it is already over!')

        # Save the game.
        # A game with no winner and with game_over=True is a cancelled game.
        game.game_over = True
        game.put()

        return StringMessage(message="The game was cancelled successfully.")

    @endpoints.method(request_message=GAME_REQUEST,
                      response_message=GameForms,
                      path='games/{urlsafe_game_key}/history',
                      name='game_history',
                      http_method='GET')
    def game_history(self, request):

        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')

        game_history = GameHistory.query(ancestor=game.key).get()

        items = []
        for index, item in enumerate(game_history.history):
            items.append(item.to_form(game_history.messages[index]))

        return GameForms(items=items)


    @staticmethod
    def increment_active_games():
        memcache.set(MEMCACHE_NUM_ACTIVE_GAMES, memcache.get(MEMCACHE_NUM_ACTIVE_GAMES) + 1)

    @staticmethod
    def decrement_active_games():
        memcache.set(MEMCACHE_NUM_ACTIVE_GAMES, memcache.get(MEMCACHE_NUM_ACTIVE_GAMES) - 1)


api = endpoints.api_server([TicTacToeApi])
