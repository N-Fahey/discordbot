import requests
import os
import json

from discord.ext import commands,tasks
from dotenv import load_dotenv
from pathlib import Path

#########################
#         Class         #
#########################

class DashcamFile():
    def __init__(self, filepath):
        self._path = Path(filepath)

        #Create file if doesnt exist
        if not self._path.exists():
            #Create folders
            self._path.parent.mkdir(exist_ok=True, parents=True)

            dc_dict = {
                    'latest': '',
                    'compilation': ''
                }
            #Create json file
            with self._path.open('w') as dc_file:                
                json.dump(dc_dict, dc_file, indent=4)                
                ('Youtube: Created dashcam file')
        
        #Load file contents as attr
        self._json = self._read_file()

    def _read_file(self):
        with self._path.open('r') as dc_file:
            dc_json = json.load(dc_file)
            return dc_json
    
    def read(self):
        return self._json

    def update_file(self, latest_link:str, compilation:bool = False):
        new_json = dict(self._json)
        
        new_json['latest'] = latest_link
        if compilation:
            new_json['compilation'] = latest_link

        #Exit if unchanged
        if new_json == self._json:
            return

        #Update attribute & save file
        self._json = new_json
        with self._path.open('w') as dc_file:
            json.dump(self._json, dc_file, indent=4)

#########################
#       Functions       #
#########################

async def process_dashcam_update(dashcam_file:DashcamFile):
    load_dotenv()
    APIKEY = os.getenv("GOOGLE_API_KEY")
    # ID for the 'all uploads' playlist of DCOA channel
    PLAYLISTID = 'UUvfqpaehdaqtkXPNhvJRyGA'

    #Get most recent video id
    req = requests.get(f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=1&playlistId={PLAYLISTID}&key={APIKEY}")
    response = str(req.json()['items'][0]['contentDetails']['videoId'])
    latest_link = "https://youtu.be/" + response
    
    dc_json = dashcam_file.read()
    old_latest = dc_json['latest']

    if old_latest == latest_link:
        return {'updated': False}
    
    #Search video title only if changed
    search_request = requests.get(f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id={response}&key={APIKEY}")
    latest_title = str(search_request.json()['items'][0]['snippet']['title'])

    is_compilation = "compilation" in latest_title.lower()

    dashcam_file.update_file(latest_link, compilation=is_compilation)

    return {
        'updated': True,
        'video': {
            'is_compilation': is_compilation,
            'link': latest_link
        }
    }

#########################
#       Extension       #
#########################

class youtube(commands.Cog):
    def __init__(self,bot):
        DASHCAM_FILEPATH = 'data/dashcams.json'

        self.bot = bot
        self.bot.dashcam_file = DashcamFile(DASHCAM_FILEPATH)
        self.checker.start()
    
    def cog_unload(self):
        self.checker.cancel()

    @tasks.loop(minutes=5)
    async def checker(self):
        dashcam_update = await process_dashcam_update(self.bot.dashcam_file)
        if not dashcam_update['updated']:
            self.bot.dispatch("log","youtube: Checked for update. No change.")
            return
        
        #There was an update - but not comp
        if not dashcam_update['video']['is_compilation']:
            self.bot.dispatch("log","youtube: Dashcams updated, but not compilation.")
            await self.bot.get_user(195114381820952577).send(f"Dashcam update, but not compilation :( {dashcam_update['video']['link']}")
            return

        #New comp
        self.bot.dispatch("log","youtube: Dashcams update! Dispatching to first text channel")
        await self.bot.guild.text_channels[0].send(f"@everyone DASHCAMS DASHCAMS DASHCAMS {dashcam_update['video']['link']}")
    
    @checker.before_loop
    async def before_checker(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name="dc",help="Resend the most recent dashcam compilation")
    async def dc(self,ctx):        
        dashcam_links = self.bot.dashcam_file.read()
        
        await ctx.reply(f"DASHCAMS DASHCAMS DASHCAMS {dashcam_links['compilation']}")

#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(youtube(bot))