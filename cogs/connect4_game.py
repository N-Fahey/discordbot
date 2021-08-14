from discord.ext import commands
from discord import Embed

#########################
#       Game Class      #
#########################

class connect4:
    def __init__(self, players:list):
        if len(players) != 2:
            raise Exception(f"connect4 expects two players. Received {len(players)}")
        self.players = { # Use key to fill columns data, value for everything else
            1:players[0],
            2:players[1]
        }
        self.round = 0
        self.player = 1
        self.emojis = ["⚪","🔵","🔴"]
        self.columns = {
            1:[0,0,0,0,0,0],
            2:[0,0,0,0,0,0],
            3:[0,0,0,0,0,0],
            4:[0,0,0,0,0,0],
            5:[0,0,0,0,0,0],
            6:[0,0,0,0,0,0],
            7:[0,0,0,0,0,0]
        }
        self.msg = None
    
    def addPiece(self,player,column:int):
        if column < 1 or column > 7:
            raise ValueError("Invalid column number")
        
        if player not in self.players.values():
            raise ValueError("Invalid player")
        
        if player != self.players[self.player]:
            raise RuntimeError("Wrong players turn")

        for iteration, value in enumerate(self.columns[column]):
            if value == 0:
                self.columns[column][iteration] = self.player
                self.round += 1
                if self.round >= 7:
                    winner = self.checkWinner()
                    if winner is not None:
                        return winner
                    elif self.round == 42:
                        return "Draw" #Round 42 = all circles filled, since still no winner - it's a draw
                self.player = self.round % 2 + 1
                return "Continue" #If no winner found proceeds to next round

            if iteration == 5:
                return "Full" #If it reaches the top row, and still doesn't find a 0, then column is full.

        raise RuntimeError("Reached end of addPiece without return.")
        

    def formatBoard(self):
        board = ''

        for row in range(5,-1,-1):
            board += ' '.join([self.emojis[self.columns[i][row]] for i in self.columns])
            board += '\n'
        
        board += '1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣'
        return board
    
    def checkWinner(self):
        #Check each column for a vertical winner
        for i in self.columns:
            colString = "".join([str(i) for i in self.columns[i]])
            if "1111" in colString:
                #p1 won
                return self.players[1]
            elif "2222" in colString:
                #p2 won
                return self.players[2]
        #Check for a horizontal winner (match indexes across columns)
        for i in range(6):
            row = []
            for j in self.columns:
                row.append(self.columns[j][i])
            rowString = "".join([str(i) for i in row])
            if "1111" in rowString:
                #p1 won
                return self.players[1]
            elif "2222" in rowString:
                #p2 won 
                return self.players[2]
        #Check for diagonal winner (positive /)
        for i in range(3):
            for j in range(1,5):
                diag = []
                diag.append(self.columns[j][i])
                diag.append(self.columns[j+1][i+1])
                diag.append(self.columns[j+2][i+2])
                diag.append(self.columns[j+3][i+3])
                if diag.count(1) == 4:
                    #p1 wins
                    return self.players[1]
                elif diag.count(2) == 4:
                    #p2 wins
                    return self.players[2]

        #Check for diagonal winner (negative \)
        for i in range(3):
            for j in range(4,8):
                diag = []
                diag.append(self.columns[j][i])
                diag.append(self.columns[j-1][i+1])
                diag.append(self.columns[j-2][i+2])
                diag.append(self.columns[j-3][i+3])
                if diag.count(1) == 4:
                    #p1 wins
                    return self.players[1]
                elif diag.count(2) == 4:
                    #p2 wins
                    return self.players[2]       
        return None

#########################
#       Extension       #
#########################

