import interactions
import os
import random
import lavalink
import datetime
import uuid
import re
import aiohttp        
import aiofiles
from replit import db

# Other Scripts
import custom_source
import dialogue_generator
import ask_responses
import profile_icons as icons
import generate_text

# Extension Libraries
from interactions.ext.wait_for import wait_for_component, setup, wait_for
from interactions.ext.lavalink import VoiceClient
from interactions.ext.files import command_send

TOKEN = os.environ['BOT-TOKEN']

try:
    bot = VoiceClient(token=TOKEN)
except:
    os.system('kill 1') # Prevents the bot from continously getting stuck on the same server.
    
bot.load('interactions.ext.files')

setup(bot)

responses = []

@bot.event()
async def on_start():
    global responses

    random.shuffle(responses)

    bot.lavalink_client.add_node(
        host = '51.161.130.134',
        port = 10333,
        password = 'youshallnotpass',
        region = "eu"
    ) # Woah, neat! Free Lavalink!
    
    bot.lavalink_client.add_event_hook(track_hook)

    await bot.change_presence(
        interactions.ClientPresence(
            status=interactions.StatusType.ONLINE,
            activities=[
                interactions.PresenceActivity(
                    name="over Niko",
                    type=interactions.PresenceActivityType.WATCHING)
            ]))

    await change_picture()
    
    print(f"{bot.me.name} is ready!")

async def change_picture():
    profile_pictures = icons.icons
    ran_num = random.randint(0, len(profile_pictures) - 1)
    picture = profile_pictures[ran_num]

    async with aiohttp.ClientSession() as session:
        url = picture
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open('Images/picture.png', mode='wb')
                await f.write(await resp.read())
                await f.close()

    image = interactions.Image("Images/picture.png")

    try:
        await bot.modify(avatar=image, username="The World Machine")
    except:
        print("Couldn't change avatar. Whoops, either way...")


@bot.command(name="say",
             description="Repeats whatever the user puts in.",
             options=[
                 interactions.Option(name="text",
                                     description="The text to repeat.",
                                     required=True,
                                     type=interactions.OptionType.STRING)
             ])
async def say_command(ctx: interactions.CommandContext, text: str):
  #stops the bot from mass pinging users
    if '@everyone' in text:
        text = text.replace('@everyone', '@‎everyone')

    if '@here' in text:
        text = text.replace('@here', '@‎here')
    channel = ctx.channel
    await channel.send(text)
    msg = await ctx.send("** **") # Makes sure it returns something 
    await msg.delete()


@bot.command(name="text-generator",
             description="Generates text in the style of OneShot!",
             options=[
                 interactions.Option(
                     name="text",
                     description="The text to add.",
                     type=interactions.OptionType.STRING,
                     required=True,
                     max_length = 184
                 )
             ])
async def text_gen(ctx: interactions.CommandContext, text: str):

    async def check(ctx):
        return True

    text__ = icons.Emojis()

    msg = await ctx.send(f"<@{ctx.author.id}>, select a character!", components=text__, ephemeral=True)
    
    char_ctx : interactions.ComponentContext = await wait_for_component(bot, components=text__, check=check)

    text_ = None

    val_char : int = int(char_ctx.data.values[0])
    print(val_char)

    if (val_char == 0):
        text_ = await icons.GenerateModalNiko()
        
    elif (val_char == 1):
        print('lol')
        text_ = await icons.GenerateModalTWM()
        
    elif (val_char == 2):
        text_ = await icons.GenerateModalNiko()

    print(text_)

    await char_ctx.send(f"<@{ctx.author.id}>, select a text face!", components=text_[0], ephemeral=True)
    
    text_ctx : interactions.ComponentContext = await wait_for_component(bot, components=text_[0], check=check)
    
    val = int(text_ctx.data.values[0])

    selection = text_[1][val] # this looks like ass but whatever

    emoji = selection.emoji.url

    print(emoji)
    
    async with aiohttp.ClientSession() as session:
        url = emoji
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open('Images/niko.png', mode='wb')
                await f.write(await resp.read())
                await f.close()

    msg = await text_ctx.send("``Generating Image...``")
    await dialogue_generator.test(text)
    await msg.delete()
    file = interactions.File(filename="Images/pil_text.png")
    await command_send(text_ctx, content=f"Generated by: {ctx.author.name}", files=file)



