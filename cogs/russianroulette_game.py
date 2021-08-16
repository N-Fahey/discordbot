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
        
    def get_current_weapon_holder_idx(self):
        return self.current_player % len(self.players)

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
    async def handle_pull(self,ctx):
        #If lobby or running game, stop
        if not self.bot.game_state.in_game or self.bot.game_state.game_type != "russianroulette":
            self.bot.dispatch("sendReply",ctx,"No game of Russian Roulette is active.")
            return

        if ctx.author != self.bot.game.players[self.bot.game.get_current_weapon_holder_idx()]:
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you don't currently have the revolver")
            return  

        if self.bot.game.current_player % 6 == self.bot.game.unlucky_chamber:
            self.bot.dispatch("sendReply",ctx,f"⚰️ `{ctx.author.display_name}` shot himself with the revolver ⚰️")
            self.bot.game.players.remove(ctx.author)

            # if there are still active players
            if len(self.bot.game.players) < 2:
                self.bot.dispatch("sendReply",ctx,f"🏆🏆 Russian roulette is over `{self.bot.game.players[0].display_name}` is the winner 🏆🏆")
                self.bot.dispatch("queryAddWin",[(self.bot.game_state.game_type ,self.bot.game.players[0].id)])
                self.bot.game_state.end_game()
                self.bot.gamePlayers = []
                return
          
            self.bot.game.unlucky_chamber = randint(0,5)
            self.bot.dispatch("sendReply",ctx,f"🔫 revolver cylinder spun..")
        else:
            self.bot.game.current_player += 1

        self.bot.dispatch("sendReply",ctx,f"😐 🔫 `{self.bot.game.players[self.bot.game.get_current_weapon_holder_idx()]}` now holds the revolver ")



    @commands.command("spin", help="Spin the cylinder of the revolver")
    async def handle_click(self,ctx):
        #If lobby or running game, stop
        if not self.bot.game_state.in_game or self.bot.game_state.game_type != "russianroulette":
            self.bot.dispatch("sendReply",ctx,"No game of Russian Roulette is active.")
            return

        if ctx.author != self.bot.game.players[self.bot.game.get_current_weapon_holder_idx()]:
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you don't currently have the revolver")
            return  

        if self.bot.game.get_current_weapon_holder_idx() in self.bot.game.players_who_have_rerolled:
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you've already spun the cylinder")
            return
        
        self.bot.game.players_who_have_rerolled.append(self.bot.game.get_current_weapon_holder_idx())
        self.bot.game.unlucky_chamber = randint(0,5)
        self.bot.game.current_player += 1
        self.bot.dispatch("sendReply",ctx,f"🔫 Cylinder spun.. `{self.bot.game.players[self.bot.game.get_current_weapon_holder_idx()]}` now holds the revolver")



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