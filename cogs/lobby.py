from discord.ext import commands
from discord import Embed
from discord.ext.commands.errors import MissingPermissions

#########################
#       Extension       #
#########################

class Lobby:
    def __init__(self,lobby_owner,game_type):
        self.lobby_players = [lobby_owner]
        self.lobby_owner = lobby_owner
        self.in_game = False
        self.game_type = game_type
        self.game = None
        self.lobby_unique_id = "red"

        # you can include stuff like lobby betting pot in here


    def has_member(self,member):
        if member in self.lobby_players:
            return True
    
    def is_owner(self, member):
        return self.lobby_owner == member


    def start_game(self, game_object):
        self.in_game = True
        self.game = game_object


class lobby(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.bot.game_lobbies = []
        self.bot.get_lobby_from_uid = self.get_lobby_from_uid
        self.bot.get_member_lobby = self.get_member_lobby
        self.bot.lobby_end_game = self.lobby_end_game

    def get_member_lobby(self,member):
        for lobby in self.bot.game_lobbies:
            if lobby.has_member(member):
                return lobby

        return None

    def get_lobby_from_uid(self,uid):
        for lobby in self.bot.game_lobbies:
            if lobby.lobby_unique_id == uid:
                return lobby

        return None
    
    def lobby_end_game(self,lobby):
        self.bot.game_lobbies.remove(lobby)



    #########################
    #        COMMANDS       #
    #########################
    #join
    @commands.command(name="join",help="Join a currently open game lobby")
    async def join(self,ctx, lobby_uid="default"):

        member_lobby = self.get_member_lobby(ctx.author)
        #If no lobby
        if member_lobby:
            self.bot.dispatch("sendReply",ctx,"You're already in a lobby!")
            return

        if not lobby_uid:
            self.bot.dispatch("sendReply",ctx,"lobby not found")
            return
        
        lobby_to_join = None

        if lobby_uid == "default" and len(self.bot.game_lobbies) == 1:
            lobby_to_join = self.bot.game_lobbies[0]

        else:
            lobby_to_join = self.get_lobby_from_uid(lobby_uid)
    
        
        if not lobby_to_join:
            self.bot.dispatch("sendReply",ctx,"lobby not found")
            return

        if lobby_to_join.in_game:
            self.bot.dispatch("sendReply",ctx,"Can't join a running game")
            return


        game_cog = self.bot.get_cog(lobby_to_join.game_type+"_game")
        if game_cog.lobby_capacity_check_join(lobby_to_join.lobby_players):
            lobby_to_join.lobby_players.append(ctx.author)
            gamePlayersPretty = ["`" + player.display_name + "`" for player in lobby_to_join.lobby_players]
            self.bot.dispatch("log",f"lobby: {ctx.author} joined {lobby_to_join.game_type} lobby")
            reply = f"`{ctx.author.display_name}` joined the {self.bot.prettyGames[lobby_to_join.game_type]} lobby. Currently waiting: {', '.join(gamePlayersPretty)}"
        else:
            reply = self.bot.get_cog(lobby_to_join.game_type+"_game").lobby_capacity_fail_message()

        self.bot.dispatch("sendReply",ctx,reply)

    @commands.command(name="game",help="Start a game {gamename}")
    async def game(self,ctx, game:str = "help"):

        if self.get_member_lobby(ctx.author):
            self.bot.dispatch("sendReply",ctx,"Can't start a new lobby, you're already in one!")
            return 


        if game == "help":
            embed = Embed()
            embed.add_field(name="Supported Games",value="\n".join([i for i in self.bot.prettyGames]))
            await ctx.send(embed=embed)
            return          

          

        match = [i for i in self.bot.prettyGames if game in i]
        if len(match) == 1:
            lobby = Lobby(ctx.author,match[0])
            self.bot.game_lobbies.append(lobby)
            # self.bot.game_state.start_lobby(match[0])
            # self.bot.game_state.game_players.append(ctx.author)
            # self.bot.timer.create_timer("lobbytimer",self.bot.lobbyTimeout,[ctx])
            self.bot.dispatch("log",f"lobby: {ctx.author} created {match[0]} lobby.")
            self.bot.dispatch("sendReply",ctx,f"`{ctx.author.display_name}` wants to play {self.bot.prettyGames[lobby.game_type]}. !join to enter the lobby. Currently waiting: `{ctx.author.display_name}`")
            return

        self.bot.dispatch("sendReply",ctx,f"game not found.")


    #start
    @commands.command(name="start",help="Start the currently open game lobby")
    async def start(self,ctx):
        #Check lobby is running & starter is lobby creator

        member_lobby = self.get_member_lobby(ctx.author)
        if not member_lobby:
            self.bot.dispatch("sendReply",ctx,"You aren't part of any lobby. Please create a new one using the game command.")
            return 

        if not member_lobby.is_owner(ctx.author):
            self.bot.dispatch("sendReply",ctx,"Only the user that created the lobby can start it!")
            return

        if member_lobby.in_game:
            self.bot.dispatch("sendReply",ctx,"You can't start the lobby, it's already running a game!")
            return
        

        game_cog = self.bot.get_cog(member_lobby.game_type+"_game")

        if not game_cog.lobby_capacity_check_start(member_lobby.lobby_players):
            self.bot.dispatch("sendReply",ctx,game_cog.lobby_capacity_fail_message())
            return
        

        member_lobby.game = game_cog.get_game_class(member_lobby.lobby_players)
        member_lobby.in_game = True
        # self.bot.timer.clear()
        self.bot.dispatch("log",f"{member_lobby.game_type}: game started by {ctx.author} with players:{','.join(i.name for i in member_lobby.lobby_players[1:])}")
        game_cog.on_game_start(ctx)
        return
    
    #kill_lobby
    @commands.command(name="cancel",help="Close the currently open game lobby\nLobby will automatically time out after 5 minutes.")
    async def kill_lobby(self,ctx):
        if ctx.bot == True:
            # reply = f"{self.bot.prettyGames[self.bot.game_state.game_type]} lobby timed out."
            # self.bot.dispatch("log",f"{self.bot.game_state.game_type} lobby timed out.")
            pass
        else:
            member_lobby = self.get_member_lobby(ctx.author)
            if not member_lobby:
                self.bot.dispatch("sendReply",ctx,"You're not in a lobby")
                return
            if not member_lobby.is_owner(ctx.author):
                self.bot.dispatch("sendReply",ctx,"You're not the owner")
                return
            if member_lobby.in_game:
                self.bot.dispatch("sendReply",ctx,"Can't cancel a running game")
                return
            
            self.bot.game_lobbies.remove(member_lobby)
            reply = f"{self.bot.prettyGames[member_lobby.game_type]} [{member_lobby.lobby_unique_id}] lobby closed."
            self.bot.dispatch("log",f"lobby: {member_lobby.game_type} lobby killed by {ctx.author}.")
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