from random import randint
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument

#########################
#       Game Class      #
#########################

class RussianRoulette:
    def __init__(self, players:list):
        if len(players) <2:
            raise ValueError("Russian Roulette requires 2 or more players")

        self.players = players
        self.players_who_have_rerolled = []
        self.current_player = 0
        self.unlucky_chamber = randint(0,5)
        
    def get_current_weapon_holder(self):
        return self.players[self.current_player % len(self.players)]
    
    def handle_pull(self,player):
        if player != self.get_current_weapon_holder():
            return "not_holder"
        
        if self.current_player % 6 == self.unlucky_chamber:
            self.players.remove(player)
            if len(self.players) > 1:
                #Continue the game
                self.unlucky_chamber = randint(0,5)
                return "dead"
            else:
                #Return the winner
                return self.players[0]
        else:
            self.current_player += 1
            return "continue"
    
    def handle_spin(self,player):
        if player != self.get_current_weapon_holder():
            return "not_holder"

        if player in self.players_who_have_rerolled:
            return "already_spun"
        
        self.players_who_have_rerolled.append(player)
        self.unlucky_chamber = randint(0,5)
        self.current_player += 1
        return True

#########################
#       Extension       #
#########################            

class russianroulette_game(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    #########################
    #        COMMANDS       #
    #########################

    @commands.command("pull", help="Fire the weapon")
    async def pull(self,ctx):
        #If lobby or running game, stop
        if not self.bot.game_state.in_game or self.bot.game_state.game_type != "russianroulette":
            self.bot.dispatch("sendReply",ctx,"No game of Russian Roulette is active.")
            return

        pull_result = self.bot.game.handle_pull(ctx.author)
        if pull_result == "not_holder":
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you don't currently have the revolver")
            return
        elif pull_result == "dead":
            self.bot.dispatch("sendReply",ctx,f"⚰️ `{ctx.author.display_name}` shot himself with the revolver ⚰️")
            self.bot.dispatch("sendReply",ctx,f"🔫 revolver cylinder spun... 😐 🔫 `{self.bot.game.get_current_weapon_holder().display_name}` now holds the revolver.")
            return
        elif pull_result == "continue":
            self.bot.dispatch("sendReply",ctx,f"😐 🔫 `{self.bot.game.get_current_weapon_holder().display_name}` now holds the revolver ")
            return
        else:
            self.bot.dispatch("sendReply",ctx,f"⚰️ `{ctx.author.display_name}` shot himself with the revolver ⚰️")
            self.bot.dispatch("sendReply",ctx,f"🏆🏆 Russian roulette is over `{self.bot.game.players[0].display_name}` is the winner 🏆🏆")
            self.bot.dispatch("queryAddWin",[(self.bot.game_state.game_type ,self.bot.game.players[0].id)])
            self.bot.game_state.end_game()
            self.bot.gamePlayers = []
            self.bot.game = None

    @commands.command("spin", help="Spin the cylinder of the revolver")
    async def handle_click(self,ctx):
        #If lobby or running game, stop
        if not self.bot.game_state.in_game or self.bot.game_state.game_type != "russianroulette":
            self.bot.dispatch("sendReply",ctx,"No game of Russian Roulette is active.")
            return

        spin_result = self.bot.game.handle_spin(ctx.author)
        if spin_result == "not_holder":
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you don't currently have the revolver")
            return
        elif spin_result == "already_spun":
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you've already spun the cylinder")
            return
        else:
            self.bot.dispatch("sendReply",ctx,f"🔫 Cylinder spun.. `{self.bot.game.get_current_weapon_holder().display_name}` now holds the revolver")

    #russianroulette (Initiator)
    @commands.command(name="roulette", help="Start a game of Russian Roulette\n The lobby will close automatically after 5 minutes.")
    async def russianroulette(self, ctx):
        #If lobby or running game, stop
        if self.bot.game_state.in_lobby:
            self.bot.dispatch("sendReply",ctx,f"A lobby is already open. !join to enter the lobby.")
            return
        if self.bot.game_state.in_game:
            self.bot.dispatch("sendReply",ctx,f"A game is already running. Wait until it's finished to start another.")
            return

        if not self.bot.game_state.in_game:
            self.bot.game_state.in_lobby = True
            self.bot.game_state.game_type = "russianroulette"
            self.bot.gamePlayers.append(ctx.author)
            PlayersPretty = [player.display_name for player in self.bot.gamePlayers]
            self.bot.timer.create_timer("lobbytimer",self.bot.lobbyTimeout,[ctx])
            self.bot.dispatch("log",f"lobby: {ctx.author} created russianroulette lobby.")
            self.bot.dispatch("sendReply",ctx,f"`{ctx.author.display_name}` wants to play Russian Roulette. !join to enter the lobby. Currently waiting: {','.join(PlayersPretty)}")
        else: #Error handling
            raise RuntimeError("Invalid status code returned while trying to start liarsdice")

    #########################
    #     COMMAND ERRORS    #
    #########################


#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(russianroulette_game(bot))