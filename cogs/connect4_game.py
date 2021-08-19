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

    def get_game_class(self,players):
        return connect4(players)

    # Lobby Capacity Check
    def lobby_capacity_check_start(self,players):
        if len(players) == 2:
            return True
        return False
    
    def lobby_capacity_check_join(self,players):
        if len(players) > 1:
           return False
        return True
    
    # Message to send if lobby capacity check fails
    def lobby_capacity_fail_message(self):
        return "There must be exactly 2 players in order to start"
    
    async def on_timer_dq(self,player,lobby,channel):
        lobby.lobby_players.remove(player)
        self.bot.dispatch("sendReply",channel,f"`{player.display_name}` was removed for inactivity.")
        self.bot.dispatch("connect4End",lobby.lobby_players[0],lobby.lobby_players[0])

    # on_game_start event
    async def on_game_start(self,ctx):
        member_lobby = self.bot.get_member_lobby(ctx.author)
        self.bot.round_timer_reset(ctx.author,member_lobby,ctx.channel)
        self.bot.dispatch("publishBoard",ctx)



    #########################
    #    EVENT LISTENERS    #
    #########################

    #Initial message creation (includes instructions)
    @commands.Cog.listener()
    async def on_publishBoard(self,ctx):
        member_lobby = self.bot.get_member_lobby(ctx.author)
        if not member_lobby:
            return

        board = member_lobby.game.formatBoard()
        embed = Embed()
        embed.add_field(name='Instructions',value='Click the reactions below to drop your piece into the corresponding column.\nFirst to line up 4 pieces wins')
        embed.add_field(name='Players turn',value=member_lobby.game.players[member_lobby.game.player].mention)
        msg = await ctx.send(board, embed= embed) #Then add reactions to the msg, and instructions?

        for react in ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣']:
            await msg.add_reaction(react)
        member_lobby.game.msg = msg

    #Update message
    @commands.Cog.listener()
    async def on_updateBoard(self,action, user):

        member_lobby = self.bot.get_member_lobby(user)
        if not member_lobby:
            return

        if action == "Continue":
            embed = Embed()
            names = [i.display_name for i in member_lobby.game.players.values()]
            embed.add_field(name='Players',value=f"{member_lobby.game.emojis[1]}Player 1: {names[0]}\n{member_lobby.game.emojis[2]}Player 2: {names[1]}")
            embed.add_field(name='Players turn',value=member_lobby.game.players[member_lobby.game.player].mention)
            self.bot.round_timer_reset(member_lobby.game.players[member_lobby.game.player],member_lobby,member_lobby.game.msg.channel)
        elif action == "Full":
            embed = Embed()
            embed.add_field(name='Error',value=f'That column is full! Please try again.')
            embed.add_field(name='Players turn',value=member_lobby.game.players[member_lobby.game.player].mention)
        board = member_lobby.game.formatBoard()
        await member_lobby.game.msg.edit(content = board, embed = embed)
    
    #Handle game completion
    @commands.Cog.listener()
    async def on_connect4End(self,result,user):
        member_lobby = self.bot.get_member_lobby(user)
        if not member_lobby:
            return

        board = member_lobby.game.formatBoard()
        if result == "Draw":
            await member_lobby.game.msg.channel.send(f"Game was a draw! No more spaces available.")
            self.bot.dispatch("log"f"connect4: Game between {member_lobby.lobby_players[0]} and {member_lobby.lobby_players[1]} was a draw.")
        else:
            self.bot.dispatch("log",f"connect4: {result} won the game.")
            await member_lobby.game.msg.channel.send(f"Game over! `{result.display_name}` is the winner!")
        await member_lobby.game.msg.edit(content = board, embed = None)
        await member_lobby.game.msg.clear_reactions()
        await self.bot.lobby_end_game(member_lobby,result)

    #Reaction listener (should only be active when game running)
    @commands.Cog.listener()
    async def on_connect4Reaction(self,user,reaction):

        member_lobby = self.bot.get_member_lobby(user)
        if not member_lobby:
            return

        if member_lobby.game.msg is not None and user == member_lobby.game.players[member_lobby.game.player]:
            outcome = member_lobby.game.addPiece(user,['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣'].index(reaction.emoji) + 1)
            if outcome == "Continue" or outcome == "Full":
                self.bot.dispatch("updateBoard", outcome ,user)
            else:
                self.bot.dispatch("connect4End", outcome, user)
        await reaction.remove(user)


def setup(bot):
    bot.add_cog(connect4_game(bot))