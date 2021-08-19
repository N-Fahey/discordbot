from random import randint
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument
from discord import Embed,Member

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
        self.event_list = [{"name": "begin"}]
        
    def get_current_weapon_holder(self):
        return self.players[self.current_player % len(self.players)]
    
    def handle_pull(self,player):
        if player != self.get_current_weapon_holder():
            return "not_holder"
        
        if self.current_player % 6 == self.unlucky_chamber:
            return self.remove_player(player)
        else:
            self.current_player += 1
            self.event_list.append({"name":"turn", "player":self.get_current_weapon_holder()})

            return "continue"
    
    def handle_spin(self,player):
        if player != self.get_current_weapon_holder():
            return "not_holder"

        if player in self.players_who_have_rerolled:
            return "already_spun"

        self.event_list.append({"name":"spin", "player":player})
        self.players_who_have_rerolled.append(player)
        self.unlucky_chamber = randint(0,5)
        self.current_player += 1
        self.event_list.append({"name":"turn", "player":self.get_current_weapon_holder()})
        return True
    
    def remove_player(self,player):
        self.players.remove(player)
        if len(self.players) > 1:
            #Continue the game
            self.unlucky_chamber = randint(0,5)
            self.event_list.append({"name":"dead", "player":player})
            self.event_list.append({"name":"turn", "player":self.get_current_weapon_holder()})
            return "dead"
        else:
            #Return the winner
            self.event_list.append({"name":"dead", "player":player})
            self.event_list.append({"name":"winner", "player": self.players[0]})
            self.event_list.append({"name":"end"})

            return self.players[0]

#########################
#       Extension       #
#########################            

class russianroulette_game(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    def get_game_class(self,players):
        return RussianRoulette(players)

    # Lobby Capacity Check
    def lobby_capacity_check_start(self, players):
        if len(players) > 1 and len(players) <= 6:
            return True
        return False
    
    def lobby_capacity_check_join(self, players):
        if len(players) > 5:
            return False
        return True
    
    # Message to send if lobby capacity check fails
    def lobby_capacity_fail_message(self):
        return "There must be between 2 and 6 players"

    async def on_timer_dq(self,player,lobby,channel):
        remove_outcome = lobby.game.remove_player(player) ### Check the reset timer event in this bit - timer should apply to next player
        if remove_outcome == "dead":
            lobby.game.message.edit(embed=self.get_embed(lobby))
            self.bot.round_timer_reset(lobby.game.get_current_weapon_holder(),lobby,lobby.game.message.channel)
        else:
            self.bot.dispatch("queryAddWin",[(lobby.game_type ,lobby.game.players[0].id)])
            if await lobby.game.message.edit(embed=self.get_embed(lobby)):
                await self.bot.lobby_end_game(lobby,lobby.game.players[0])

    # on_game_start event
    async def on_game_start(self,ctx):
        member_lobby = self.bot.get_member_lobby(ctx.author)
        self.bot.round_timer_reset(member_lobby.game.get_current_weapon_holder(),member_lobby,ctx.channel)
        member_lobby.game.event_list.append({"name":"turn", "player":member_lobby.game.get_current_weapon_holder()})
        member_lobby.game.message = await ctx.send(embed=self.get_embed(member_lobby))


    def roulette_event_to_emoji(self,event):

        if event['name'] == "begin":
            return f"⭐⭐ Round Begins ⭐⭐"
        if event['name'] == "end":
            return f"🎉🎉 Round Ends 🎉🎉"
        if event['name'] == "turn":
            return f"😐 🔫 {event['player'].display_name} now holds the revolver"
        if event['name'] == "spin":
            return f"↩️↩️↩️ {event['player'].display_name} spun the cylinder.."
        if event['name'] == "dead":
            return f"⚰️⚰️⚰️ {event['player'].display_name} shot himself with the revolver.."
        if event['name'] == "winner":
            return f"⭐⭐⭐ {event['player'].display_name}  was the last person standing!"
        if "player" in event:
            return event["name"] + " - " + event["player"].display_name

        return event["name"]

    def get_embed(self,member_lobby):
        embed = Embed(title=f"{member_lobby.lobby_owner.display_name}'s Russian Roulette Lobby")
        embed.add_field(name='Alive Players',value='\n'.join(i.display_name for i in member_lobby.lobby_players))
        event_list_parsed = '\n '.join(self.roulette_event_to_emoji(i) for i in member_lobby.game.event_list)
        embed.add_field(name='Current Move',value=self.roulette_event_to_emoji(member_lobby.game.event_list[len(member_lobby.game.event_list)-1]))
        embed.add_field(name='Game Log',value=event_list_parsed,inline=False)
        return embed

    #########################
    #        COMMANDS       #
    #########################

    @commands.command("pull", help="Fire the weapon")
    async def pull(self,ctx):
        #If lobby or running game, stop

        member_lobby = self.bot.get_member_lobby(ctx.author)

        if not member_lobby:
            self.bot.dispatch("sendReply",ctx,"You're not in a lobby.")
            return

        if not member_lobby.in_game or member_lobby.game_type != "russianroulette":
            self.bot.dispatch("sendReply",ctx,"You're not in a game of russian roulette.")
            return

        pull_result = member_lobby.game.handle_pull(ctx.author)

        if pull_result == "not_holder":
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you don't currently have the revolver")
            return        
        elif pull_result == "dead":
            await member_lobby.game.message.edit(embed=self.get_embed(member_lobby))
            await ctx.message.delete()
            self.bot.round_timer_reset(ctx,member_lobby)
            return
        elif pull_result == "continue":
            await member_lobby.game.message.edit(embed=self.get_embed(member_lobby))
            await ctx.message.delete()
            self.bot.round_timer_reset(ctx,member_lobby)
            return
        else:
            self.bot.dispatch("queryAddWin",[(member_lobby.game_type ,member_lobby.game.players[0].id)])
            await self.bot.lobby_end_game(member_lobby,member_lobby.game.players[0])
            await ctx.message.delete()

            if await member_lobby.game.message.edit(embed=self.get_embed(member_lobby)):
                await self.bot.lobby_end_game(member_lobby)

    @commands.command("spin", help="Spin the cylinder of the revolver")
    async def handle_click(self,ctx):
        member_lobby = self.bot.get_member_lobby(ctx.author)
        #If lobby or running game, stop

        if not member_lobby:
            self.bot.dispatch("sendReply",ctx,"You're not in a lobby.")
            return

        if not member_lobby.in_game or member_lobby.game_type != "russianroulette":
            self.bot.dispatch("sendReply",ctx,"You're not in a game of russian roulette.")
            return

        spin_result = member_lobby.game.handle_spin(ctx.author)
        if spin_result == "not_holder":
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you don't currently have the revolver")
            return
        elif spin_result == "already_spun":
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you've already spun the cylinder")
            return
        else:
            await member_lobby.game.message.edit(embed=self.get_embed(member_lobby))
            self.bot.round_timer_reset(ctx,member_lobby)
            await ctx.message.delete()
    #########################
    #     COMMAND ERRORS    #
    #########################


#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(russianroulette_game(bot))
