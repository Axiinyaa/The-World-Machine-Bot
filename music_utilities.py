# This file is used to clean up some of the functions in the main file.
import interactions
import datetime
from interactions.ext.wait_for import wait_for_component
import uuid
import random
import asyncio
import lavalink
import database_manager as db_manager

def setup_(self):
    global bot
    bot = self

async def GetButtons(guild_id):
    play_emoji = interactions.Emoji(name="playorpause", id=1019286927888883802)
    stop_emoji = interactions.Emoji(name="stopmusic", id=1019286931504386168)
    queue_emoji = interactions.Emoji(name="openqueue", id = 1019286929059086418)
    loop_song_emoji = interactions.Emoji(name="loopsong", id=1019286926404091914)
    skip_emoji = interactions.Emoji(name="skipmusic", id=1019286930296410133)

    print(guild_id)
    
    return [
        # Queue Button
        interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            emoji = queue_emoji,
            custom_id = f"queue {guild_id}",
        ),
        # Loop Button
        interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            custom_id = f"loop {guild_id}",
            emoji = loop_song_emoji,
        ),

        # Play Button
        interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            custom_id = f"play {guild_id}",
            emoji = play_emoji,
        ),
        # Skip Button
        interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            custom_id = f"skip {guild_id}",
            emoji = skip_emoji
        ),
        # Stop Button
        interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            custom_id = f"stop {guild_id}",
            emoji = stop_emoji
        ),
    ]

async def GenerateEmbed(id : str, player, show_timeline):
    if (player.is_playing):
        current_length = player.position / 1000
        song_length = player.current.duration / 1000
    
        l_length = list("█░░░░░░░░░░░░░░░░░░░░")
        
        calc_length = round((current_length / song_length) * len(l_length))
    
        i = 0
    
        new_c_length = datetime.datetime.fromtimestamp(current_length).strftime('%M:%S')
        new_length = datetime.datetime.fromtimestamp(song_length).strftime('%M:%S')
        
        for char in l_length:
            if (i < calc_length):
                l_length[i] = "█"
            i += 1
        
        length = "".join(l_length)
    
        if (show_timeline):
            return interactions.Embed(
                title = f"**Now Playing:** [{player.current.title}]",
                thumbnail = interactions.EmbedImageStruct( url = f"https://i3.ytimg.com/vi/{id}/maxresdefault.jpg", height = 720, width = 1280),
                description = f"{length} \n\n *{new_c_length} / {new_length}*",
                footer = interactions.EmbedFooter( text = 'Do /music get_player if the buttons don\'t work or if you\'ve lost the player.'),
                url = player.current.uri
            )
        else:
            return interactions.Embed(
                title = f"**Now Playing:** [{player.current.title}]",
                thumbnail = interactions.EmbedImageStruct( url = f"https://i3.ytimg.com/vi/{id}/maxresdefault.jpg", height = 720, width = 1280),
                description = f"Loading Player... <a:loading:1026539890382483576> \n\n *00:00 / {new_length}*",
                footer = interactions.EmbedFooter( text = 'Do /music get_player if the buttons don\'t work or if you\'ve lost the player.'),
                url = player.current.uri
            )

async def GenerateQueue(page_number, player):
    full_queue = player.queue
    list_ = ""

    items_pi = 10

    starting_index = (items_pi * (page_number + 1)) - items_pi
    queue = full_queue[starting_index : starting_index + items_pi] # From 0 to 20


    try:
        for song in queue:
            time = datetime.datetime.fromtimestamp(song.duration / 1000).strftime('%M:%S')
            list_ = f"{list_}**{queue.index(song) + 1}.** `{song.title}` *({time})*\n"
    except:
        pass
    
    if (len(list_) > 0):
        return interactions.Embed(
        title = "Music Queue",
        description = f"\n**Currently Playing:** `{player.current.title}`\n\n",
        thumbnail = interactions.EmbedImageStruct( url = "https://shortcut-test2.s3.amazonaws.com/uploads/role/attachment/346765/default_Enlarged_sunicon.png" ),
        fields = [
            interactions.EmbedField(
                name = "Song List",
                value = list_,
                inline = True
                )
            ]
        )
    else:
        return interactions.Embed(
        title = "Music Queue",
        description = f"\n**Currently Playing:** `{player.current.title}`\n\n",
        thumbnail = interactions.EmbedImageStruct( url = "https://shortcut-test2.s3.amazonaws.com/uploads/role/attachment/346765/default_Enlarged_sunicon.png" ),
        fields = [
            interactions.EmbedField(
                name = "Song List",
                value = 'Queue is empty!',
                inline = True
                )
            ]
        )


