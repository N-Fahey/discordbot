from random import randint
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument

#########################
#       Game Class      #
#########################

class LiarsDice:
    def __init__(self, players:list):
        if len(players) <2:
            raise ValueError("LiarsDice requires 2 or more players")
        self.players = players
        self.round = 0
        self.betNumber = 0
        self.hands = {}
        self.lastBet = [0,0,0]
        self.better = None
        self.pcount = len(players)
        self.totals = {1:0,2:0,3:0,4:0,5:0,6:0}
        self.assignHands()
    
    def betHandler(self, qty:int, face:int, player):
        if face > 6 or face < 1:
            raise ValueError("Face must be between 1 & 6")
        
        if qty > 6 * self.pcount or qty < 1:
            raise ValueError("Invalid number of dice, try again")
        
        bet = [qty,face,player]

        if bet[1] > self.lastBet[1]:
            #Face is higher,
            if bet[0] >= self.lastBet[0]:
                #If qty is greater or equal
                valid = True
            else:
                #qty is less, so invalid even for higher face
                valid = False
        else:
            #Face is either equal, or less than last bet
            if bet[0] > self.lastBet[0]:
                #qty is greater, valid bet
                valid = True
            else:
                #qty is less or the same, so invalid
                valid = False
        
        if valid:
            self.lastBet = bet
            self.betNumber = self.betNumber + 1
            self.better = self.players[self.betNumber % len(self.players)]
            return True
        else:
            return False
        
    def betLiar(self, player):
        if self.lastBet == [0,0,0]:
            return "Nobody has placed a bet yet!"
            
        if self.totals[self.lastBet[1]] < self.lastBet[0]:
            if self.removePlayer(self.lastBet[2]) == True:
                lb = self.lastBet[2]
                self.assignHands()
                return [lb,"continue"]
            else:
                return [self.lastBet[2],"end"]
        else:
            if self.removePlayer(player) == True:
                self.assignHands()
                return [player,"continue"]
            else:
                return [player,"end"]
    
    def rollDice(self):
        dice = []
        for _ in range(6):
            dice.append(randint(1,6))
        dice.sort()
        return dice
    
    def assignHands(self):
        self.hands = {}
        self.totals = {1:0,2:0,3:0,4:0,5:0,6:0}
        self.betNumber = self.round
        self.better = self.players[self.round % self.pcount]
        self.lastBet = [0,0,0]
        self.round = self.round + 1
        for player in self.players:
            self.hands[player] = self.rollDice()
            for i in self.hands[player]:
                self.totals[i] = self.totals[i] + 1
        return self.hands
    
    def removePlayer(self,player):
        if player in self.players:
            self.players.remove(player)
            self.pcount = len(self.players)
            if len(self.players) > 1:
                return True
            else:
                return False
        else:
            raise RuntimeError(f"Couldn't find a player matching: {player}")

#########################
#       Extension       #
#########################            

