from discord.ext import commands,timers
from discord import Embed,Member,Thread

#########################
#       Extension       #
#########################

class Lobby:
    def __init__(self,lobby_owner,game_type,bet):
        self.lobby_players = [lobby_owner]
        self.lobby_owner = lobby_owner
        self.in_game = False
        self.game_type = game_type
        self.game = None
        self.message = None
        self.timer = None
        if bet > 0:
            self.pot = {
                lobby_owner:bet
            }
        else:
            self.pot = None

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
        self.bot.get_lobby_from_owner = self.get_lobby_from_owner
        self.bot.get_member_lobby = self.get_member_lobby
        self.bot.lobby_end_game = self.lobby_end_game
        self.bot.round_timer_reset = self.round_timer_reset
        self.bot.check_wrong_channel = self.check_wrong_channel

    def get_member_lobby(self,member):
        for lobby in self.bot.game_lobbies:
            if lobby.has_member(member):
                return lobby

        return None

    def get_lobby_from_owner(self,lobby_owner):
        for lobby in self.bot.game_lobbies:
            if lobby.lobby_owner == lobby_owner:
                return lobby

        return None

    def check_wrong_channel(self,lobby,channel):
        if hasattr(lobby,'thread') and channel != lobby.thread:
            return f"Game commands only work in the correct thread. Try again here:{lobby.thread.mention}"
    
    async def lobby_end_game(self,lobby,winner):
        pot = None
        sql_cog = self.bot.get_cog('sql')

        if lobby.pot is not None: #If betting is enabled for the lobby...            
            if winner is None:
                #Return the pot if there is no winner
                log_msg = f"lobby: {lobby.lobby_owner.name}'s {lobby.game_type} lobby closing without winner. Returning bets."
                for member,pot_amount in lobby.pot.items():
                    await sql_cog.queryPay([(pot_amount,member.id)])
            else:
                #Otherwise - pay full pot to the winner & log win in db
                pot = sum(lobby.pot.values())
                await sql_cog.queryPay([(pot,winner.id)])
                log_msg = f"lobby: {lobby.lobby_owner.name}'s {lobby.game_type} lobby closing with winner: {winner.name}"
                self.bot.dispatch("queryAddWin",[(lobby.game_type,winner.id,pot)])   

        else: #Betting disabled lobby. Still log to db if there's a winner
            if winner is not None:
                log_msg = f"lobby: {lobby.lobby_owner.name}'s {lobby.game_type} lobby closing with winner: {winner.name}"
                self.bot.dispatch("queryAddWin",[(lobby.game_type,winner.id,pot)])
            else:
                log_msg = f"lobby: {lobby.lobby_owner.name}'s {lobby.game_type} lobby closing without winner."

        self.bot.dispatch("log",log_msg)
        if lobby.message is not None:
            await lobby.message.edit(embed=self.get_lobby_embed_message(lobby,closed=True))
        if hasattr(lobby,'thread'):
            await lobby.thread.edit(archived=True,name=lobby.thread.name+' [CLOSED]',locked=True)
        lobby.timer.clear()
        self.bot.game_lobbies.remove(lobby)

    def get_lobby_embed_message(self,lobby, closed=False):
        embed = Embed(title=f"{lobby.lobby_owner.display_name} wants to play {self.bot.prettyGames[lobby.game_type]}")
        embed.set_thumbnail(url=lobby.lobby_owner.avatar.url)
        embed.add_field(name='Game',value=self.bot.prettyGames[lobby.game_type])
        embed.add_field(name='Owner',value=lobby.lobby_owner.mention)
        if not closed:
            embed.add_field(name='State',value="Waiting for players..." if not lobby.in_game else "In Game")
            if lobby.pot is None:
                player_list = ', '.join("`"+i.name+"`" for i in lobby.lobby_players)
                embed.add_field(name='Players',value=player_list if len(player_list) > 0 else "None",inline=False)
                embed.add_field(name='Instructions',value=f"If you want to join the lobby type !join {lobby.lobby_owner.mention}",inline=False)
            else:
                player_list = '\n'.join(f'[{self.bot.currencyCode}' + str(lobby.pot[i]) + '] `' + i.name + '`' for i in lobby.lobby_players)
                embed.add_field(name='[Bet] Player',value=player_list if len(player_list) > 0 else "None",inline=False)
                embed.add_field(name='Instructions',value=f"If you want to join the lobby type !join {lobby.lobby_owner.mention} [bet]",inline=False)
        else:
            embed.add_field(name='State',value="Closed")
            if lobby.pot is None:
                embed.add_field(name='Closed',value=f"Lobby is now closed.",inline=False)
            else:
                embed.add_field(name='Closed',value=f"Lobby is now closed. All bets have been returned.",inline=False)
        return embed

    def round_timer_reset(self,player,lobby,channel):
        if lobby.pot is not None:
            round_time = self.bot.round_timers[lobby.game_type]
            timer = lobby.timer
            timer.clear()
            timer.create_timer("timer_warning",round_time - self.bot.round_timers['seconds_warning'],[player,lobby,channel])

    #########################
    #        COMMANDS       #
    #########################
    #join
    @commands.command(name="join",help="Join a currently open game lobby")
    async def join(self,ctx, lobby_owner:Member="default", bet:int = 0):

        if not isinstance(ctx.channel,Thread) or ctx.channel.owner_id != self.bot.user.id:
            self.bot.dispatch("sendReply",ctx,"Game and lobby commands can only be used in a game thread.")
            return

        member_lobby = self.get_member_lobby(ctx.author)
        #If in lobby
        if member_lobby:
            self.bot.dispatch("sendReply",ctx,"You're already in a lobby!")
            return        

        if not lobby_owner:
            self.bot.dispatch("sendReply",ctx,"lobby not found")
            return
        
        lobby_to_join = None

        if lobby_owner == "default" and len(self.bot.game_lobbies) == 1:
            lobby_to_join = self.bot.game_lobbies[0]

        else:
            lobby_to_join = self.get_lobby_from_owner(lobby_owner)

        if msg := self.bot.check_wrong_channel(lobby_to_join,ctx.channel):
            self.bot.dispatch("sendReply",ctx,msg)
            return
        
        if not lobby_to_join:
            self.bot.dispatch("sendReply",ctx,"lobby not found")
            return

        if lobby_to_join.in_game:
            self.bot.dispatch("sendReply",ctx,"Can't join a running game")
            return

        game_cog = self.bot.get_cog(lobby_to_join.game_type+"_game")

        if game_cog.lobby_capacity_check_join(lobby_to_join.lobby_players):
            if lobby_to_join.pot is None:
                lobby_to_join.lobby_players.append(ctx.author)
                self.bot.dispatch("log",f"lobby: {ctx.author} joined {lobby_to_join.game_type} lobby")
                await lobby_to_join.message.edit(embed=self.get_lobby_embed_message(lobby_to_join)) 
            else:
                if bet >= lobby_to_join.pot[lobby_to_join.lobby_owner]:
                    sql_cog = self.bot.get_cog('sql')
                    if await sql_cog.queryWithdraw([(bet,ctx.author.id)]):
                        lobby_to_join.lobby_players.append(ctx.author)
                        lobby_to_join.pot[ctx.author] = bet
                        self.bot.dispatch("log",f"lobby: {ctx.author} joined {lobby_to_join.game_type} lobby with bet: {bet}")
                        await lobby_to_join.message.edit(embed=self.get_lobby_embed_message(lobby_to_join))
                    else:
                        self.bot.dispatch("sendReply",ctx,"You don't have enough money to do that!")
                else:
                    self.bot.dispatch("sendReply",ctx,"Your bet must match or exceed the lobby owner's.")
        else:
            reply = self.bot.get_cog(lobby_to_join.game_type+"_game").lobby_capacity_fail_message()
            self.bot.dispatch("sendReply",ctx,reply)

    #Game starter
    @commands.command(name="game",help="Start a game. Usage: !game {gamename} optional:{bet_amount}\nIf not bet specified, game is played without betting")
    async def game(self,ctx, game:str = "help", bet:int = 0):
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return

        if self.get_member_lobby(ctx.author):
            self.bot.dispatch("sendReply",ctx,"Can't start a new lobby, you're already in one!")
            return 


        if game == "help":
            embed = Embed()
            embed.add_field(name="Usage",value="Use !game {gamename} to start a game without betting.\nUse !game {gamename} {bet_amount} to start with betting enabled.")
            embed.add_field(name="Supported Games",value="\n".join([i for i in self.bot.prettyGames]),inline=False)
            await ctx.send(embed=embed)
            return


        match = [i for i in self.bot.prettyGames if game in i]
        if len(match) == 1:
            if bet > 0:
                sql_cog = self.bot.get_cog('sql')
                if not await sql_cog.queryWithdraw([(bet,ctx.author.id)]):
                    self.bot.dispatch("sendReply",ctx,"You don't have enough money to do that!")
                    return
            else:
                bet = 0
            
            lobby = Lobby(ctx.author,match[0],bet)
            lobby.timer = timers.TimerManager(self.bot)
            lobby.timer.create_timer("lobbytimer",self.bot.lobbyTimeout,[lobby])
            self.bot.game_lobbies.append(lobby)
            if lobby.game_type.endswith('_sp'):
                lobby.message = None
                await self.start(ctx)
                return
            self.bot.dispatch("log",f"lobby: {ctx.author} created {match[0]} lobby.")
            lobby.message = await ctx.send(embed=self.get_lobby_embed_message(lobby)) 
            lobby.thread = await lobby.message.create_thread(name=f"[Game] {self.bot.prettyGames[match[0]]} - {ctx.author.display_name}",auto_archive_duration=60)
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
        
        if msg := self.bot.check_wrong_channel(member_lobby,ctx.channel):
            self.bot.dispatch("sendReply",ctx,msg)
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
        member_lobby.timer.clear()
        if member_lobby.message is not None:
            await member_lobby.message.edit(embed=self.get_lobby_embed_message(member_lobby)) 
        self.bot.dispatch("log",f"{member_lobby.game_type}: game started by {ctx.author} with players:{','.join(i.name for i in member_lobby.lobby_players[1:])}")
        await game_cog.on_game_start(ctx)
        return
    
    #Leave lobby
    @commands.command(name="leave",help="Leave the game lobby you're currently a member of")
    async def leave_lobby(self,ctx):

        member_lobby = self.get_member_lobby(ctx.author)

        if not member_lobby:
            self.bot.dispatch("sendReply",ctx,"You're not in a lobby")
            return
        
        if msg := self.bot.check_wrong_channel(member_lobby,ctx.channel):
            self.bot.dispatch("sendReply",ctx,msg)
            return

        if member_lobby.is_owner(ctx.author):
            self.bot.dispatch("sendReply",ctx,"You're the lobby owner! You can only leave by cancelling the lobby with !cancel.")
            return
        
        if member_lobby.pot is not None:
            sql_cog = self.bot.get_cog('sql')
            await sql_cog.queryPay([(member_lobby.pot.pop(ctx.author),ctx.author.id)])

        member_lobby.lobby_players.remove(ctx.author)  
        self.bot.dispatch("log",f"lobby: {ctx.author} left {member_lobby.game_type} lobby")
        if member_lobby.message is not None:
            await member_lobby.message.edit(embed=self.get_lobby_embed_message(member_lobby))

    #kill_lobby
    @commands.command(name="cancel",help="Close the currently open game lobby\nLobby will automatically time out after 5 minutes.")
    async def kill_lobby(self,ctx):

        member_lobby = self.get_member_lobby(ctx.author)
        
        if not member_lobby:
            self.bot.dispatch("sendReply",ctx,"You're not in a lobby")
            return
        
        if msg := self.bot.check_wrong_channel(member_lobby,ctx.channel):
            self.bot.dispatch("sendReply",ctx,msg)
            return

        if not member_lobby.is_owner(ctx.author):
            self.bot.dispatch("sendReply",ctx,"You're not the owner")
            return
        if member_lobby.in_game:
            self.bot.dispatch("sendReply",ctx,"Can't cancel a running game")
            return
        
        if member_lobby.pot is not None:
            sql_cog = self.bot.get_cog('sql')
            for member,pot_amount in member_lobby.pot.items():
                await sql_cog.queryPay([(pot_amount,member.id)])
        reply = f"`{member_lobby.lobby_owner.display_name}`'s {self.bot.prettyGames[member_lobby.game_type]} lobby closed."
        self.bot.dispatch("log",f"lobby: {member_lobby.game_type} lobby killed by {ctx.author}.")
        self.bot.dispatch("sendReply",ctx,reply)
        await self.lobby_end_game(member_lobby,None)

    #########################
    #    EVENT LISTENERS    #
    #########################

    @commands.Cog.listener()
    async def on_timer_warning(self,player,lobby,channel):
        timer = lobby.timer
        timer.clear()
        timer.create_timer("timer_boot",self.bot.round_timers['seconds_warning'],[player,lobby,channel])
        self.bot.dispatch("sendReply",channel,f"{player.mention}, you have {self.bot.round_timers['seconds_warning']} seconds left to end your round before being disqualified.")

    @commands.Cog.listener()
    async def on_timer_boot(self,player,lobby,channel):
        timer = lobby.timer
        timer.clear()
        game_cog = self.bot.get_cog(lobby.game_type+"_game")
        self.bot.dispatch("log",f"lobby: {player.name} removed from {lobby.lobby_owner.name}'s {lobby.game_type}")
        await game_cog.on_timer_dq(player,lobby,channel)

    @commands.Cog.listener()
    async def on_lobbytimer(self,member_lobby):
        self.bot.dispatch("log",f"lobby: {member_lobby.game_type} lobby timed out.")
        self.bot.dispatch("sendReply",member_lobby.message.channel,f"{member_lobby.lobby_owner.mention}'s {self.bot.prettyGames[member_lobby.game_type]} lobby timed out.")
        await self.lobby_end_game(member_lobby,None)

    #########################
    #    COMMAND ERRORS     #
    #########################

    @join.error
    async def join_error(self,ctx,error):
        if isinstance(error,commands.errors.MemberNotFound) and len(self.bot.game_lobbies) == 1 and self.bot.game_lobbies[0].pot is not None:
            try:
                await self.join(ctx,self.bot.game_lobbies[0].lobby_owner,int(error.argument))
                return
            except:
                pass
            self.bot.dispatch("sendReply",ctx,f"Invalid argument: `{error.argument}`. Please try again")
        
        
#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(lobby(bot))