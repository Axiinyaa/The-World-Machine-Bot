from interactions import *
from error_handler import on_error
import profile_icons as icons
import aiohttp
import aiofiles
import dialogue_generator
from interactions.ext.database.database import Database

class Command(Extension):
    
    @extension_command(description = 'Put Command Description here.')
    @option(description = 'What you want the character to say.', max_length = 184)
    async def say(self, ctx : CommandContext, text : str):
        async def check(ctx):
            return True

        text__ = icons.Emojis()

        msg = await ctx.send(f"<@{ctx.author.id}>, select a character!", components=text__, ephemeral=True)
        
        char_ctx : ComponentContext = await self.client.wait_for_component(text__)

        text_ = None

        val_char : int = int(char_ctx.data.values[0])

        if (val_char == 0):
            text_ = await icons.GenerateModalNiko()
            
        elif (val_char == 1):
            print('lol')
            text_ = await icons.GenerateModalTWM()
            
        elif (val_char == 2):
            text_ = await icons.GenerateModalKip()

        await char_ctx.send(f"<@{ctx.author.id}>, select a text face!", components=text_[0], ephemeral=True)
        
        text_ctx : ComponentContext = await self.client.wait_for_component(text_[0])
        
        val = int(text_ctx.data.values[0])

        selection = text_[1][val] # this looks like ass but whatever

        emoji = selection.emoji.url

        msg = await text_ctx.send("[ Generating Image... <a:loading:1026539890382483576> ]")
        
        await dialogue_generator.test(text, emoji)
        await msg.delete()
        file = File(filename="Images/pil_text.png", description=text)
        await ctx.channel.send(f"Generated by: {ctx.author.name}", files=file)
        pass
    
    @say.error
    async def error(self, ctx : CommandContext, error):
        
        embed = await on_error(error)
        
        await ctx.send(embeds=embed)
        
def setup(client):
    Command(client)