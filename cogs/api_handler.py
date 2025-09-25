import aiohttp
import os

from dotenv import load_dotenv
from discord.ext import commands

#########################
#        Wrapper        #
#########################

class APIWrapper:
    def __init__(self):
        load_dotenv()
        self._base_url = os.getenv('BOT_API_URL')
        self.__headers = {
            'X-API-KEY': os.getenv('BOT_API_KEY')
        }
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(base_url=self._base_url, headers=self.__headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get(self, endpoint:str, params:dict | None = None):
        async with self.session.get(url=endpoint, params=params) as resp:
            if not resp.ok:
                #Do something if error
                pass

            json = await resp.json()
            return json

    async def post(self, endpoint:str, data:dict | None = None):
        async with self.session.post(url=endpoint, json=data) as resp:
            if not resp.ok:
                #Do something if error
                pass
            
            json = await resp.json()
            return json


#########################
#       Extension       #
#########################

class api_handler(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.bot.api = APIWrapper()


#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(api_handler(bot))