class liarsdice_game(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    #########################
    #        COMMANDS       #
    #########################

    #liarsdice (Initiator)
    @commands.command(name="liarsdice", help="Start a game of Liar's Dice\nThe lobby will close automatically after 5 minutes.")
    async def liarsdice(self, ctx):
        #If lobby or running game, stop
        if self.bot.gameStatus[0] == "lobby":
            self.bot.dispatch("sendReply",ctx,f"A lobby is already open! /join to enter the lobby.")
            return
        if self.bot.gameStatus[0] == "active":
            self.bot.dispatch("sendReply",ctx,f"A game is already running. Wait until it's finished to start another.")
            return

        if self.bot.gameStatus[0] == "inactive":
            self.bot.gameStatus[0] = "lobby"
            self.bot.gameStatus[1] = "liarsdice"
            self.bot.gamePlayers.append(ctx.author)
            dicePlayersPretty = [player.display_name for player in self.bot.gamePlayers]
            self.bot.timer.create_timer("lobbytimer",self.bot.lobbyTimeout,[ctx])
            self.bot.dispatch("log",f"lobby: {ctx.author} created liarsdice lobby.")
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name} wants to play Liar's Dice! /join to enter the lobby! Currently waiting: {','.join(dicePlayersPretty)}")
        else: #Error handling
            raise RuntimeError("Invalid status code returned while trying to start liarsdice")

    #bet
    @commands.command(name="bet", help="Place a bet in Liar's Dice. Usage: /bet {face} {quantity}")
    async def bet(self, ctx, qty:int, face:int):
        if self.bot.gameStatus[0] != "active" or self.bot.gameStatus[1] != "liarsdice":
            self.bot.dispatch("sendReply",ctx,"No game of Liar's Dice active.")
            return

        if ctx.author != self.bot.game.better:
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, it's not your turn to bet.")
            return

        if 1 <= face <= 6 and 1 <= qty <= 6 * self.bot.game.pcount:
            self.bot.dispatch("log",f"liarsdice: {ctx.author} placed bet of {qty} {face}'s.")
            res = self.bot.game.betHandler(qty,face,ctx.author) #Do this if passes checks
            if res == True:
                emoji = f"d{face}"
                reply = f"{ctx.author.display_name} placed bet of {qty} x {self.bot.emojiDict[emoji]}. {self.bot.game.better.mention}, your turn to bet."
            else:
                reply = f"{ctx.author.display_name}, you can't make that bet. Try again. Use /bet [quantity] [face]"
        else:
            reply = "Bet invalid."

        self.bot.dispatch("sendReply",ctx,reply)

    #liar
    @commands.command(name="liar", help="Call the last better a liar in Liar's Dice.")
    async def liar(self,ctx):
        if self.bot.gameStatus[0] != "active" or self.bot.gameStatus[1] != "liarsdice":
            self.bot.dispatch("sendReply",ctx,"No game of Liar's Dice active.")
            return

        if ctx.author != self.bot.game.better:
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name}, it's not your turn to bet.")
            return  

        if self.bot.game.lastBet == [0,0,0]:
            self.bot.dispatch("sendReply",ctx,f"Nobody has placed a bet yet.")
            return
        lastBet = self.bot.game.lastBet
        totals = self.bot.game.totals
        res = self.bot.game.betLiar(ctx.author)

        if res[1] == "continue" or res[1] == "end":
            if res[0] == ctx.author:
                logmsg = f"liarsdice: {ctx.author} called liar against {res[0]} incorrectly. {ctx.author} removed from game."
                reply = f"Wrong, total number of {lastBet[1]}'s was: {totals[lastBet[1]]}. {res[0].display_name} loses!"
            elif res[0] == lastBet[2]:
                logmsg = f"liarsdice: {ctx.author} called liar against {res[0]} correctly. {res[0]} removed from game."
                reply = f"{res[0].display_name}, you're liar and you will spend an eternity on this ship! Total number of {lastBet[1]}'s was: {totals[lastBet[1]]}."
            else:
                raise RuntimeError("Invalid player returned by betLiar.")
        else:
            raise RuntimeError("Invalid result code returned")
        
        self.bot.dispatch("log",logmsg)
        self.bot.dispatch("sendReply",ctx,reply)
        if res[1] == "continue":
            self.bot.dispatch("messageHands")
            self.bot.dispatch("sendReply",ctx,f"Round {self.bot.game.round}: {self.bot.game.better.mention}, your turn to bet.")
        else:
            self.bot.dispatch("queryAddWin",[(self.bot.gameStatus[1],self.bot.game.players[0].id)])
            self.bot.dispatch("sendReply",ctx,f"Game is over. {self.bot.game.players[0].mention} is the winner!")
            self.bot.gamePlayers = []
            self.bot.gameStatus = ["inactive", ""] 
            self.bot.game = None

    #########################
    #     COMMAND ERRORS    #
    #########################

    @bet.error
    async def bet_error(self,ctx,error):
        if isinstance(error,MissingRequiredArgument):
            await ctx.send("Missing required argument. You need to /bet {face} {quantity}")

    @commands.Cog.listener()
    async def on_messageHands(self):
        hands = {}
        for p in self.bot.game.hands:
            dice = []
            for i in self.bot.game.hands[p]:
                dice.append(self.bot.emojiDict[f"d{i}"])
            hands[p] = dice

        for player in self.bot.gamePlayers:
            await player.send("Here are your dice. Keep them a secret!")
            await player.send(" ".join(hands[player]))

#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(liarsdice_game(bot))