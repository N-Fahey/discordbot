import requests,os
from discord.ext import commands,tasks
from dotenv import load_dotenv

#########################
#    Check Function     #
#########################

def checkDashCams():
    load_dotenv()
    APIKEY = os.getenv("GOOGLE_API_KEY") 
    #dashcams uploads playlist id: UUvfqpaehdaqtkXPNhvJRyGA
    req = requests.get(f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=1&playlistId=UUvfqpaehdaqtkXPNhvJRyGA&key={APIKEY}")
    response = str(req.json()['items'][0]['contentDetails']['videoId'])
    link = "https://youtu.be/" + response

    with open("cogs/dashcam.txt", "r+") as file:
        oldlink = file.read()

        if oldlink == link:
            return False
        else:
            cont = True
        
        if cont:
            searchreq = requests.get(f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id={response}&key={APIKEY}")
            searchresp = str(searchreq.json()['items'][0]['snippet']['title'])

            if "compilation" in searchresp.lower():
                compilation = True
            else:
                compilation = False

            file.truncate(0)
            file.seek(0)
            file.write(link)
            if compilation:
                return link
            else:
                return [link]

#########################
#       Extension       #
#########################

class youtube(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.checker.start()
    
    def cog_unload(self):
        self.checker.cancel()

    @tasks.loop(minutes=5)
    async def checker(self):
        res = checkDashCams()
        if res == False:
            self.bot.dispatch("log","youtube: Checked for update. No change.")
            return
        
        if isinstance(res,list):
            await self.bot.get_user(195114381820952577).send(f"Dashcam update, but not compilation :( {res[0]}")
            return

        self.bot.dispatch("log","youtube: Dashcams update! Dispatching to first text channel")
        await self.bot.guild.text_channels[0].send(f"@everyone DASHCAMS DASHCAMS DASHCAMS {res}")
    
    @checker.before_loop
    async def before_checker(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name="dc",help="Resend the most recent dashcam message")
    async def dc(self,ctx):
        with open('cogs/dashcam.txt','r') as dc_file:
            dc_link = dc_file.read()
        
        await ctx.reply(f"DASHCAMS DASHCAMS DASHCAMS {dc_link}")

#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(youtube(bot))