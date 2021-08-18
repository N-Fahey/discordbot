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
            return self.remove_player(player)
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
    
    def remove_player(self,player):
        self.players.remove(player)
        if len(self.players) > 1:
            #Continue the game
            self.unlucky_chamber = randint(0,5)
            return "dead"
        else:
            #Return the winner
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
    
    async def on_timer_dq(self,ctx,lobby):
        remove_outcome = lobby.game.remove_player(ctx.author)
        if remove_outcome == "dead":
            self.bot.dispatch("sendReply",ctx,f"⚰️ `{ctx.author.display_name}` shot himself with the revolver ⚰️")
            self.bot.dispatch("sendReply",ctx,f"🔫 revolver cylinder spun... 😐 🔫 `{lobby.game.get_current_weapon_holder().display_name}` now holds the revolver.")
        else:
            self.bot.dispatch("sendReply",ctx,f"⚰️ `{ctx.author.display_name}` shot himself with the revolver ⚰️")
            self.bot.dispatch("sendReply",ctx,f"🏆🏆 Russian roulette is over `{lobby.game.players[0].display_name}` is the winner 🏆🏆")
            self.bot.dispatch("queryAddWin",[(lobby.game_type ,lobby.game.players[0].id)])
            await self.bot.lobby_end_game(lobby,lobby.game.players[0])

    # on_game_start event
    def on_game_start(self,ctx):
        member_lobby = self.bot.get_member_lobby(ctx.author)
        self.bot.round_timer_reset(ctx,member_lobby)
        self.bot.dispatch("sendReply",ctx, f"😐 🔫 Starting Russian Roulette! `{member_lobby.game.players[member_lobby.game.current_player].display_name}` has the weapon")


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
            self.bot.dispatch("sendReply",ctx,f"⚰️ `{ctx.author.display_name}` shot himself with the revolver ⚰️")
            self.bot.dispatch("sendReply",ctx,f"🔫 revolver cylinder spun... 😐 🔫 `{member_lobby.game.get_current_weapon_holder().display_name}` now holds the revolver.")
            return
        elif pull_result == "continue":
            self.bot.dispatch("sendReply",ctx,f"😐 🔫 `{member_lobby.game.get_current_weapon_holder().display_name}` now holds the revolver ")
            return
        else:
            self.bot.dispatch("sendReply",ctx,f"⚰️ `{ctx.author.display_name}` shot himself with the revolver ⚰️")
            self.bot.dispatch("sendReply",ctx,f"🏆🏆 Russian roulette is over `{member_lobby.game.players[0].display_name}` is the winner 🏆🏆")
            self.bot.dispatch("queryAddWin",[(member_lobby.game_type ,member_lobby.game.players[0].id)])
            await self.bot.lobby_end_game(member_lobby,member_lobby.game.players[0])

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
            self.bot.dispatch("sendReply",ctx,f"🔫 Cylinder spun.. `{member_lobby.game.get_current_weapon_holder().display_name}` now holds the revolver")


    #########################
    #     COMMAND ERRORS    #
    #########################


#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(russianroulette_game(bot))