from random import randint
from discord.ext import commands
from discord import ui,ButtonStyle,Interaction,Embed
import asyncio

#########################
#         Views         #
#########################


class Slots_View(ui.View):
    def __init__(self,bot,lobby):
        super().__init__(timeout=None)
        self.bot = bot
        self.lobby = lobby
    
    async def interaction_check(self,interaction):
        if interaction.user != self.lobby.lobby_owner:
            await interaction.response.send_message("This isn't your game!",ephemeral=True)
            return False
        else:
            return True
    
    async def update_buttons(self,bet_options):
        buttons = [i for i in self.children if isinstance(i,ui.Button) and i.custom_id != 'quit' and i.custom_id != 'all_in']
        for index,btn in enumerate(buttons):
            try:
                btn.disabled = False
                btn.label = f'{self.bot.currencyCode}{bet_options[index+1]}'               
            except IndexError:                
                btn.disabled = True
            except:
                raise
        return self #Returns the updated view. pass this into the message.edit along with any other changes

    @ui.button(label='1',emoji='1️⃣', style=ButtonStyle.blurple,custom_id='1')
    async def bet_1(self, button:ui.Button, interaction:Interaction):
        self.bot.dispatch("slots_reaction",interaction.user,1)
    
    @ui.button(label='2',emoji='2️⃣', style=ButtonStyle.blurple,custom_id='2')
    async def bet_2(self, button:ui.Button, interaction:Interaction):
        self.bot.dispatch("slots_reaction",interaction.user,2)
    
    @ui.button(label='3',emoji='3️⃣', style=ButtonStyle.blurple,custom_id='3')
    async def bet_3(self, button:ui.Button, interaction:Interaction):
        self.bot.dispatch("slots_reaction",interaction.user,3)
    
    @ui.button(label='All in',emoji='🤑', style=ButtonStyle.danger,custom_id='all_in')
    async def allin(self, button:ui.Button, interaction:Interaction):
        confirm_view = Slots_Confirm_View(self.bot,self.lobby)
        await interaction.response.send_message(f"Are you sure you want to go all in? This will bet your entire pot ({self.bot.currencyCode}{self.lobby.game.pot})\nDismiss this message to back out like a tiny little baby. waa waaa waaaaa.\nOh, you didn't mean to press the button? What are you going to do? Cry??? Like a baby??",view=confirm_view,ephemeral=True)
    
    @ui.button(label='Cash out',emoji='🏧', style=ButtonStyle.blurple, custom_id='quit')
    async def cashout(self, button:ui.Button, interaction:Interaction):
        self.bot.dispatch("slots_reaction",interaction.user,'quit')

class Slots_Confirm_View(ui.View):
    def __init__(self,bot,lobby):
        super().__init__()
        self.bot=bot
        self.lobby=lobby
    
    async def interaction_check(self,interaction): #Since message this attaches to is ephemeral this shouldn't ever matter. But putting it here anyway
        if interaction.user != self.lobby.lobby_owner:
            await interaction.response.send_message("This isn't your game!",ephemeral=True)
            return False
        else:
            return True
    
    @ui.button(label='Confirm',emoji='⚠️', style=ButtonStyle.red)
    async def allin_confirm(self,button:ui.Button,interaction:Interaction):
        self.bot.dispatch("slots_reaction",interaction.user,0)

#########################
#       Game Class      #
#########################

