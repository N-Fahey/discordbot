import os,datetime
from discord.ext import commands
from dotenv import load_dotenv
import yaml
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData,BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime,timedelta

Base = declarative_base()
load_dotenv()

engine = create_engine(os.getenv("DB_CONNSTR")+"?charset=utf8mb4", echo = False, pool_recycle = 3600)

class BotUsers(Base):
    __tablename__ = 'bot_users'
    user_id = Column('user_id', BigInteger, primary_key=True)
    name = Column('name', String(200))
    display_name =  Column('display_name', String(200))
    bank = Column('bank', BigInteger, default=0)
    last_dole = Column('last_dole', DateTime)

class BotScores(Base):
    __tablename__ = 'bot_scores'
    uid = Column('id', Integer, primary_key=True)
    winner_id = Column('winner_id', BigInteger)
    time = Column('time', DateTime)
    game = Column('game', String(200))
    winnings = Column('winnings',BigInteger)

class BotAILog(Base):
    __tablename__ = 'bot_ai_log'
    uid = Column('id', Integer, primary_key=True)
    time = Column('time', DateTime)
    user_id = Column('user_id', BigInteger)    
    type = Column('type', String(200))
    tokens = Column('usage_tokens', BigInteger)

class BotAIMessageLog(Base):
    __tablename__ = 'bot_ai_message_log'
    uid = Column('id', Integer, primary_key=True)
    time = Column('time', DateTime)
    base_message_id = Column('base_message_id', BigInteger)
    message_id = Column('message_id', BigInteger)
    user_id = Column('user_id', BigInteger)
    role = Column('role', String(20))
    message_text = Column('message_text', String(2000))

Base.metadata.create_all(engine)


#########################
#       Extension       #
#########################

