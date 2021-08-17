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

    def get_game_class(self,players):
        return RussianRoulette(players)

    # Lobby Capacity Check
    def lobby_capacity_check_start(self):
        if len(self.bot.game_state.game_players) > 1 and len(self.bot.game_state.game_players) <= 6:
            return True
        return False
    
    def lobby_capacity_check_join(self):
        if len(self.bot.game_state.game_players) > 5:
            return False
        return True
    
    # Message to send if lobby capacity check fails
    def lobby_capacity_fail_message(self):
        return "There must be between 2 and 6 players"


    # on_game_start event
    def on_game_start(self,ctx):
        self.bot.dispatch("sendReply",ctx, f"😐 🔫 Starting Russian Roulette! `{self.bot.game_state.game.players[self.bot.game_state.game.current_player].display_name}` has the weapon")
    

    #########################
    #        COMMANDS       #
    #########################

    @commands.command("pull", help="Fire the weapon")
    async def pull(self,ctx):
        #If lobby or running game, stop
        if not self.bot.game_state.in_game or self.bot.game_state.game_type != "russianroulette":
            self.bot.dispatch("sendReply",ctx,"No game of Russian Roulette is active.")
            return

        pull_result = self.bot.game_state.game.handle_pull(ctx.author)
        if pull_result == "not_holder":
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you don't currently have the revolver")
            return
        elif pull_result == "dead":
            self.bot.dispatch("sendReply",ctx,f"⚰️ `{ctx.author.display_name}` shot himself with the revolver ⚰️")
            self.bot.dispatch("sendReply",ctx,f"🔫 revolver cylinder spun... 😐 🔫 `{self.bot.game_state.game.get_current_weapon_holder().display_name}` now holds the revolver.")
            return
        elif pull_result == "continue":
            self.bot.dispatch("sendReply",ctx,f"😐 🔫 `{self.bot.game_state.game.get_current_weapon_holder().display_name}` now holds the revolver ")
            return
        else:
            self.bot.dispatch("sendReply",ctx,f"⚰️ `{ctx.author.display_name}` shot himself with the revolver ⚰️")
            self.bot.dispatch("sendReply",ctx,f"🏆🏆 Russian roulette is over `{self.bot.game_state.game.players[0].display_name}` is the winner 🏆🏆")
            self.bot.dispatch("queryAddWin",[(self.bot.game_state.game_type ,self.bot.game_state.game.players[0].id)])
            self.bot.game_state.end_game()

    @commands.command("spin", help="Spin the cylinder of the revolver")
    async def handle_click(self,ctx):
        #If lobby or running game, stop
        if not self.bot.game_state.in_game or self.bot.game_state.game_type != "russianroulette":
            self.bot.dispatch("sendReply",ctx,"No game of Russian Roulette is active.")
            return

        spin_result = self.bot.game_state.game.handle_spin(ctx.author)
        if spin_result == "not_holder":
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you don't currently have the revolver")
            return
        elif spin_result == "already_spun":
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, you've already spun the cylinder")
            return
        else:
            self.bot.dispatch("sendReply",ctx,f"🔫 Cylinder spun.. `{self.bot.game_state.game.get_current_weapon_holder().display_name}` now holds the revolver")


    #########################
    #     COMMAND ERRORS    #
    #########################


#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(russianroulette_game(bot))