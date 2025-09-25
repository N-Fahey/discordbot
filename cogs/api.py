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

    async def _get(self, endpoint:str, params:dict | None = None) -> dict:
        async with self.session.get(url=endpoint, params=params) as resp:
            if not resp.ok:
                #TODO: Error handling
                print('Error: ', resp.status) #temp

            json = await resp.json()

            return {
                'success': resp.ok,
                'json': json
            }

    async def _post(self, endpoint:str, data:dict | None = None) -> dict:
        async with self.session.post(url=endpoint, json=data) as resp:
            if not resp.ok:
                #TODO: Error handling
                print('Error: ', resp.status) #temp
            
            json = await resp.json()
            
            return {
                'success': resp.ok,
                'json': json
            }

    #########################
    #           AI          #
    #########################

    async def get_conversation(self, message_id:int):
        params = {
            'message_id': message_id
        }

        return await self._get('ai/messages/get_conversation', params=params)

    async def ai_add_message(self, uid:int, conversation_id:int, message_id:int, msg:str):
        json = {
            'uid': uid,
            'conversation_id': conversation_id,
            'message_id': message_id,
            'text': msg
        }

        return await self._post('ai/messages/add_message', data=json)
    
    async def ai_add_usage(self, uid:int, type:str, tokens:int):
        json = {
            'uid': uid,
            'type': type,
            'tokens': tokens
        }

        return await self._post('ai/usage/add_usage', data=json)
    

    #########################
    #          Bank         #
    #########################

    async def get_balance(self, uid:int):
        params = {
            'user_id': uid
        }

        return await self._get('bank/get_balance', params=params)
    
    async def get_balances(self, count:int = 0):
        params = {
            'num_balances': count
        }

        return await self._get('bank/get_balances', params=params)
    
    async def get_dole(self, uid:int):
        params = {
            'user_id': uid
        }

        return await self._get('bank/get_dole', params=params)
    
    async def bank_deposit(self, uid:int, amount:int):
        params = {
            'uid': uid,
            'amount': amount
        }
        
        return await self._get('bank/deposit', params=params)
    
    async def bank_withdraw(self, uid:int, amount:int):
        params = {
            'uid': uid,
            'amount': amount
        }
        
        return await self._get('bank/withdraw', params=params)

    async def bank_transfer(self, from_uid:int, to_uid:int, amount:int):
        params = {
            'from_uid': from_uid,
            'to_uid': to_uid,
            'amount': amount
        }
        
        return await self._get('bank/transfer', params=params)
    

    #########################
    #          Games        #
    #########################

    async def add_game(self, game_name:str):
        json = {
            'game_name': game_name
        }

        return await self._post('games/add_game', data=json)


    #########################
    #         Scores        #
    #########################

    async def add_score(self, uid:int, game_name:str, amount_won:int | None = None):
        json = {
            'uid': uid,
            'game_name': game_name,
            'amount_won': amount_won
        }

        return await self._post('scores/add_score', data=json)


    #########################
    #         Users         #
    #########################

    async def get_user(self, uid:int):
        params = {
            'user_id': uid
        }
        return await self._get('users/get_user', params=params)

    async def get_all_users(self):
        return await self._get('users/get_users')
    
    async def add_user(self, uid:int, username:str, display_name:str):
        json = {
            'uid': uid,
            'username': username,
            'display_name': display_name
        }

        return await self._post('users/create_user', data=json)
    
    #TODO: Update user


#########################
#       Extension       #
#########################

class api(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.bot.api = APIWrapper()

    @commands.Cog.listener()
    async def on_populate_db(self):
        #TODO: Add updating user logic
        async with self.bot.api as api:
            res = await api.get_all_users()

            if not res['success']:
                raise RuntimeError("Error retrieving users (on_populate_db)")
            
            db_users = res['json']['users']
            db_uids = {user['uid'] for user in db_users}

            for member in self.bot.guild.members:
                if member.bot:
                    continue

                if member.id not in db_uids:
                    res = await api.add_user(member.id, member.name, member.display_name)

                    if not res['success']:
                        raise RuntimeError(f"Error adding user (on_populate_db): {member.name}, uid: {member.id}")
                    
                    self.bot.dispatch('log', f'api: Created user {member.name}')
                    

    @commands.command(name="testapi")
    async def test(self, ctx):
        self.bot.dispatch('populate_db')
        # async with self.bot.api as api:
        #     res = await api.add_user(ctx.author.id, ctx.author.name, ctx.author.display_name)
        
        # print(res)

#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(api(bot))