@bot.command(
    name="music",
    options=[
        interactions.Option(
            name="play",
            description="Add Music to the music queue to be played.",
            type=interactions.OptionType.SUB_COMMAND,
            options=[                
                interactions.Option(
                    name="search",
                    description=
                    "Search for the track you are looking for.",
                    required=True,
                    type=interactions.OptionType.STRING
                )
            ]
        ),

        interactions.Option(
            name = "get_player",
            description = "See what is playing now.",
            type = interactions.OptionType.SUB_COMMAND
        )
    ])
        
async def music(ctx: interactions.CommandContext, sub_command: str, search: str = "", fromindex: int = 0):
    if (ctx.author.voice == None):
        await ctx.send("Sorry! You need to be in a voice channel to use this command.", ephemeral = True)
        return

    if (ctx.author.voice.guild_id != ctx.guild_id):
        await ctx.send("Sorry! You need to be in a voice channel to use this command.", ephemeral = True)
        return
    
    await ctx.defer()
    if (sub_command == "play"):
        player = await bot.connect(ctx.guild_id, ctx.author.voice.channel_id, self_deaf = True)

        player.store(f'channel {ctx.guild_id}', ctx)

        if (search.startswith("https://open.spotify.com/")):
            search = await custom_source.SearchSpotify(search)

        if ('playlist' in search or 'list=PL' in search):
            playlist = await custom_source.GetPlaylist(search)

            msg = await ctx.send(f'Adding **{len(playlist)}** songs to the queue. This might take a while.')

            print(playlist)

            successful = 0
            
            for video in playlist:
                #try:
                results = await player.node.get_tracks(video)
                track = lavalink.AudioTrack(results["tracks"][0], int(ctx.author.id))
                player.add(requester=int(ctx.author.id), track=track)
                successful += 1
                if (successful % 10 == 0):
                    await msg.edit(f'Adding **{len(playlist)}** songs to the queue. This might take a while. ({successful}/{len(playlist)})')
               #@ except:
                    #pass
            
            await msg.edit(f'Added **{successful}** songs to the queue successfully!')
            
            if not player.is_playing:
                await player.play()

            return
        else:
            results = await player.node.get_tracks(f"ytsearch:{search}")
            track = lavalink.AudioTrack(results["tracks"][0], int(ctx.author.id))
            player.add(requester=int(ctx.author.id), track=track)
        

        if not player.is_playing:
            await player.play()
        else:
            cool = interactions.Embed(
                title = f"**Added:** [{track.title}] to queue.",
                thumbnail = interactions.EmbedImageStruct( url = f"https://i3.ytimg.com/vi/{track.identifier}/maxresdefault.jpg", height = 720, width = 1280),
                description = f"Current Position: {len(player.queue)}",
                url = player.queue[len(player.queue) - 1].uri
            )
            await ctx.send(embeds = cool)    
    elif (sub_command == "get_player"):
        player = await bot.connect(ctx.guild_id, ctx.channel_id)

        await ShowPlayer(ctx, player, True)

# --------------------------------------------------------------------

