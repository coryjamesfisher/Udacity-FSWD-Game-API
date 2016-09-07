#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""

import webapp2
from google.appengine.api import mail, app_identity
from api import TicTacToeApi

from models import Game


class SendReminderEmail(webapp2.RequestHandler):

    @staticmethod
    def get():
        """Send a reminder email to the user who's turn it is for each game that is active.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()

        # Get all in progress games
        games = Game.query(Game.game_over == False)
        for game in games:

            # Get first player or second player based on whos turn
            if game.whos_turn == 1:
                user = game.player_one.get()
            else:
                user = game.player_two.get()

            # If the user has an email send them a little reminder
            if user.email is not None:
                subject = 'Freaky TicTacToe Reminder'
                body = 'Hello {}, it is currently your turn in the game [ {} ]. Please return to the game.' \
                    .format(user.name, game.key.urlsafe())
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                               user.email,
                               subject,
                               body)


class IncrementActiveGames(webapp2.RequestHandler):

    @staticmethod
    def post():
        TicTacToeApi.increment_active_games()


class DecrementActiveGames(webapp2.RequestHandler):

    @staticmethod
    def post():
        TicTacToeApi.decrement_active_games()


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/increment_active_games', IncrementActiveGames),
    ('/tasks/decrement_active_games', DecrementActiveGames)
], debug=True)
