from pypokerengine.api.game import setup_config, start_poker
from randomplayer import RandomPlayer
from raise_player import RaisedPlayer
from WinRatePlayer import WinRatePlayer
from new_mcts_agent import MCTSPlayerPlus
from short_stack import ShortStacked
#TODO:config the config as our wish
config = setup_config(max_round=500, initial_stack=10000, small_blind_amount=10)



# config.register_player(name="Rand", algorithm=RandomPlayer())
# config.register_player(name="Raise1", algorithm=RaisedPlayer())
# config.register_player(name="Raise2", algorithm=RaisedPlayer())
# config.register_player(name="MyPlayer", algorithm=WinRatePlayer())
config.register_player(name="MCTS", algorithm=MCTSPlayerPlus())
config.register_player(name="ShortStack", algorithm=ShortStacked())
game_result = start_poker(config, verbose=1)