class sql(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.Session = sessionmaker(bind=engine)

    #########################
    #    EVENT LISTENERS    #
    #########################

    #Add member - called when someone joins, or updates user / member
    @commands.Cog.listener()
    async def on_queryAddMember(self,member_id:int,member_name:str,member_display_name:str):
        try:
            with self.Session() as session:

                query_result = session.query(BotUsers).filter(BotUsers.user_id == member_id).one_or_none()

                if query_result:
                    # Update
                    query_result = session.query(BotUsers).filter(BotUsers.user_id == member_id).update({BotUsers.name:member_name, BotUsers.display_name:member_display_name})
                else:
                    # Insert
                    session.add(BotUsers(user_id=member_id,name=member_name,display_name=member_display_name,last_dole=datetime.now()))

                session.commit()

        except:
            raise



    #Add win to winners table
    @commands.Cog.listener()
    async def on_queryAddWin(self,game_type:str,winner_id:int,win_amount): #Set win_amount to None if no pot

        try:
            with self.Session() as session:
                session.add(BotScores(game=game_type,winner_id=winner_id,time=datetime.now(),winnings=win_amount))
                session.commit()

        except:
            raise

    #AI Usage Logging
    @commands.Cog.listener()
    async def on_queryAILog(self, user_id:int, ai_type:str, tokens:int):
        try:
            with self.Session() as session:
                session.add(BotAILog(time=datetime.now(), user_id=user_id, type=ai_type, tokens=tokens))
                session.commit()
        except:
            raise
    
    #AI Conversations
    @commands.Cog.listener()
    async def on_queryAIMessageAdd(self, base_message_id, message_id, user_id, role, message_text):
        try:
            with self.Session() as session:
                session.add(BotAIMessageLog(time=datetime.now(), base_message_id=base_message_id, message_id=message_id, user_id=user_id, role=role, message_text=message_text))
                session.commit()
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

        with open("settings.yaml", "r") as f:
            data = yaml.safe_load(f)
            return data



    #Check bank & return value. Should mostly be used internally
    async def queryCheckBalance(self,member_id:int):
        try:
            with self.Session() as session:

                query_result = session.query(BotUsers).filter(BotUsers.user_id == member_id).one_or_none()

                if query_result:
                    # Update
                    return query_result.bank

                return 0

        except:
            raise
    
    #Attempt to withdraw. Automatically checks balance so don't call separately
    async def queryWithdraw(self,member_id:int,withdraw_amount:int):
        bal = await self.queryCheckBalance(member_id)
        if bal >= withdraw_amount:
            try:
                with self.Session() as session:
                    session.query(BotUsers).filter(BotUsers.user_id == member_id).update({BotUsers.bank:BotUsers.bank - withdraw_amount})
                    session.commit()
                    return True
            except:
                raise  
        else:
            return False      

    #Pay
    async def queryPay(self,member_id:int,pay_amount:int):
        try:
            with self.Session() as session:
                session.query(BotUsers).filter(BotUsers.user_id == member_id).update({BotUsers.bank: BotUsers.bank + pay_amount})
                session.commit()
                return True
        except:
            raise
    
    #Transfer - Use this wherever possible as general transfer from one ID to another
    async def queryTransfer(self,from_member_id:int,to_member_id:int,transfer_amount:int):
        withdraw = await self.queryWithdraw(from_member_id,transfer_amount)
        if withdraw:
            await self.queryPay(to_member_id,transfer_amount)
            return True
        else:
            return False
    
    async def queryPayDole(self,member_id:int):
        try:
            with self.Session() as session:
                session.query(BotUsers).filter(BotUsers.user_id == member_id).update({BotUsers.last_dole:datetime.now()})
                session.commit()
        except:
            raise
        await self.queryPay(member_id,self.bot.dolePayment)

    #Dole checker. This returns their dict of bank value, and allow/disallow dole claim {value,binary allowed/blocked}
    async def queryCheckDole(self,member_id:int):
        try:
            with self.Session() as session:

                query_result = session.query(BotUsers).filter(BotUsers.user_id == member_id).one_or_none()

                if query_result:
                    if query_result.last_dole == None:
                        last_dole_delta = None
                        allow = True
                    else:
                        if (datetime.now().replace(hour=0,second=0,minute=0,microsecond=0) - query_result.last_dole.replace(hour=0,second=0,minute=0,microsecond=0)) >= timedelta(days=1) and query_result.bank < self.bot.doleLimit:
                            last_dole_delta = None
                            allow = True
                        else:
                            allow = False
                            last_dole_delta = datetime.now() - query_result.last_dole

                    return {
                        "balance":query_result.bank,
                        "allow":allow,
                        "lastdole": last_dole_delta
                    }
                else:
                    raise
        except:
            raise
    
    #Top 10 moneys
    async def queryTop10(self):
        try:
            with self.Session() as session:

                query_result = session.query(BotUsers).filter(BotUsers.bank != 0).order_by(BotUsers.bank.desc()).limit(10).all()
                res = {}

                for line in query_result:
                    res[line.display_name] = self.bot.currencyCode + str(line.bank)

                return res
            
        except:
            raise
    
    #Get all currency values
    async def queryAllBanks(self):
        try:
            with self.Session() as session:

                query_result = session.query(BotUsers).all()
                res = {}
                for line in query_result:
                    res[line.user_id] = line.bank
                return res
        except:
            raise
    
    #Get AI Conversation messages
    async def queryAIMessages(self, message_id:int):
        try:
            with self.Session() as session:
                query_base_id = session.query(BotAIMessageLog).filter(BotAIMessageLog.message_id == message_id).one_or_none()
                base_message_id = query_base_id.base_message_id

                res = []
                query_result = session.query(BotAIMessageLog).filter(
                    BotAIMessageLog.base_message_id == base_message_id,
                    BotAIMessageLog.message_id <= message_id)
                for line in query_result:
                    res.append({
                        'role':line.role,
                        'text':line.message_text
                    })
                return {
                    'log':res,
                    'base_message_id':base_message_id
                    }
        except:
            raise


#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(sql(bot))