async def ShowPlayer(ctx, player, show_timeline : bool):
    message = ""
    
    if (player.is_playing):
        embed = await GenerateEmbed(player.current.identifier, player, show_timeline)
        msg = await ctx.send('`Loading Player`')
        buttons = await GetButtons(msg.id)
        msg = await msg.edit('', embeds=embed, components=buttons)
    else:
        embed = interactions.Embed(
                title = "Not Currently Playing Anything",
                thumbnail = interactions.EmbedImageStruct( url = "https://shortcut-test2.s3.amazonaws.com/uploads/role/attachment/346765/default_Enlarged_sunicon.png"),
                description = "Use /play music to add music."
            )
        
        await ctx.send(embeds=embed)
        return
    

    async def check(ctx):
        return True
        
    while True:
        print('waiting')
        button_ctx = await wait_for_component(bot, components=buttons, check=check)
        
        data = button_ctx.data.custom_id

        print(data)
    
        if (data == f"play {msg.id}"):
            is_paused = player.fetch("is_paused")
            
            if not (is_paused):
                await player.set_pause(True)
                player.store("is_paused", True)
                message = "`Paused the current track playing.`"
            elif (is_paused):
                await player.set_pause(False)
                player.store("is_paused", False)
                message = "`Resumed the current track playing.`"
        elif (data == f"skip {msg.id}"):
            await button_ctx.send("`Skipped this track!`")
            await player.skip()
        elif (data == f"queue {msg.id}"):
            if (len(player.queue) > 0):
                await button_ctx.edit(components=[])
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
                
                queue = await GenerateQueue(button_ctx, 0, player)

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
    
                msg = await button_ctx.send(embeds = queue, components=[row1, row2])

                async def checkers(ctx):
                    return True
    
                while True:
                    shuffle_ctx = await wait_for_component(bot, components = [row1, row2], check=checkers)

                    if (shuffle_ctx.data.custom_id == f'shuffle {str(id)}'):
                        random.shuffle(player.queue)
                    
                        queue = await GenerateQueue(button_ctx, 0, player)
                        await shuffle_ctx.edit('`Shuffled Queue.`', embeds = queue, components=button_)
                    if (shuffle_ctx.data.custom_id == f'remove {str(id)}'):
                        await shuffle_ctx.send(components=select, ephemeral = True)

                        contexto : interactions.ComponentContext = await wait_for_component(bot, components = select, check=checkers)

                        song_ = player.queue.pop(int(contexto.data.values[0]))
                        
                        await contexto.channel.send(f'<@{contexto.author.id}> Removed {song_.title} from the queue.')

                        queue = await GenerateQueue(button_ctx, 0, player)
                        await shuffle_ctx.edit('`Deleted Song.`', embeds = queue, components=button_)
                    if (shuffle_ctx.data.custom_id == f'jump {str(id)}'):
                        await shuffle_ctx.send(components=select, ephemeral = True)

                        contexto : interactions.ComponentContext = await wait_for_component(bot, components = select, check=checkers)

                        song_ = player.queue[int(contexto.data.values[0])]

                        await contexto.channel.send(f'<@{contexto.author.id}> Jumped to {song_.title}.')

                        del player.queue[0 : int(contexto.data.values[0])]
                        
                        await player.play(song_)
            else:
                message = "`Queue is currently empty :(`"
        elif (data == f"stop {msg.id}"):
            await bot.disconnect(ctx.guild_id)
            await button_ctx.send("Stopped playback :(")
        elif (data == f"loop {msg.id}"):
            if not (player.repeat):
                player.set_repeat(True)
                message = "`Looping Queue!`"
            else:
                player.set_repeat(False)
                message = "`Loop Stopped!`"
                
        funny_embed = await GenerateEmbed(player.current.identifier, player, True)
        await button_ctx.edit(message, embeds = funny_embed)
        
async def track_hook(event):
    if isinstance(event, lavalink.events.TrackStartEvent):
        ctx = event.player.fetch(f'channel {event.player.guild_id}')
        await ShowPlayer(ctx, event.player, False)
    elif isinstance(event, lavalink.events.QueueEndEvent):
        ctx = event.player.fetch(f'channel {event.player.guild_id}')
        await ctx.channel.send("`End of queue! Add more music or audio using /music play.`")
    elif isinstance(event, lavalink.events.TrackExceptionEvent):
        ctx = event.player.fetch(f'channel {event.player.guild_id}')
        await ctx.send("An error occurred when attempting to play the track. Try Skipping the track and replaying it later.")
        await ctx.send(f"`{event.exception}`")
    elif isinstance(event, lavalink.events.TrackStuckEvent):
        ctx = event.player.fetch(f'channel {event.player.guild_id}')
        await ctx.send("Whoops track is stuck that kind of sucks")

async def GenerateQueue(button_ctx, page_number, player):
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
                description = f"█░░░░░░░░░░░░░░░░░░░░\n\n *00:00 / {new_length}*",
                footer = interactions.EmbedFooter( text = 'Do /music get_player if the buttons don\'t work or if you\'ve lost the player.'),
                url = player.current.uri
            )

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
            emoji = loop_song_emoji
        ),

        # Play Button
        interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            custom_id = f"play {guild_id}",
            emoji = play_emoji
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