class Slots:
    def __init__(self,players):
        self.player = players[0]
        self.pot = 0
        self.update_bet_options()
        self.msg = None
        self.spinning = False
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
            
            if 2 in spin and 3 in spin and 4 in spin:
                outcome = "A Gaggle of Gamer Girls"
            elif 4 in spin and 5 in spin and 6 in spin:
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
            self.bet_options.insert(0,self.pot)
        elif 4 <= self.pot <= 20:
            self.bet_options = [self.pot,1,2,4]
        elif 21 <= self.pot <= 50:
            self.bet_options = [self.pot,2,5,10]
        elif 51 <= self.pot <= 100:
            self.bet_options = [self.pot,5,10,20]
        elif 101 <= self.pot <= 500:
            self.bet_options = [self.pot,10,30,60]
        else:
            self.bet_options = [self.pot,50,75,100]

    def check_win(self,spin:list):
        big_win_options = { #key: spin, value: payout multiple
            #Gamer girls
            (2,3,4):5,
            (2,4,3):5,
            (3,2,4):5,
            (3,4,2):5,
            (4,2,3):5,
            (4,3,2):5,
            #The FG Three
            (4,5,6):5,
            (4,6,5):5,
            (5,4,6):5,
            (5,6,4):5,
            (6,4,5):5,
            (6,5,4):5,
            #CJ's Jackpot
            (1,1,1):50,
        }
        for i in range(2,9):
            #Any other 3 match
            big_win_options[(i,i,i)] = 3

        if spin in big_win_options:
            self.big_wins += 1
            return big_win_options[spin]
        else:
            for i in spin:
                if spin.count(i) > 1:
                    self.wins += 1
                    return 2
            return None

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
        #Don't really need this
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
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="Game Ended",value="Thanks for playing!")
        if member_lobby.game.pot > 0:
            embed.add_field(name="Payout",value=f"{self.bot.currencyCode}{member_lobby.game.pot}")
        await member_lobby.game.msg.edit(embed=embed,view=None)

    @commands.Cog.listener()
    async def on_create_slots_message(self,ctx):
        member_lobby = self.bot.get_member_lobby(ctx.author)
        if not member_lobby:
            return
        
        if member_lobby.game.msg is not None:
            raise RuntimeError("Can only create slots message if none exists")
        
        embed = Embed(title=f"🤑🎰💰{ctx.author.display_name}'s Slots!💰🎰🤑")
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.add_field(name="Instructions",value="Select one of the bet options below to place a bet and pull the handle! Choose the 🏧 option to withdraw your pot.")
        embed.add_field(name="Pot",value=f"{self.bot.currencyCode}{member_lobby.game.pot}")
        view = Slots_View(self.bot,member_lobby)
        await view.update_buttons(member_lobby.game.bet_options)
        member_lobby.game.view = view
        message = await ctx.send(embed=embed,view=view)

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
            embed.set_thumbnail(url=user.avatar.url)
            embed.add_field(name="Instructions",value="Select one of the bet options below to place a bet and pull the handle! Choose the 🏧 option to withdraw your pot.",inline=False)
            embed.add_field(name="🎰Your Spin!🎰",value=" ".join(disp_msg),inline=False)
            await member_lobby.game.msg.edit(embed=embed)
        
        if result['pot'] == 0:
            await asyncio.sleep(0.5)
            await self.end_slots_message(user)
            await self.bot.lobby_end_game(member_lobby,None)
            return

        if result['outcome'] != "":
            embed.add_field(name="You Won!",value=f"🤑You spun 💸⭐{result['outcome']}⭐💸!! You win:{self.bot.currencyCode}{result['winnings']}!!🤑",inline=False)
        embed.add_field(name="Pot",value=f"{self.bot.currencyCode}{member_lobby.game.pot}")
        embed.add_field(name="Spins",value=member_lobby.game.spins)
        if member_lobby.game.won > 0:
            embed.add_field(name="Total Won",value=f"💰{self.bot.currencyCode}{member_lobby.game.won}💰")
        view = await member_lobby.game.view.update_buttons(member_lobby.game.bet_options)
        await member_lobby.game.msg.edit(embed=embed, view=view)
        member_lobby.game.spinning = False

    #Repurposed reaction listener
    @commands.Cog.listener()
    async def on_slots_reaction(self,user,selection):
        member_lobby = self.bot.get_member_lobby(user)
        if not member_lobby:
            return

        if member_lobby.game.spinning:
            return

        if selection == 'quit':
            member_lobby.pot = {user:member_lobby.game.pot}
            await self.end_slots_message(user)                
            await self.bot.lobby_end_game(member_lobby,user)
        else:
            if len(member_lobby.game.bet_options) - 1 >= selection:
                member_lobby.game.spinning = True
                res = member_lobby.game.pull(user,selection)
                self.bot.dispatch("update_slots_message",user,res)

#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(slots_sp_game(bot))
