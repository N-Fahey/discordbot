import aiohttp
import os

from datetime import datetime, timedelta
from dotenv import load_dotenv
from discord.ext import commands
from time import perf_counter

#########################
#        Wrapper        #
#########################

class APIWrapper:
    def __init__(self, bot: commands.Bot):
        load_dotenv()
        self._base_url = os.getenv('BOT_API_URL')
        self.__headers = {
            'X-API-KEY': os.getenv('BOT_API_KEY')
        }
        self.bot = bot
        self.session = None

    async def setup(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(base_url=self._base_url, headers=self.__headers)
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def _get(self, endpoint:str, params:dict | None = None) -> dict:
        req_start = perf_counter()
        async with self.session.get(url=endpoint, params=params) as resp:
            if not resp.ok:
                self.bot.dispatch('error', f'api: GET {endpoint} {resp.status}. Params: {params}')
                return

            json = await resp.json()
            
            req_end = perf_counter()
            self.bot.dispatch('log', f'api: GET {endpoint} {resp.status} {(req_end - req_start)*1000:.0f}ms. Params: {params}')
            return {
                'success': resp.ok,
                'json': json
            }

    async def _post(self, endpoint:str, data:dict | None = None) -> dict:
        req_start = perf_counter()
        async with self.session.post(url=endpoint, json=data) as resp:
            if not resp.ok:
                self.bot.dispatch('error', f'api: POST {endpoint} {resp.status}. Data: {data}')
                return
            
            json = await resp.json()
            
            req_end = perf_counter()
            self.bot.dispatch('log', f'api: POST {endpoint} {resp.status} {(req_end - req_start)*1000:.0f}ms. Data: {data}')
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

    async def ai_add_message(self, uid:int | None, conversation_id:int, message_id:int, msg:str):
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
    
    async def _get_dole_timestamp(self, uid:int):
        params = {
            'user_id': uid
        }

        return await self._get('bank/get_dole', params=params)
    
    async def _update_dole_timestamp(self, uid:int):
        json = {
            'uid': uid
        }
        return await self._post('bank/update_dole', data=json)
    
    async def try_dole(self, uid:int, dole_amount:int, dole_limit:int):
        res = await self.get_balance(uid)
        if res['json']['balance'] >= dole_limit:
            return {
                'success': False,
                'reason': 'balance'
            }
        
        res = await self._get_dole_timestamp(uid)
        last_dole = datetime.strptime(res['json']['last_dole'], '%Y-%m-%dT%H:%M:%S')

        if datetime.now().date() - last_dole.date() < timedelta(days=1):
            return {
                'success': False,
                'reason': 'time',
                'delta': datetime.now() - last_dole
            }
        
        result = await self.bank_deposit(uid, dole_amount)
        await self._update_dole_timestamp(uid)

        return {
            'success': True,
            'balance': result['json']['balance']
        }

    async def bank_deposit(self, uid:int, amount:int):
        json = {
            'uid': uid,
            'amount': amount
        }
        
        return await self._post('bank/deposit', data=json)
    
    async def _bank_withdraw(self, uid:int, amount:int):
        json = {
            'uid': uid,
            'amount': amount
        }
        
        return await self._post('bank/withdraw', data=json)

    async def try_withdraw(self, uid:int, amount:int):
        res = await self.get_balance(uid)
        balance = res['json']['balance']

        if balance < amount:
            return False
        
        await self._bank_withdraw(uid, amount)
        return True
    
    async def try_transfer(self, from_uid:int, to_uid:int, amount:int):
        withdraw_result = await self.try_withdraw(from_uid, amount)
        if not withdraw_result:
            return False
        
        await self.bank_deposit(to_uid, amount)
        return True

    #########################
    #          Games        #
    #########################

    async def get_games(self):

        return await self._get('games/get_games')

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
    
    async def update_user(self, uid:int, username:str | None = None, display_name:str | None = None):
        json = {
            'uid': uid,
            'username': username,
            'display_name': display_name
        }

        return await self._post('users/update_user', data=json) 


#########################
#       Extension       #
#########################

class api(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.bot.api = APIWrapper(self.bot)

    async def cog_load(self):
        await self.bot.api.setup()

    async def cog_unload(self):
        await self.bot.api.close()
    
    #########################
    #    Event Listeners    #
    #########################
    
    @commands.Cog.listener()
    async def on_verify_games(self):
        res = await self.bot.api.get_games()
        
        game_list = res['json']['games'] if res['success'] else []
        game_names = {game['name'] for game in game_list}
        

        for game in self.bot.prettyGames.keys():
            if game not in game_names:
                await self.bot.api.add_game(game)
        

    @commands.Cog.listener()
    async def on_populate_db(self):
        res = await self.bot.api.get_all_users()

        if not res['success']:
            raise RuntimeError("Error retrieving users (on_populate_db)")
        
        all_users = res['json']['users']
        db_uids = {user['uid'] for user in all_users}
        dict_users = {user['uid']: user for user in all_users}

        for member in self.bot.guild.members:
            if member.bot:
                continue
            
            #Create new
            if member.id not in db_uids:
                res = await self.bot.api.add_user(member.id, member.name, member.display_name)

                if not res['success']:
                    raise RuntimeError(f"Error adding user (on_populate_db): {member.name}, uid: {member.id}")
                
                continue
                
            #Update
            if dict_users[member.id]['username'] != member.name or dict_users[member.id]['display_name'] != member.display_name:
                res = await self.bot.api.update_user(member.id, member.name, member.display_name)

                if not res['success']:
                    raise RuntimeError(f"Error updating user (on_populate_db): {member.name}, uid: {member.id}")
                

#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(api(bot))