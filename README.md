#FSND Extreme Tic Tac Toe API

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 
 
 
##Game Description:
Extreme Tic-Tac-Toe is a small twist on a classic two player game. In each game
players take turns marking a spot in a 2 dimensional grid. Traditionally the grids
are 3 x 3 and it takes a player placing their mark on either a full row, column,
left diagonal, or right diagonal to win the game. When a game board is filled with
neither player having achieved the winning criteria the game is declared a draw. The
only difference with extreme tic-tac-toe is that a freak factor is added which impacts
both the size of the board and the number of marks in a sequence required to win the game.

The rules based on freak factor are as follows.
Grid Size Rules:
freak_factor divisible by 3: 5 x 5 grid
freak_factor divisible by 2: 4 x 4 grid
freak_factor 0 or 1: 3 x 3 grid

Winning Sequence Count Rules:
freak_factor >= 10: Number of marks equal to the lowest between row and column length
(this is designed with rectangular grids in mind)
freak_factor < 10: 3 marks

Score Rules:
The game records wins, losses, and draws for each user.
Users are ranked via the following algorithm:
wins descending, losses descending, draws ascending.
This is such that 2 users with the same win ratio can be ranked based on secondary
and tertiary criteria. If all of the 3 factors match then the order will not be guaranteed
and either user may be reported as ranked above the other until another game has been
played.

##Game Order of Operations:
Players must first register with an email address and name using
the /user endpoint prior to playing a game. Once two players have been
created a game can be started by calling the new_game endpoint with both
users' names and a freak factor. Keep track of the urlsafe_game_key for subsequent calls.
After that users will take turns making moves by posting to the game/{urlsafe_game_key} endpoint
the row and column of the move and their name. That endpoint will return the current state of the game
which you may also retreive at any time by querying the game/{urlsafe_game_key} endpoint.
Once a user has created a sequence of the winning length or if all moves are exhausted and
the game is a draw the game_over flag will be set and no further moves can be made.
The wins/losses are recorded for each user and are retrievable by querying
the scores/user/{user_name} endpoint for a single user's score or the user/rankings endpoint for
the entire list ordered by ranking.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: player_one_name, player_two_name, freak_factor
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. player_one_name & player_two_name provided must correspond to an
    existing user - will raise a NotFoundException if not. freak_factor must be an integer.
    Also adds a task to a task queue to increment the number of active games.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, player_name, move_row, move_col
    - Returns: GameForm with new game state.
    - Description: Accepts a move from the player who's turn it is and
    returns the updated state of the game. Raises a ValueError if the move is invalid.
    Also adds a task to a task queue to decrement the number of active games
    if the game has ended. Note: All move history is recorded so that a game
    could be replayed turn by turn.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_user_rankings**
    - Path: 'user/rankings'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns user scores in order from highest to lowest.
    
 - **get_user_games**
    - Path: 'user/games'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms
    - Description: Returns all of users active games.
    
 - **get_num_active_games**
    - Path: 'games/active_games'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the number of active games from a previously cached memcache key.
    
 - **cancel_game**
    - Path: 'games/{urlsafe_game_key}/cancel'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: Cancels an active game that has not been completed.
    Adds a task to the taskqueue to decrement number of active games.
    Raises a NotFoundException if the game does not exist.
    Raises a ForbiddenException if the game is already over.
    
 - **game_history**
    - Path: 'games/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForms
    - Description: Returns the history of a game as an array of GameForms.
    Raises a NotFoundException if the game does not exist.
    
##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via player_one_name and player_two_name.
    
 - **Score**
    - Records completed games. Associated with Users model by ancestry.
    
 - **Game History**
    - Records the state of the game over time. Associated with game by ancestry.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, player_one_name, player_two_name, freak_factor,
    rows, cols, winning_length, whos_turn, board, game_over, message, winner_name).
 - **GameForms**
    - Multiple GameForm container.
 - **NewGameForm**
    - Used to create a new game (player_one_name, player_two_name, freak_factor)
 - **MakeMoveForm**
    - Inbound make move form (player_name, move_row, move_col).
 - **ScoreForm**
    - Representation of a completed game's Score (player_name, wins, losses, ties).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.