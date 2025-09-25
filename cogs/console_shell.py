import cmd,re
from aioconsole import ainput
from discord.ext import commands
from discord import TextChannel

class CmdShell(cmd.Cmd):
    prompt = '>> '
    intro = 'Hello, and welcome!'

    def __init__(self,bot):
        super().__init__()
        self.bot = bot
        self.channels = None
        self.bank = []

    def get_mention_string(self,match):
        try:
            mention = self.bot.guild.get_member_named(match[0][1:]).mention
            return mention
        except:
            return match[0]

    async def onecmd(self,line):
        cmd,arg,line = self.parseline(line)
        if not line:
            return self.emptyline()
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        if line == 'EOF' :
            self.lastcmd = ''
        if cmd == '':
            return self.default(line)
        else:
            try:
                func = getattr(self, 'do_' + cmd)
            except AttributeError:
                return self.default(line)
            if cmd == 'help':
                return func(arg)
            else:
                return await func(arg)

    #Override default emptyline behaviour
    def emptyline(self):
        pass

    #######################
    #   CUSTOM COMMANDS   #
    #######################

    #List channels
    async def do_channels(self,arg):
        'Prints a list of all the channels available on the primary server. Use provided index to send message using say command'
        self.channels = [i for i in self.bot.guild.channels if isinstance(i,TextChannel)]
        print('\n'.join([str(i)+': '+channel.name for i,channel in enumerate(self.channels)]))
    
    #Send message to specified channel
    async def do_say(self,args):
        'Send a message to the specified channel. Use channels to retrieve list of options'
        if self.channels is None:
            print('Use channels first to generate channel list')
            return
        arg_list = args.split(' ',1)

        try:
            arg_list[0] = int(arg_list[0])
        except ValueError as error:
            print(f'Unable to convert: {error.args[0]}. Please try again')
            return

        if 0 <= arg_list[0] <= len(self.channels) - 1:
            #Replace @name with internal mention string for tagging people            
            arg_list[1] = re.sub(r'@\S*',self.get_mention_string,arg_list[1])
            self.bot.dispatch("sendReply",self.channels[arg_list[0]],arg_list[1])
        else:
            print("Didn't recognise that index. Use channels for current list")
    
    #List & administrate lobbies
    async def do_lobby(self,args):
        'View or administrate lobbies. Usage: lobby [list/kill/end] [id]'
        lobbies = [i for i in self.bot.game_lobbies]
        lobby_options = ['list','kill','end']

        if args == '':
            print(f"Incomplete command. Options: {' '.join(lobby_options)}")
            return
        
        arg_list = args.split(' ')

        if len(arg_list) == 1 and arg_list[0] == 'list':
            if len(lobbies) == 0:
                print("No active lobbies")
            else:
                print('\n'.join(str(i) + ': ' + lobby.lobby_owner.name + ', ' + lobby.game_type for i,lobby in enumerate(lobbies)))
        elif len(arg_list) == 2:
            try:
                arg_list[1] = int(arg_list[1])
            except ValueError as error:
                print(f'Unable to convert: {error.args[0]}. Please try again')
                return
            if 0 <= arg_list[1] < len(lobbies):
                if arg_list[0] == 'kill':
                    self.bot.game_lobbies.remove(lobbies[arg_list[1]])
                    print("Lobby removed from lobbies list")
                elif arg_list[0] == 'end':
                    self.bot.loop.create_task(self.bot.get_cog('lobby').lobby_end_game(lobbies[arg_list[1]],None))
                    print("Attempting to end lobby.")
                else:
                    print(f"Command {arg_list[0]} not recognised. Options: kill end")
            else:
                print("Unrecognised index.")
        else:
            print("Incorrect argument length. Usage: lobby [list/kill/end] [id]")

    #Admin cog commands
    async def do_admin(self,args):
        'Admin cog commands. Do admin help for list of options'
        options = ['help','reset','reload','populatedb']
        if args == '':
            print(f"Admin options: {' '.join(options)}")
            return
        
        args_list = args.split(' ')
        if len(args_list) == 1 and args_list[0] in options:
            if args_list[0] == 'help':
                print(f"Admin options: {' '.join(options)}")
            elif args_list[0] == 'reset':
                self.bot.dispatch("reset")
                print("Bot attributes reset")
            elif args_list[0] == 'reload':
                self.bot.dispatch("reload",None)
                print("Reloading extensions...")
            elif args_list[0] == 'populatedb':
                self.bot.dispatch("populate_db")
                print("DB populating...")
            else:
                raise RuntimeError("Something went fucky")
        else:
            print(f"Unrecognised command. Options: {' '.join(options)}")

    async def do_currency(self,args):
        'Currency cog commands. Do currency help for list of options'
        options = ['bank','pay','withdraw']

        if args == '' or args == 'help':
            print(f"Currency options: {', '.join(options)}\n  bank to generate & view member list\n  pay [id] [amount] to pay a user\n  withdraw [id] [amount] to withdraw from user")
            return
        
        arg_list = args.split(' ')
        
        if len(arg_list) == 1 and arg_list[0] in options:

            if arg_list[0] == 'bank':
                async with self.bot.api as api:
                    res = await api.get_balances(0)
                
                balances = res['json']['balances']

                self.bank = []
                for balance in balances:
                    member_object = self.bot.guild.get_member(balance['uid'])
                    if member_object is not None:
                        self.bank.append({
                            'member': member_object,
                            'bank': balance['balance']
                            })

                print('id'.ljust(2),'Name'.ljust(15),'Bank')

                for index,bank_dict in enumerate(self.bank):
                    print(str(index).ljust(2),bank_dict['member'].name.ljust(15),bank_dict['bank'])
            else:
                print("Incomplete command. Use currency help for info.")

        elif len(arg_list) == 3 and arg_list[0] in options:
            try:
                arg_list[1] = int(arg_list[1])
                arg_list[2] = int(arg_list[2])
            except ValueError as error:
                print(f'Unable to convert: {error.args[0]}. Please try again')
                return
            
            if self.bank == []:
                print('Run bank first to get list of members')
                return

            sql_cog = self.bot.get_cog('sql')
            if 0 <= arg_list[1] < len(self.bank):
                if arg_list[0] == 'pay':
                    async with self.bot.api as api:
                        res = api.bank_deposit(self.bank[arg_list[1]]['member'].id,arg_list[2])

                    print(f"Successfully paid {arg_list[2]} to user {self.bank[arg_list[1]]['member'].name}.")
                 
                elif arg_list[0] == 'withdraw':
                    async with self.bot.api as api:
                        result = await api.try_withdraw(self.bank[arg_list[1]]['member'].id, arg_list[2])

                    if not result:
                        print(f"Can't withdraw {arg_list[2]} from user {self.bank[arg_list[1]]['member'].name}. Balance too low")
                        return

                    print(f"Successfully withdrew {arg_list[2]} from user {self.bank[arg_list[1]]['member'].name}.")
            else:
                print("Unrecognised index. Run currency bank & then currency [pay/withdraw] [id] [amount].")
        else:
            print(f"Unrecognised command. Use currency help for instructions.")

    
    #Exec any code
    async def do_exec(self,args):
        'Exec code. Not restricted to bot. Use self.bot to refer to bot'
        exec(args)

class console_shell(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.handler = CmdShell(self.bot)

    async def console_handler(self):
        while True:
            cmd_input = await ainput('>> ')
            await self.handler.onecmd(cmd_input)

#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(console_shell(bot))