class connect4_game(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    #########################
    #        COMMANDS       #
    #########################

    #connect4 (initiator)
    @commands.command("connect4", help="Start a game of Connect 4\nThe lobby will automatically close after 5 minutes")
    async def connect4(self,ctx):
        #If lobby or running game, stop
        if self.bot.gameStatus[0] == "lobby":
            self.bot.dispatch("sendReply",ctx,f"A {self.bot.prettyGames[self.bot.gameStatus[1]]} lobby is already open. /join to enter the lobby.")
            return
        if self.bot.gameStatus[0] == "active":
            self.bot.dispatch("sendReply",ctx,f"A {self.bot.prettyGames[self.bot.gameStatus[1]]} game is already running. Wait until it's finished to start another.")
            return
        
        if self.bot.gameStatus[0] == "inactive":
            self.bot.gameStatus[0] = "lobby"
            self.bot.gameStatus[1] = "connect4"
            self.bot.gamePlayers.append(ctx.author)
            self.bot.timer.create_timer("lobbytimer",self.bot.lobbyTimeout,[ctx])
            self.bot.dispatch("log",f"lobby: {ctx.author} created connect4 lobby.")
            self.bot.dispatch("sendReply",ctx,f"{ctx.author.display_name} wants to play Connect 4! /join to enter the lobby! Currently waiting: {ctx.author.display_name}")
        else: #Error handling
            raise RuntimeError("Invalid status code returned while trying to start connect4")
    
    #########################
    #    EVENT LISTENERS    #
    #########################

    #Initial message creation (includes instructions)
    @commands.Cog.listener()
    async def on_publishBoard(self,ctx):
        board = self.bot.game.formatBoard()
        embed = Embed()
        embed.add_field(name='Instructions',value='Click the reactions below to drop your piece into the corresponding column.\nFirst to line up 4 pieces wins')
        embed.add_field(name='Players turn',value=self.bot.game.players[self.bot.game.player].mention)
        msg = await ctx.send(board, embed= embed) #Then add reactions to the msg, and instructions?

        for react in ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣']:
            await msg.add_reaction(react)
        self.bot.game.msg = msg

    #Update message
    @commands.Cog.listener()
    async def on_updateBoard(self,action):
        if action == "Continue":
            embed = Embed()
            embed.add_field(name='Players turn',value=self.bot.game.players[self.bot.game.player].mention)
        elif action == "Full":
            embed = Embed()
            embed.add_field(name='Error',value=f'That column is full! Please try again.')
            embed.add_field(name='Players turn',value=self.bot.game.players[self.bot.game.player].mention)
        board = self.bot.game.formatBoard()
        await self.bot.game.msg.edit(content = board, embed = embed)
    
    #Handle game completion
    @commands.Cog.listener()
    async def on_connect4End(self,result):
        board = self.bot.game.formatBoard()
        if result == "Draw":
            await self.bot.game.msg.channel.send(f"Game was a draw! No more spaces available.")
            self.bot.dispatch("log"f"connect4: Game between {self.bot.gamePlayers[0]} and {self.bot.gamePlayers[1]} was a draw.")
        else:
            self.bot.dispatch("queryAddWin",[(self.bot.gameStatus[1],result.id)])
            self.bot.dispatch("log",f"connect4: {result} won the game.")
            await self.bot.game.msg.channel.send(f"Game over! {result.display_name} is the winner!")
        await self.bot.game.msg.edit(content = board, embed = None)
        await self.bot.game.msg.clear_reactions()
        self.bot.gamePlayers = []
        self.bot.gameStatus = ["inactive", ""]
        self.bot.game = None

    #Reaction listener (should only be active when game running)
    @commands.Cog.listener()
    async def on_connect4Reaction(self,user,reaction):
        if self.bot.game.msg is not None and user == self.bot.game.players[self.bot.game.player]:
            outcome = self.bot.game.addPiece(user,['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣'].index(reaction.emoji) + 1)
            if outcome == "Continue" or outcome == "Full":
                self.bot.dispatch("updateBoard", outcome)
            else:
                self.bot.dispatch("connect4End", outcome)
        await reaction.remove(user)


def setup(bot):
    bot.add_cog(connect4_game(bot))