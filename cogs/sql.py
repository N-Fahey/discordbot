import os,datetime
from discord.ext import commands
from mysql.connector import connect,Error
from dotenv import load_dotenv

#General connector used in all events
def openConnection():  
    load_dotenv()
    loginDetails = {"host":os.getenv("SQL_HOST"),"database":os.getenv("SQL_DB"),"user":os.getenv("SQL_USER"),"password":os.getenv("SQL_PW")}
    try:
        connection = connect(**loginDetails)
        return connection
    except Error as error:
        raise error

#########################
#       Extension       #
#########################

class sql(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    #########################
    #    EVENT LISTENERS    #
    #########################

    #Add member - called when someone joins, or updates user / member
    @commands.Cog.listener()
    async def on_queryAddMember(self,qData): #qData expects [(member.id, member.name, member.display_name)]
        if not isinstance(qData, list) and not isinstance(qData[0], tuple):
            raise TypeError(f"Wrong type for qData. Expected List of Tuples, received outer: {type(qData)}, inner: {type(qData[0])}")

        conn = openConnection()
        if conn.is_connected():
            try:
                cursor = conn.cursor()
                q = """INSERT INTO bot_users (user_id,name,display_name)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name), display_name=VALUES(display_name);
                    """
                cursor.executemany(q, qData)
                conn.commit()
                cursor.close()
                conn.close()
                self.bot.dispatch("log",f"mysql: queryAddMember succeeded. Query passed with values: {qData}")
            except:
                raise
        else:
            raise ConnectionError("No open connection to sql server.")

    #Add win to winners table
    @commands.Cog.listener()
    async def on_queryAddWin(self,qData): #qData expects [(bot.gameStatus[1]:str(gamename),winner.id)]
        conn = openConnection()
        if conn.is_connected():
            try:
                cursor = conn.cursor()
                q = """INSERT INTO bot_scores (winner_id, game)
                SELECT id, %s
                FROM bot_users WHERE user_id = %s"""
                cursor.executemany(q, qData)
                conn.commit()
                cursor.close()
                conn.close()
                self.bot.dispatch("log",f"mysql: queryAddWinner succeeded. Query passed with values: {qData}")
            except:
                raise
    
    #########################
    #    ASYNC FUNCTIONS    #
    #########################
    #For when a return value is expected
    #To call these somewhere else:
    #var = self.bot.get_cog('cogname')
    #await var.function(args)

    #Load settings. Return settings values, and games list
    async def queryRetrieveSettings(self): #No need to pass any data here
        conn = openConnection()
        if conn.is_connected():
            try:
                cursor = conn.cursor()
                q = """SELECT name,value,type FROM bot_settings"""
                cursor.execute(q)
                settingRes = cursor.fetchall() #Returns list of tuples
                q = """SELECT name,pretty_name FROM bot_games"""
                cursor.execute(q)
                gameRes = cursor.fetchall()
                cursor.close()
                conn.close()
            except:
                raise

            settings = {}
            games = {}
            #All setting values are TEXT in DB - so convert to whatever is needed and append to settings dict
            for setting in settingRes:
                if setting[2] == 'int':
                    settings[setting[0]] = int(setting[1])
                elif setting[2] == 'float':
                    settings[setting[0]] = float(setting[1])
                elif setting[2] == 'str':
                    settings[setting[0]] = setting[1]
            
            for game in gameRes:
                games[game[0]] = game[1]
            
            settings['prettyGames'] = games
            return settings
        else:
            return "Connection failed to open"

    #Check bank & return value. Should mostly be used internally
    async def queryCheckBalance(self,qData): #qData expects (member.id,). Single pass only
        conn = openConnection()
        if conn.is_connected():
            try:
                cursor = conn.cursor()
                q = """SELECT bank FROM bot_users
                WHERE user_id = %s"""
                cursor.execute(q,qData)
                res = cursor.fetchone()
                conn.commit()
                cursor.close()
                conn.close()
                self.bot.dispatch("log",f"mysql: queryCheckBalance succeeded. Query passed with values: {qData}")
                return res[0]
            except:
                raise
    
    #Attempt to withdraw. Automatically checks balance so don't call separately
    async def queryWithdraw(self,qData): #qData expects [(withdraw_amount,member_id)]
        bal = await self.queryCheckBalance((qData[0][1],))
        if bal >= qData[0][0]:
            conn = openConnection()
            if conn.is_connected():
                try:
                    cursor = conn.cursor()
                    q = """UPDATE bot_users SET bank = bank - %s
                    WHERE user_id = %s"""
                    cursor.executemany(q,qData)
                    conn.commit()
                    cursor.close()
                    conn.close()
                    self.bot.dispatch("log",f"mysql: queryWithdraw succeeded. Query passed with values: {qData}")
                    return True
                except:
                    raise
        else:
            return False

    #Pay
    async def queryPay(self,qData): #qData expects [(pay_amount,member_id)]
        conn = openConnection()
        if conn.is_connected():
            try:
                cursor = conn.cursor()
                q = """UPDATE bot_users SET bank = bank + %s
                WHERE user_id = %s""" 
                cursor.executemany(q,qData)
                conn.commit()
                cursor.close()
                conn.close()
                self.bot.dispatch("log",f"mysql: queryPay succeeded. Query passed with values: {qData}")
            except:
                raise

    #Transfer - Use this wherever possible as general transfer from one ID to another
    async def queryTransfer(self,qData): #qData expects [(pay_amount,from_member_id,to_member_id)]
        withdraw = await self.queryWithdraw([(qData[0][0],qData[0][1])])
        if withdraw:
            await self.queryPay([(qData[0][0],qData[0][2])])
            return True
        else:
            return False
    
    async def queryPayDole(self,qData): #qData expects [(member_id,)]
        conn = openConnection()
        if conn.is_connected():
            try:
                cursor = conn.cursor()
                q = """UPDATE bot_users
                SET last_dole = CURRENT_TIMESTAMP()
                WHERE user_id = %s
                """
                cursor.executemany(q,qData)
                conn.commit()
                cursor.close()
                conn.close()
                self.bot.dispatch("log",f"mysql: queryPayDole succeeded. Query passed with values: {qData}")
            except:
                raise
            await self.queryPay([(self.bot.dolePayment,qData[0][0])]) #Tie dole payments to setting

    #Dole checker. This returns their dict of bank value, and allow/disallow dole claim {value,binary allowed/blocked}
    async def queryCheckDole(self,qData): #qData expects (member.id,)
        conn = openConnection()
        if conn.is_connected():
            try:
                cursor = conn.cursor()
                q = """SELECT bank, TIMEDIFF(CURRENT_TIMESTAMP,last_dole)
                FROM bot_users
                WHERE user_id = %s"""
                cursor.execute(q,qData)
                res = cursor.fetchone()
                conn.commit()
                cursor.close()
                conn.close()

                if res[1].total_seconds() > self.bot.doleTimeout and res[0] < self.bot.doleLimit:
                    allow = True
                else:
                    allow = False

                self.bot.dispatch("log",f"mysql:queryCheckDole succeeded. Query passed with values: {qData}")
                return {
                    "balance":res[0],
                    "allow":allow
                }
            except:
                raise

#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(sql(bot))
