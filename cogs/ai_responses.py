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

    #Handle bot mentions
    @commands.Cog.listener()
    async def on_bot_mentioned(self, message):
        if not self.bot.ai_toggle: return

        #Check if message is reply to an existing bot msg (conversation trigger)
        is_reply = True if message.reference is not None else False

        #Start simulating typing for extra immersion
        async with message.channel.typing():
            if self.bot.user.mention in message.content:
                prompt = message.content[len(self.bot.user.mention):].strip()
            else:
                prompt = message.content

            openai.api_key = self.bot.ai_key
            max_tokens = self.bot.ai_tokens_default
            model = self.bot.ai_model

            #Pretty pictures :)
            if prompt.lower().startswith("draw "):
                prompt = prompt[5:]
                self.bot.dispatch("ai_image", message, prompt)
                return

            #Check moderation first
            moderation_response = openai.moderations.create(
                input=prompt
            )
            #If it's naughty, then stop, and log reason
            if moderation_response.results[0].flagged:
                naughty_string = ''
                for category,flag in moderation_response.results[0].categories:
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

            #Check if message is a response & create conversation
            ai_messages= [{"role":"system", "content":self.bot.ai_sysprompt}]
            if is_reply:
                sql_cog = self.bot.get_cog('sql')
                resp = await sql_cog.queryAIMessages(message_id = message.reference.message_id)
                msglog = resp['log']
                base_message_id = resp['base_message_id']

                for line in msglog:
                    ai_messages.append({
                        'role':line['role'],
                        'content':line['text']
                    })

            else:
                base_message_id = message.id
            
            ai_messages.append({"role":"user", "content":prompt})

            #Create the response
            response = openai.chat.completions.create(
                model=model,
                #prompt=prompt,
                messages=ai_messages,
                temperature=0.9,
                max_tokens=max_tokens)

            response_text = response.choices[0].message.content.strip()[:2000]

            self.bot.dispatch('log',
            f"OpenAI: {message.author} used the AI. Sent prompt: '{prompt}', Response: '{response_text}, Usage(promt,reply,total): {response.usage.prompt_tokens}, {response.usage.completion_tokens}, {response.usage.total_tokens}")

            self.bot.dispatch('queryAILog', user_id = message.author.id, ai_type = 'text', tokens = response.usage.total_tokens)
            self.bot.dispatch('queryAIMessageAdd', base_message_id=base_message_id, message_id=message.id, user_id=message.author.id, role='user', message_text=prompt)

        #Stop typing, and send reply 
        reply_message = await message.reply(response_text)
        #Add the bot reply to the log
        self.bot.dispatch('queryAIMessageAdd', base_message_id = base_message_id, message_id=reply_message.id, user_id=self.bot.user.id, role='assistant', message_text=response_text)

    #Image generation
    @commands.Cog.listener()
    async def on_ai_image(self, message, prompt):

        try:
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024")
        except openai.OpenAIError as e:
            self.bot.dispatch('log',
            f"OpenAI: {message.author} attempted to use image AI but was moderated on input: '{prompt}'. Error: '{e}'")
            await message.reply("I'm not responding to that")
            return

        
        image_url = response.data[0].url
        
        self.bot.dispatch('log',
        f"OpenAI: {message.author} used the AI to generate an image. Prompt: '{prompt}', Image url: '{image_url}'")
        #1 image cost = $0.04, same as 2500 response tokens
        self.bot.dispatch('queryAILog', user_id = message.author.id, ai_type = 'image', tokens = 2500)

        await message.reply(image_url)
        

#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(ai_responses(bot))