async def ShowPlayer(ctx : interactions.CommandContext, player : lavalink.DefaultPlayer, show_timeline : bool):
    message = ""
    
    player_id = uuid.uuid4()
    
    default_data = {'guild_id' : int(ctx.guild_id), 'player_id' : str(player_id)}
    await db_manager.GetDatabase(int(ctx.guild_id), 'current_players', default_data)   
    db = await db_manager.SetDatabase(int(ctx.guild_id), 'current_players', 'player_id', str(player_id))

    msg = await ctx.send('Loading Player... <a:loading:1026539890382483576>')
    niko = '<a:vibe:1027325436360929300>'
    
    if (player.is_playing):
        embed = await GenerateEmbed(player.current.identifier, player, show_timeline)
        buttons = await GetButtons(msg.id)
        msg = await msg.edit(niko, embeds=embed, components=buttons)
    else:
        embed = interactions.Embed(
                title = "Not Currently Playing Anything",
                thumbnail = interactions.EmbedImageStruct( url = "https://shortcut-test2.s3.amazonaws.com/uploads/role/attachment/346765/default_Enlarged_sunicon.png"),
                description = "Use /play music to add music."
            )
        
        await ctx.send(embeds=embed)
        return

    async def check(ctx):
        if (not ctx.author.voice.joined):
            await ctx.send('Sorry! But you need to be in the voice call in order to use these buttons!', ephemeral=True)
            return False
        else:
            return True

    song_ = player.current
    
    message = {'niko' : niko, 'message' : ''}
    
    while True:
        
        button_ctx = msg
        task = asyncio.create_task(wait_for_component(bot, components=buttons, check=check))
        
        while True:
            done, pending = await asyncio.wait({task}, timeout=2)
            
            if not done:
                
                db = await db_manager.GetDatabase(int(ctx.guild_id), 'current_players', default_data)   
                
                if player.current != song_:
                    await button_ctx.edit('<:nikosleepy:1027492467337080872> `Song Ended.`', embeds = [], components = [])
                    return
                
                if db['player_id'] != str(player_id):
                    await button_ctx.edit('<:nikosleepy:1027492467337080872> `Player Moved.`', embeds = [], components = [])
                    return
                
                if not player.paused and player.is_playing:
                    funny_embed = await GenerateEmbed(player.current.identifier, player, True)
                    funny_embed.set_author(name = message['message'])
                    await button_ctx.edit(message['niko'], embeds = funny_embed, components = buttons)
                continue  # very important!
                
            button_ctx = task.result()
            message = await ButtonManager(niko, msg, ctx, button_ctx, player)
            break
            