@bot.command(
    name = "purge",
    description = "Delete multiple messages at once. User must have the 'Administrator' Permission.",
    default_member_permissions=interactions.Permissions.ADMINISTRATOR,
    options = [
        interactions.Option(
            name = "amount",
            required = True,
            description = "The amount of messages to delete up to 100.",
            type = interactions.OptionType.INTEGER,
            max_value = 100
        )
    ]
)
async def testing_lol(ctx : interactions.CommandContext, amount : int):
    await ctx.channel.purge(amount)
    await ctx.send(f"Deleted {amount} messages.", ephemeral=True)

@bot.command(
    name = "actions",
    description = "Do an action towards someone.",
    options = [
        interactions.Option(
            name = "choices",
            description = "The action you wish to do",
            type = interactions.OptionType.STRING,
            required = True,
            choices = [
                interactions.Choice(
                    name = "Hug",
                    value = 'hugg'
                ),

                interactions.Choice(
                    name = "Kiss",
                    value = 'kiss'
                ),

                interactions.Choice(
                    name = "Cuddle",
                    value = 'cuddl'
                ),

                interactions.Choice(
                    name = "Pet",
                    value = 'pett'
                ),

                interactions.Choice(
                    name = "Punch",
                    value = 'punch'
                ),

                interactions.Choice(
                    name = "Slap",
                    value = 'slapp'
                ),

                interactions.Choice(
                    name = "Kill",
                    value = "murder"
                ),
            ]
        ),

        interactions.Option(
            name = "user",
            required = True,
            description = 'The person to do the action towards.',
            type=interactions.OptionType.USER
        )
    ]
)
async def action(ctx : interactions.CommandContext, user : str, choices : str):

    verb = f'{choices}ed'

    title_ = await GetTitles(choices)
    
    if (user.id == ctx.author.user.id):
        if (choices == 'murder' or choices == 'slapp' or choices == 'punch'):
            await ctx.send('Hey! Don\'t do that. That ain\'t cool. Love yourself. ♥', ephemeral = True)
            return
        else:
            embed = interactions.Embed(
                title = f'{title_}!',
                description = f'<@{ctx.author.user.id}> {verb} themself.'
            )   
    else:
        embed = interactions.Embed(
            title = f'{title_}!',
            description = f'<@{ctx.author.user.id}> {verb} <@{user.id}>.'
        )

    button = interactions.Button(
        style = interactions.ButtonStyle.PRIMARY,
        label = await GetTitles(choices) + ' back',
        custom_id = f'sussy {user.id}'
    )

    if (user.id == ctx.author.user.id):
        msg = await ctx.send(embeds = embed)
    else:
        msg = await ctx.send(embeds = embed, components = button)

    async def check(ctx):
        if (ctx.author.id == user.id):
            return True
        else:
            await ctx.send(f'Sorry! Only the user <@{user.id}> can respond to this action!', ephemeral = True)
            return False

    
    if (user.id == bot.me.id):
        embed = interactions.Embed(
            title = f'A {title_} back!',
            description = f'<@{user.id}> {verb} <@{ctx.author.user.id}> back.'
        )
    
        await msg.edit(components = [])
    
        await ctx.send(embeds=embed)
    else:
        button_ctx = await wait_for_component(bot, components=button, check=check)

        embed = interactions.Embed(
            title = f'A {title_} back!',
            description = f'<@{user.id}> {verb} <@{ctx.author.user.id}> back.'
        )
    
        await msg.edit(components = [])
    
        await button_ctx.send(embeds=embed)

async def GetTitles(choice):
    if (choice == 'hugg'):
        return 'Hug'
    if (choice == 'kiss'):
        return 'Kiss'
    if (choice == 'cuddl'):
        return 'Cuddle'
    if (choice == 'pett'):
        return 'Pet'
    if (choice == 'slapp'):
        return 'Slap'
    if (choice == 'punch'):
        return 'Punch'
    if (choice == 'murder'):
        return 'Kill'
        
