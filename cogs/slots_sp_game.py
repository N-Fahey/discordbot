from random import randint
from discord.ext import commands
from discord import Embed
import asyncio
from statistics import mean

#########################
#       Game Class      #
#########################

class Slots:
    def __init__(self,players):
        self.player = players[0]
        self.pot = 0
        self.update_bet_options()
        self.msg = None
        self.spins = 0
        self.won = 0
        self.max_pot = 0 #Only used for testing
        self.wins = 0 #Only used for testing        
        self.big_wins = 0 #Only used for testing
        self.jackpots = 0 #Only used for testing
    
    def pull(self,player,bet_index):
        if player != self.player:
            raise ValueError("Player doesn't match.")
        
        if self.pot <= 0:
            return "Out of money"
        
        if self.bet_options[bet_index] > self.pot:
            return "Not enough for that bet"

        self.spins += 1
        spin = self.get_spin()
        result_multiple = self.check_win(spin)
        this_bet = self.bet_options[bet_index]
        self.pot -= this_bet

        if result_multiple is not None:
            winnings = int(result_multiple * this_bet)
            if winnings == 0:
                winnings = 1
            self.won += winnings
            self.pot += winnings
            if self.pot > self.max_pot:
                self.max_pot = self.pot
            
            if spin == (2,3,4) or spin == (4,3,2):
                outcome = "A Gaggle of Gamer Girls"
            elif spin == (4,5,6) or spin == (6,5,4):
                outcome = "The FG Three"
            elif spin == (1,1,1):
                outcome = "CJ's Jackpot"
            elif spin[0] == spin[1] == spin[2]:
                outcome = "a triple"
            else:
                outcome = "two of a kind"

            self.update_bet_options()
        else:
            winnings = 0
            outcome = ""
            self.update_bet_options()

        return {
            "spin":spin,
            "bet":this_bet,
            "winnings":winnings,
            "outcome":outcome,
            "pot":self.pot,
            "options":self.bet_options
        }
    
    def get_spin(self):
        spin = tuple(randint(1,8) for _ in range(3))
        return spin
    
    def update_bet_options(self):
        if self.pot <= 3:
            self.bet_options = [i for i in range(1,self.pot+1)]
        elif 4 <= self.pot <= 20:
            self.bet_options = [1,2,4]
        elif 21 <= self.pot <= 50:
            self.bet_options = [2,5,10]
        elif 51 <= self.pot <= 100:
            self.bet_options = [5,10,20]
        elif 101 <= self.pot <= 500:
            self.bet_options = [10,30,60]
        else:
            self.bet_options = [50,75,100]

    def check_win(self,spin:list):
        big_win_options = { #key: spin, value: payout multiple
            #Gamer girls
            (2,3,4):10,
            (4,3,2):10,
            #The FG Three
            (4,5,6):10,
            (6,5,4):10,
            #CJ's Jackpot
            (1,1,1):50,
        }
        for i in range(2,9):
            #Any other 3 match
            big_win_options[(i,i,i)] = 5

        if spin in big_win_options:
            self.big_wins += 1
            return big_win_options[spin]
        else:
            for i in spin:
                if spin.count(i) > 1:
                    self.wins += 1
                    return 0.9
            return None

""" outcomes = {
    "spins":[],
    "avg_spins":0,
    "max_pots":[],
    "highest_pot":0,
    "little_wins":0,
    "big_wins":0,
    "jackpots":0
}

for _ in range(100):
    slot = Slots(['fish'])
    slot.pot = 100
    slot.update_bet_options()

    while True:
        res = slot.pull('fish',0)
        if slot.pot < 3:
            break
    outcomes["spins"].append(slot.spins)
    outcomes["little_wins"] += slot.wins
    outcomes["max_pots"].append(slot.max_pot)
    if slot.max_pot > outcomes["highest_pot"]:
        outcomes["highest_pot"] = slot.max_pot
    outcomes["big_wins"] += slot.big_wins
    outcomes["jackpots"] += slot.jackpots

outcomes["avg_spins"] = mean(outcomes["spins"])
outcomes["highest_pot_avg"] = mean(outcomes["max_pots"])
outcomes.pop("spins")
outcomes.pop("max_pots")
print(outcomes) """



#########################
#       Extension       #
#########################

