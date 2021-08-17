from discord.ext import commands
from discord import Embed
from discord.ext.commands.errors import MissingPermissions

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
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return

        #If no lobby
        if not self.bot.game_state.in_lobby:
            self.bot.dispatch("sendReply",ctx,"No lobby currently active. !liarsdice or !connect4 to start one.")
            return

        if self.bot.game_state.in_game:
            self.bot.dispatch("sendReply",ctx,f"A game of {self.bot.prettyGames[self.bot.game_state.game_type]} is already running.")
            return

        if ctx.author in self.bot.game_state.game_players:
            reply = f"`{ctx.author.display_name}`, you're already in the lobby."
            self.bot.dispatch("sendReply",ctx,reply)
            return 

        game_cog = self.bot.get_cog(self.bot.game_state.game_type+"_game")
        if game_cog.lobby_capacity_check_join():
            self.bot.game_state.add_player(ctx.author)
            gamePlayersPretty = ["`" + player.display_name + "`" for player in self.bot.game_state.game_players]
            self.bot.dispatch("log",f"lobby: {ctx.author} joined {self.bot.game_state.game_type} lobby")
            reply = f"`{ctx.author.display_name}` joined the {self.bot.prettyGames[self.bot.game_state.game_type]} lobby. Currently waiting: {', '.join(gamePlayersPretty)}"
        else:
            reply = self.bot.get_cog(self.bot.game_state.game_type+"_game").lobby_capacity_fail_message()

        self.bot.dispatch("sendReply",ctx,reply)

    @commands.command(name="game",help="Start a game {gamename}")
    async def game(self,ctx, game:str = "help"):
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return

        #If no lobby
        if self.bot.game_state.in_lobby:
            self.bot.dispatch("sendReply",ctx,"Can't start a new lobby, one is already open.")
            return

        if self.bot.game_state.in_game:
            self.bot.dispatch("sendReply",ctx,f"A game of {self.bot.prettyGames[self.bot.game_state.game_type]} is already running.")
            return

        if game == "help":
            embed = Embed()
            embed.add_field(name="Supported Games",value="\n".join([i for i in self.bot.prettyGames]))
            await ctx.send(embed=embed)
            return            

        match = [i for i in self.bot.prettyGames if game in i]
        if len(match) == 1:            
            self.bot.game_state.start_lobby(match[0])
            self.bot.game_state.game_players.append(ctx.author)
            self.bot.timer.create_timer("lobbytimer",self.bot.lobbyTimeout,[ctx])
            self.bot.dispatch("log",f"lobby: {ctx.author} created {match[0]} lobby.")
            self.bot.dispatch("sendReply",ctx,f"`{ctx.author.display_name}` wants to play {self.bot.prettyGames[self.bot.game_state.game_type]}. !join to enter the lobby. Currently waiting: `{ctx.author.display_name}`")
            return

        self.bot.dispatch("sendReply",ctx,f"game not found.")


    #start
    @commands.command(name="start",help="Start the currently open game lobby")
    async def start(self,ctx):
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return

        #Check lobby is running & starter is lobby creator
        if not self.bot.game_state.in_lobby:
            self.bot.dispatch("sendReply",ctx,"No lobby to start.")
            return
        if ctx.author != self.bot.game_state.game_players[0]:
            self.bot.dispatch("sendReply",ctx,"Only the user that created the lobby can start it!")
            return

        game_cog = self.bot.get_cog(self.bot.game_state.game_type+"_game")

        if not game_cog.lobby_capacity_check_start():
            self.bot.dispatch("sendReply",ctx,game_cog.lobby_capacity_fail_message())
            return
        
        self.bot.game_state.start_game(game_cog.get_game_class(self.bot.game_state.game_players))
        self.bot.timer.clear()
        self.bot.dispatch("log",f"{self.bot.game_state.game_type}: game started by {ctx.author} with players:{','.join(i.name for i in self.bot.game_state.game_players[1:])}")
        game_cog.on_game_start(ctx)
        return
    
    #kill_lobby
    @commands.command(name="cancel",help="Close the currently open game lobby\nLobby will automatically time out after 5 minutes.")
    async def kill_lobby(self,ctx):
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return
                
        if ctx.bot == True:
            reply = f"{self.bot.prettyGames[self.bot.game_state.game_type]} lobby timed out."
            self.bot.dispatch("log",f"{self.bot.game_state.game_type} lobby timed out.")
        else:
            if self.bot.game_state.in_lobby:
                if ctx.author == self.bot.game_state.game_players[0]:
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