async def ButtonManager(niko, msg, ctx, button_ctx, player):
    
    message = ''
    
    data = button_ctx.data.custom_id
            
    if (data == f"play {msg.id}"):
        is_paused = player.fetch("is_paused")
        
        if not (is_paused):
            await player.set_pause(True)
            player.store("is_paused", True)
            message = "Paused the current track playing."
            niko = '<:nikosleepy:1027492467337080872>'
        elif (is_paused):
            await player.set_pause(False)
            player.store("is_paused", False)
            message = "Resumed the current track playing."
            niko = '<a:vibe:1027325436360929300>'
    elif (data == f"skip {msg.id}"):
        await button_ctx.edit('<:nikosleepy:1027492467337080872> `Song Skipped.`', embeds=[], components =[])
        await player.skip()
    elif (data == f"queue {msg.id}"):
        if (len(player.queue) > 0):
            await button_ctx.edit('Queue was opened, to get the player back, do </music get_player:1030977228885987419>.', components=[])
            id = uuid.uuid4()
            
            options = []
            i = 0

            for song in player.queue:
                if (i < 10):
                    options.append(
                        interactions.SelectOption(
                            label = f'{i + 1}. {song.title}',
                            value = i
                        )
                    )

                i += 1

            select = interactions.SelectMenu(
                options=options,
                placeholder= 'What Song?',
                custom_id="woo",
            )
            
            queue = await GenerateQueue(0, player)

            control_buttons = [
                interactions.Button(
                    label= "Prev. Page",
                    style = interactions.ButtonStyle.PRIMARY,
                    custom_id = f"b {str(id)}",
                    disabled = True,
                ),
                interactions.Button(
                    label="Next Page",
                    style = interactions.ButtonStyle.PRIMARY,
                    custom_id = f"n {str(id)}",
                    disabled = True,
                ),
            ]

            button_ = [
                interactions.Button(
                    label="Shuffle",
                    style = interactions.ButtonStyle.PRIMARY,
                    custom_id = f"shuffle {str(id)}"
                ),
                interactions.Button(
                    label="Remove Song",
                    style = interactions.ButtonStyle.DANGER,
                    custom_id = f"remove {str(id)}"
                ),
                interactions.Button(
                    label="Jump To...",
                    style = interactions.ButtonStyle.SUCCESS,
                    custom_id = f'jump {str(id)}'
                ),
            ]

            row1 = interactions.ActionRow(components=button_)
            row2 = interactions.ActionRow(components=control_buttons)
            
            funny_message = await button_ctx.send(embeds = queue, components=[row1, row2])

            async def checkers(ctx):
                return True

            while True:
                shuffle_ctx = await wait_for_component(bot, components = [row1, row2], check=checkers)

                if (shuffle_ctx.data.custom_id == f'shuffle {str(id)}'):
                    random.shuffle(player.queue)
                
                    queue = await GenerateQueue(0, player)
                    await shuffle_ctx.edit('`Shuffled Queue.`', embeds = queue, components=button_)
                if (shuffle_ctx.data.custom_id == f'remove {str(id)}'):
                    await shuffle_ctx.send(components=select, ephemeral = True)

                    contexto : interactions.ComponentContext = await wait_for_component(bot, components = select, check=checkers)

                    song_ = player.queue.pop(int(contexto.data.values[0]))

                    queue_ = await GenerateQueue(0, player)
                    await funny_message.edit(f'<@{contexto.author.id}> removed {song_.title} from the queue.', embeds = queue_, components=button_)
                    await contexto.send(f'Successfully removed {song_.title} from the queue.', ephemeral = True)
                if (shuffle_ctx.data.custom_id == f'jump {str(id)}'):
                    await shuffle_ctx.send(components=select, ephemeral = True)

                    contexto : interactions.ComponentContext = await wait_for_component(bot, components = select, check=checkers)

                    song_ = player.queue[int(contexto.data.values[0])]
                    
                    queue_ = await GenerateQueue(0, player)
                    await funny_message.edit(f'<@{contexto.author.id}> jumped to {song_.title}.', embeds = queue_, components=button_)
                    await contexto.send(f'Successfully jumped to {song_.title}.', ephemeral = True)

                    del player.queue[0 : int(contexto.data.values[0])]
                    
                    await player.play(song_)
        else:
            message = "Queue is currently empty :("
    elif (data == f"stop {msg.id}"):
        await button_ctx.edit('<:nikosleepy:1027492467337080872> `Song Stopped.`', embeds=[], components =[])
        await bot.disconnect(ctx.guild_id)
    elif (data == f"loop {msg.id}"):
        if not (player.repeat):
            player.set_repeat(True)
            message = "Looping Queue!"
        else:
            player.set_repeat(False)
            message = "Loop Stopped!"
        
    funny_embed = await GenerateEmbed(player.current.identifier, player, True)
    funny_embed.set_author(name = message)
    await button_ctx.edit(niko, embeds = funny_embed)
    
    return {'niko' : niko, 'message' : message}