class slots_sp_game(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    def get_game_class(self,players):
        return Slots(players)

    # Lobby Capacity Check
    def lobby_capacity_check_start(self, players):
        if len(players) == 1:
            return True
        return False
    
    def lobby_capacity_check_join(self, players):
            return False
    
    # Message to send if lobby capacity check fails
    def lobby_capacity_fail_message(self):
        return "Slots is a single player game!"

    async def on_timer_dq(self,player,lobby,channel):
        #Don't know yet
        pass

    # on_game_start event
    async def on_game_start(self,ctx):
        member_lobby = self.bot.get_member_lobby(ctx.author)
        if member_lobby.pot is None or member_lobby.pot[ctx.author] <= 0:
            await self.bot.lobby_end_game(member_lobby,None)
            self.bot.dispatch("sendReply",ctx,"A bet is required to start Slots.")
            return
        
        member_lobby.game.pot = member_lobby.pot[ctx.author]
        member_lobby.pot[ctx.author] = 0
        member_lobby.game.update_bet_options()
        self.bot.dispatch("create_slots_message",ctx)
        self.bot.dispatch("sendReply",ctx,f"Ready to play. !handle. Bet options: {member_lobby.game.bet_options} Pot: {member_lobby.game.pot}")
    
    #########################
    #        COMMANDS       #
    #########################

    #Shouldnt be any
    
    #########################
    #    EVENT LISTENERS    #
    #########################

    async def end_slots_message(self,user):
        member_lobby = self.bot.get_member_lobby(user)
        if not member_lobby:
            return
        
        if member_lobby.game.msg is None:
            raise RuntimeError("No game message could be found.")
        
        embed = Embed(title=f"🤑🎰💰{user.display_name}'s Slots!💰🎰🤑")
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Game Ended",value="Thanks for playing!")
        if member_lobby.game.pot > 0:
            embed.add_field(name="Payout",value=f"{self.bot.currencyCode}{member_lobby.game.pot}")
        await member_lobby.game.msg.edit(embed=embed)
        await member_lobby.game.msg.clear_reactions()

    @commands.Cog.listener()
    async def on_create_slots_message(self,ctx):
        member_lobby = self.bot.get_member_lobby(ctx.author)
        if not member_lobby:
            return
        
        if member_lobby.game.msg is not None:
            raise RuntimeError("Can only create slots message if none exists")
        
        embed = Embed(title=f"🤑🎰💰{ctx.author.display_name}'s Slots!💰🎰🤑")
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name="Instructions",value="Select one of the bet options below to place a bet and pull the handle! Choose the 🏧 option to withdraw your pot.")
        embed.add_field(name="Pot",value=f"{self.bot.currencyCode}{member_lobby.game.pot}")
        render_bet_options = member_lobby.game.bet_options + ['--'] * (3-len(member_lobby.game.bet_options))
        embed.add_field(name="Bet Options",value=f"1️⃣:{self.bot.currencyCode}{render_bet_options[0]} 2️⃣:{self.bot.currencyCode}{render_bet_options[1]} 3️⃣:{self.bot.currencyCode}{render_bet_options[2]} 🏧:Cash out!",inline=False)
        
        message = await ctx.send(embed=embed)

        for react in ['1️⃣','2️⃣','3️⃣','🏧']:
            await message.add_reaction(react)

        member_lobby.game.msg = message
        
    @commands.Cog.listener()
    async def on_update_slots_message(self,user,result):
        member_lobby = self.bot.get_member_lobby(user)
        if not member_lobby:
            return
        
        if member_lobby.game.msg is None:
            raise RuntimeError("No game message could be found.")
        for i in range(4):
            if i != 0:
                await asyncio.sleep(1)
            spin_msg = result['spin'][:i]
            disp_msg = [self.bot.emojiDict['spin'],self.bot.emojiDict['spin'],self.bot.emojiDict['spin']]
            for index,spin_int in enumerate(spin_msg):
                disp_msg[index] = self.bot.emojiDict['slot_' + str(spin_int)]
            embed = Embed(title=f"🤑🎰💰{user.display_name}'s Slots!💰🎰🤑")
            embed.set_thumbnail(url=user.avatar_url)
            embed.add_field(name="Instructions",value="Select one of the bet options below to place a bet and pull the handle! Choose the 🏧 option to withdraw your pot.",inline=False)
            embed.add_field(name="🎰Your Spin!🎰",value=" ".join(disp_msg),inline=False)
            await member_lobby.game.msg.edit(embed=embed)
        
        if result['pot'] == 0:
            await asyncio.sleep(0.5)
            await self.end_slots_message(user)
            await self.bot.lobby_end_game(member_lobby,None)

        if result['outcome'] != "":
            embed.add_field(name="You Won!",value=f"🤑You spun 💸⭐{result['outcome']}⭐💸!! You win:{self.bot.currencyCode}{result['winnings']}!!🤑",inline=False)
        embed.add_field(name="Pot",value=f"{self.bot.currencyCode}{member_lobby.game.pot}")
        embed.add_field(name="Spins",value=member_lobby.game.spins)
        if member_lobby.game.won > 0:
            embed.add_field(name="Total Won",value=f"💰{self.bot.currencyCode}{member_lobby.game.won}💰")
        render_bet_options = member_lobby.game.bet_options + ['--'] * (3-len(member_lobby.game.bet_options))
        embed.add_field(name="Bet Options",value=f"1️⃣:{self.bot.currencyCode}{render_bet_options[0]} 2️⃣:{self.bot.currencyCode}{render_bet_options[1]} 3️⃣:{self.bot.currencyCode}{render_bet_options[2]} 🏧:Cash out!",inline=False)
        await member_lobby.game.msg.edit(embed=embed)

    #Reaction listener - called by on_reaction_add if the calling user is in a game of slots
    @commands.Cog.listener()
    async def on_slots_reaction(self,user,reaction):
        member_lobby = self.bot.get_member_lobby(user)
        if not member_lobby:
            return

        if member_lobby.game.msg is not None and user == member_lobby.game.player and reaction.emoji:
            bet_options = ['1️⃣','2️⃣','3️⃣']
            if reaction.emoji in bet_options:
                #Check if the selected bet option is valid (Occurs when pot < 3)
                if len(member_lobby.game.bet_options) -1 >= bet_options.index(reaction.emoji):
                    res = member_lobby.game.pull(user,bet_options.index(reaction.emoji))
                    self.bot.dispatch("update_slots_message",user,res)
            elif reaction.emoji == '🏧':
                #Pay em out and end the game
                member_lobby.pot = {user:member_lobby.game.pot}
                await self.end_slots_message(user)                
                await self.bot.lobby_end_game(member_lobby,user)
                pass

        
        #Regardless of above, remove the reaction at the end
        await reaction.remove(user)


#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(slots_sp_game(bot))
