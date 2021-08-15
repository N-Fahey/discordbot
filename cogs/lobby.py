from discord.ext import commands
from discord.ext.commands.errors import MissingPermissions
from cogs.liarsdice_game import LiarsDice
from cogs.russianroulette_game import RussianRoulette
from cogs.connect4_game import connect4

#########################
#       Extension       #
#########################

class lobby(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    #########################
    #        COMMANDS       #
    #########################

    #join
    @commands.command(name="join",help="Join a currently open game lobby")
    async def join(self,ctx):
        #If no lobby
        if not self.bot.game_state.in_lobby:
            self.bot.dispatch("sendReply",ctx,"No lobby currently active. !liarsdice or !connect4 to start one.")
            return

        if self.bot.game_state.in_game:
            self.bot.dispatch("sendReply",ctx,f"A game of {self.bot.prettyGames[self.bot.game_state.game_type]} is already running.")
            return

        if self.bot.game_state.in_lobby:
            if ctx.author in self.bot.gamePlayers:
                reply = f"{ctx.author.display_name}, you're already in the lobby."
            elif self.bot.game_state.game_type == "connect4" and len(self.bot.gamePlayers) > 1: #Connect 4 exceptions
                reply = f"Sorry {ctx.author.display_name}, Connect 4 only supports 2 players."
            else:
                self.bot.gamePlayers.append(ctx.author)
                gamePlayersPretty = [player.display_name for player in self.bot.gamePlayers]
                self.bot.dispatch("log",f"lobby: {ctx.author} joined {self.bot.game_state.game_type} lobby")
                if self.bot.game_state.game_type == "connect4":
                    ctx.author = self.bot.gamePlayers[0]
                    await self.start(ctx)
                    return
                reply = f"{ctx.author.display_name} joined the {self.bot.prettyGames[self.bot.game_state.game_type]} lobby. Currently waiting: {', '.join(gamePlayersPretty)}"
            self.bot.dispatch("sendReply",ctx,reply)
        else: #Error handling
            raise RuntimeError("Invalid status code returned while trying to start liarsdice")
    
    #start
    @commands.command(name="start",help="Start the currently open game lobby")
    async def start(self,ctx):
        #Check lobby is running & starter is lobby creator
        if not self.bot.game_state.in_lobby:
            self.bot.dispatch("sendReply",ctx,"No lobby to start.")
            return
        if ctx.author != self.bot.gamePlayers[0]:
            self.bot.dispatch("sendReply",ctx,"Only the user that created the lobby can start it!")
            return

        #Liar's Dice lobby handling
        if self.bot.game_state.game_type == "liarsdice":
            if len(self.bot.gamePlayers) > 1:
                self.bot.game = LiarsDice(self.bot.gamePlayers)
                self.bot.game_state.in_lobby = False
                self.bot.game_state.in_game = True
                self.bot.timer.clear()
                self.bot.dispatch("log",f"liarsdice: game started by {ctx.author} with players:{','.join(i.name for i in self.bot.gamePlayers[1:])}")
                self.bot.dispatch("messageHands")
                reply = f"Starting Liar's Dice! {self.bot.game.better.mention}, place your bet."
            else:
                reply = "Can't start Liar's Dice with one player. Wait for someone else to join the lobby."


        #Russian Roulette lobby handling
        if self.bot.game_state.game_type == "russianroulette":
            if len(self.bot.gamePlayers) > 1:
                self.bot.game = RussianRoulette(self.bot.gamePlayers)
                self.bot.game_state.in_lobby = False
                self.bot.game_state.in_game = True
                self.bot.timer.clear()
                self.bot.dispatch("log",f"russianroulette: game started by {ctx.author} with players:{','.join(i.name for i in self.bot.gamePlayers[1:])}")
                reply = f"😐 🔫 Starting Russian Roulette! `{self.bot.game.players[self.bot.game.current_player].display_name}` has the weapon"
            else:
                reply = "Russian roulette player count must be between 1 and 6 players"





        #Connect 4 lobby handling
        elif self.bot.game_state.game_type == "connect4":
            if len(self.bot.gamePlayers) == 2:
                self.bot.game = connect4(self.bot.gamePlayers)
                self.bot.game_state.in_lobby = False
                self.bot.game_state.in_game = True
                self.bot.timer.clear()
                self.bot.dispatch("log",f"connect4: game started by {ctx.author} with opponent: {','.join(i.name for i in self.bot.gamePlayers[1:])}")
                self.bot.dispatch("publishBoard",ctx)
                reply = None
            else:
                reply = "2 players required to start Connect 4."
        else:
            raise RuntimeError(f"Didn't recognise game:{self.bot.game_state.game_type}. Does this game exist?")
        if reply is not None:
            self.bot.dispatch("sendReply",ctx,reply)
    
    #kill_lobby
    @commands.command(name="cancel",help="Close the currently open game lobby\nLobby will automatically time out after 5 minutes.")
    async def kill_lobby(self,ctx):
        if ctx.bot == True:
            reply = f"{self.bot.prettyGames[self.bot.game_state.game_type]} lobby timed out."
            self.bot.dispatch("log",f"{self.bot.game_state.game_type} lobby timed out.")
        else:
            if self.bot.game_state.in_lobby:
                if ctx.author == self.bot.gamePlayers[0]:
                    reply = f"{self.bot.prettyGames[self.bot.game_state.game_type]} lobby closed."
                    self.bot.dispatch("log",f"lobby: {self.bot.game_state.game_type} lobby killed by {ctx.author}.")
                    self.bot.timer.clear()
                else:
                    self.bot.dispatch("sendReply",ctx,"Only the user that created the lobby can end it!")
                    return


            else:
                reply = "No lobby active! Nothing to kill."
                return


        self.bot.game_state.end_game()
        self.bot.gamePlayers = []
        self.bot.dispatch("sendReply",ctx,reply)

    #########################
    #     COMMAND ERRORS    #
    #########################

    @kill_lobby.error
    async def kill_lobby_error(ctx,error):
        if isinstance(error, MissingPermissions):
            await ctx.send("You can't do that")

    #########################
    #    EVENT LISTENERS    #
    #########################

    @commands.Cog.listener()
    async def on_lobbytimer(self,ctx):
        ctx.bot = True
        await self.kill_lobby(ctx)
        
#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(lobby(bot))