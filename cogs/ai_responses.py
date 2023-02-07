import openai

from discord.ext import commands

#########################
#       Extension       #
#########################

class ai_responses(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    #########################
    #    EVENT LISTENERS    #
    #########################

 #AI Responses

    @commands.Cog.listener()
    async def on_bot_mentioned(self, message):
        #Start simulating typing for extra immersion
        async with message.channel.typing():
            #prompt = message.content.removeprefix(self.bot.user.mention).strip()
            if self.bot.user.mention in message.content:
                prompt = message.content[len(self.bot.user.mention):].strip()
            else:
                prompt = message.content
            openai.api_key = self.bot.ai_key
            max_tokens = self.bot.ai_tokens_default
            model = self.bot.ai_model

            #Check moderation first
            moderation_response = openai.Moderation.create(
                input=prompt
            )
            #If it's naughty, then stop, and log reason
            if moderation_response['results'][0]['flagged']:
                naughty_string = ''
                for category,flag in moderation_response['results'][0]['categories'].items():
                    if flag:
                        naughty_string += category + ","
                naughty_string = naughty_string[:-1]
            
                self.bot.dispatch('log',
                f"OpenAI: {message.author} attempted to use AI but was moderated on input: '{prompt}'. Flagged categories: {naughty_string}")
                await message.reply("I'm not responding to that")
                return


            #Give fish extra powers! wow lucky fish !
            if message.author.id == 195114381820952577:
                max_tokens = self.bot.ai_tokens_fish

            #Create the response itself
            response = openai.Completion.create(
                model=model,
                prompt=prompt,
                temperature=0.9,
                max_tokens=max_tokens)

            response_text = response['choices'][0]['text'].strip()[:2000]

            self.bot.dispatch('log',
            f"OpenAI: {message.author} used the AI. Sent prompt: '{prompt}', Response: '{response_text}, Usage(promt,reply,total): {response['usage']['prompt_tokens']}, {response['usage']['completion_tokens']}, {response['usage']['total_tokens']}")

        #Stop typing, and send reply 
        await message.reply(response_text)


#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(ai_responses(bot))