@bot.command(
    name = 'ask',
    description = 'Ask a question, with the bot responding using OpenAI\'s GPT-3.',
)
async def gen_text(ctx : interactions.CommandContext):
    
    modal = Modal('')
    
    await ctx.popup(modal)

@bot.modal('funny modal')
async def on_modal(ctx, prompt : str):
    msg = await ctx.send('`Generating text...`')
    
    result = await generate_text.GenerateText(prompt)

    embed = interactions.Embed(
        title = 'Result',
        description = prompt + result
    )

    await msg.edit('', embeds=embed)

def Modal(starting_prompt : str):
    return interactions.Modal(
            title = 'Enter Prompt',
            description = 'Enter your prompt and the bot will respond. Asking the bot questions about itself might lead to spoilers for the game OneShot.',
            components = [
                interactions.TextInput(
                    style=interactions.TextStyleType.PARAGRAPH,
                    label="Enter your prompt.",
                    custom_id="text_input_response",
                    type = interactions.ComponentType.INPUT_TEXT,
                    placeholder = 'How are you feeling?, What are you up to?'
                )
            ],
            custom_id='funny modal'
        )

@bot.command(
    name = 'get_pfp',
    description = 'Get a Profile Picture of a user in the server.',
    options = [
        interactions.Option(
            name = 'user',
            description = 'The user to get the profile picture from.',
            type = interactions.OptionType.USER,
            required = True
        )
    ]
)
async def wow_beautiful(ctx : interactions.CommandContext, user : interactions.Member):
    embed = interactions.Embed(
        title = f'{user.name}\'s Profile Picture.',
        image = interactions.EmbedImageStruct(url = user.user.avatar_url, width = 300, height = 300)
    )

    await ctx.send(embeds = embed)

@bot.command(
    name = 'send_letter',
    description = 'Send a letter to someone.',
    options = [
        interactions.Option(
            name = 'user',
            description = 'The user to send the letter to.',
            type = interactions.OptionType.USER,
            required = True
        ),

        interactions.Option(
            name = 'message',
            description = 'The message to send.',
            type = interactions.OptionType.STRING,
            required = True
        ),
    ]
)
async def letter(ctx : interactions.CommandContext, user : interactions.Member, message : str):
    
    lllist = db['loveletters'].split('\n')

    embed = interactions.Embed(
        title = 'You got a letter!',
        description = f'{message}\n\nFrom: **{ctx.author.user.username}**\nIn: **{ctx.guild.name}**',
        footer = interactions.EmbedFooter(text= f'If you wish to send a letter, do /send_letter!'),
        thumbnail = interactions.EmbedImageStruct(url = 'https://www.freepnglogos.com/uploads/letter-png/letter-png-transparent-letter-images-pluspng-17.png')
    )

    if (user.id in lllist and ctx.author.id in lllist):
        await user.send(embeds=embed)
        await ctx.send('Letter sent successfully!', ephemeral=True)
    elif (not user.id in lllist):
        await ctx.send('This user has not opted in for recieving letters. Ask the other person to use /recieve_letters to recieve letters.', ephemeral=True)
    else:
        await ctx.send('In order to send letters, you need to opt in. Use /recieve_letters to recieve and send letters.', ephemeral=True)

@bot.command(
    name = 'recieve_letters',
    description = 'Allows you to recieve letters from anyone.',
)
async def allow(ctx : interactions.CommandContext):
    button = interactions.Button(
        style = interactions.ButtonStyle.PRIMARY,
        label = 'Yes',
        custom_id = str(ctx.author.id)
    )

    lllist = db['loveletters'].split('\n')
    
    if (ctx.author.id in lllist):
        lllist.remove(str(ctx.author.id))

        result = '\n'.join(lllist)

        db['loveletters']  = result

        await ctx.send('You have opted out from recieving letters. If you wish to recieve letters again, run this command again', ephemeral=True)
    else:
        await ctx.send('Are you sure you want to recieve letters?', components=button, ephemeral=True)

        button_ctx = await wait_for_component(bot, components = button)
    
        db['loveletters'] = db['loveletters'] + f'\n{str(ctx.author.id)}'
        await button_ctx.send('You will now recieve letters. To opt out of this, run this command again.', ephemeral=True)

bot.start()