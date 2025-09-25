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
    #TODO: Update to API - events.py, member updated & user updated
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


#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(sql(bot))
