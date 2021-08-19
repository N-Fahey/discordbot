from discord.ext import commands,timers
from discord import Embed,Member,FFmpegPCMAudio
import time,os
#########################
#       Extension       #
#########################



class audiobites(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.bot.audio_bite_cooldown = None
    #kill_lobby
    @commands.command(name="audio",help="play an audio clip")
    async def audio_bite(self,ctx, bite):

        if self.bot.audio_bite_cooldown is None or (time.time() - self.bot.audio_bite_cooldown) > 0:
            dirs = os.listdir( "resources/sound/bites" )
            match = [i for i in dirs if bite in i]
            
            if len(match) == 1:
                voice_channel = ctx.author.voice.channel
                if voice_channel != None:
                    self.bot.audio_bite_cooldown = time.time() + self.bot.audio_bite_cooldown_seconds
                    vc = await voice_channel.connect()
                    vc.play(FFmpegPCMAudio(source=f"resources/sound/bites/{match[0]}"))
                    # Sleep while audio is playing.
                    while vc.is_playing():
                        time.sleep(.1)
                    await vc.disconnect()
                else:
                    await ctx.send(f"{ctx.author.mention} you're not in an audio channel")
                # Delete command after the audio is done playing.
                await ctx.message.delete()
            else:
                await ctx.send(f"{ctx.author.mention} audio file not found.")

        else:
            await ctx.send(f"{ctx.author.mention} audio command is on cooldown: {-int((time.time() - self.bot.audio_bite_cooldown))} seconds.")


        
#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(audiobites(bot))
