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

engine = create_engine(os.getenv("DB_CONNSTR"), echo = True)

class BotUsers(Base):
    __tablename__ = 'bot_users'
    user_id = Column('user_id', BigInteger, primary_key=True)
    name = Column('name', String(200))
    display_name =  Column('display_name', String(200))
    bank = Column('bank', BigInteger, default=100)
    last_dole = Column('last_dole', DateTime)

class BotScores(Base):
    __tablename__ = 'bot_scores'
    uid = Column('id', Integer, primary_key=True)
    winner_id = Column('winner_id', BigInteger)
    time = Column('time', DateTime)
    game = Column('game', String(200))
    winnings = Column('winnings',BigInteger)


Base.metadata.create_all(engine)


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
        
        try:
            qData = qData[0]
            Session = sessionmaker(bind=engine)
            session = Session()

            query_result = session.query(BotUsers).filter(BotUsers.user_id == qData[0]).one_or_none()

            if query_result:
                # Update
                query_result = session.query(BotUsers).filter(BotUsers.user_id == qData[0]).update({BotUsers.name:qData[1], BotUsers.display_name:qData[2]})
            else:
                # Insert
                session.add(BotUsers(user_id=qData[0],name=qData[1],display_name=qData[2]))

            session.commit()

        except:
            raise


    @commands.Cog.listener()
    async def on_populatedb(self,qData):
        for guild in self.bot.guilds:
            for member in guild.members:
                if not member.bot:
                    await self.on_queryAddMember([(member.id, member.name, member.display_name)])


    #Add win to winners table
    @commands.Cog.listener()
    async def on_queryAddWin(self,qData): #qData expects [(gamename,winner.id,winning_amount(or None))]

        try:
            Session = sessionmaker(bind=engine)
            session = Session()
            session.add(BotScores(game=qData[0][0],winner_id=qData[0][1],time=datetime.now(),winnings=qData[0][2]))
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
    async def queryCheckBalance(self,qData): #qData expects (member.id,). Single pass only
        try:
            Session = sessionmaker(bind=engine)
            session = Session()

            query_result = session.query(BotUsers).filter(BotUsers.user_id == qData[0]).one_or_none()

            if query_result:
                # Update
                return query_result.bank

            return 0

        except:
            raise
    
    #Attempt to withdraw. Automatically checks balance so don't call separately
    async def queryWithdraw(self,qData): #qData expects [(withdraw_amount,member_id)]
        bal = await self.queryCheckBalance((qData[0][1],))
        if bal >= qData[0][0]:
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                query_result = session.query(BotUsers).filter(BotUsers.user_id == qData[0][1]).update({BotUsers.bank:BotUsers.bank - qData[0][0]})
                session.commit()
                return True
            except:
                raise
        

    # #Pay
    async def queryPay(self,qData): #qData expects [(pay_amount,member_id)]
        try:
            Session = sessionmaker(bind=engine)
            session = Session()
            query_result = session.query(BotUsers).filter(BotUsers.user_id == qData[0][1]).update({BotUsers.bank: BotUsers.bank + qData[0][0] })
            session.commit()
            return True
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
        try:
            Session = sessionmaker(bind=engine)
            session = Session()

            query_result = session.query(BotUsers).filter(BotUsers.user_id == qData[0][0]).update({BotUsers.last_dole:datetime.now()})



            session.commit()
        except:
            raise
        await self.queryPay([(self.bot.dolePayment,qData[0][0])]) #Tie dole payments to setting

    #Dole checker. This returns their dict of bank value, and allow/disallow dole claim {value,binary allowed/blocked}


    async def queryCheckDole(self,qData): #qData expects (member.id,)
        try:
            Session = sessionmaker(bind=engine)
            session = Session()

            query_result = session.query(BotUsers).filter(BotUsers.user_id == qData[0]).one_or_none()

            if query_result:
                next_dole = timedelta(seconds=0)
                if query_result.last_dole == None:
                    allow = True

                else:
                    if (datetime.now() - query_result.last_dole) > timedelta(seconds=self.bot.doleTimeout) and query_result.bank < self.bot.doleLimit:
                        allow = True
                    else:
                        allow = False
                        next_dole = (timedelta(seconds=self.bot.doleTimeout) -  (datetime.now() - query_result.last_dole))

                return {
                    "balance":query_result.bank,
                    "allow":allow,
                    "nextdole": next_dole
                }
            else:
                raise
        except:
            raise

#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(sql(bot))
