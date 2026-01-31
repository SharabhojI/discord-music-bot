## Imports ##
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio
import yt_dlp
from datetime import datetime

load_dotenv() # load the .env file with the bot token

## Discord intents ##
intents = discord.Intents.all()
client = commands.Bot(command_prefix='-', intents=intents)

## Per-Guild State ##
music_queues = {}      # guild_id -> asyncio.Queue
player_tasks = {}      # guild_id -> asyncio.Task
last_activity = {}     # guild_id -> datetime

inactivity_time = 600 # Auto-disconnect timer (in s)

# FFmpeg options for reconnecting to unstable streams
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

## Bot Event Handlers ##
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} Command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

## Internal Helpers ##
def get_guild_queue(guild_id: int) -> asyncio.Queue:
    # create a queue for the guild if it doesn't exist
    if guild_id not in music_queues:
        music_queues[guild_id] = asyncio.Queue()
    return music_queues[guild_id]

async def player_loop(ctx: discord.Interaction):
    guild = ctx.guild
    voice_client = guild.voice_client
    queue = get_guild_queue(guild.id)

    while True:
        try:
            # wait for the next song or timeout for inactivity
            next_url, next_title = await asyncio.wait_for(
                queue.get(),
                timeout=inactivity_time
            )

            last_activity[guild.id] = datetime.utcnow()

            # play the audio
            voice_client.play(
                discord.FFmpegPCMAudio(next_url, **FFMPEG_OPTIONS)
            )

            await ctx.channel.send(f"Now playing: {next_title}")

            # wait until the song finishes
            while voice_client.is_playing():
                await asyncio.sleep(1)

        except asyncio.TimeoutError:
            # disconnect after inactivity
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
                await ctx.channel.send(
                    "No activity for a while, so I'm leaving the voice channel."
                )

            # cleanup per-guild state
            music_queues.pop(guild.id, None)
            player_tasks.pop(guild.id, None)
            last_activity.pop(guild.id, None)
            return

        except Exception as e:
            print(f"Player loop error: {e}")

## Bot Commands ##
@client.tree.command(
    name='play',
    description='Play the input url or queue it if something is already playing'
)
async def play(ctx: discord.Interaction, query: str):
    await ctx.response.defer()

    # join voice channel if not already in it
    if not ctx.guild.voice_client:
        if ctx.user.voice and ctx.user.voice.channel:
            await ctx.user.voice.channel.connect()
        else:
            await ctx.followup.send("You must be in a voice channel to use this command!")
            return

    voice_client = ctx.guild.voice_client
    queue = get_guild_queue(ctx.guild.id)

    # yt-dlp options for safer audio extraction
    ydl_options = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'force_ipv4': True
    }

    # check if input query is a URL or a search query
    if not query.startswith(("http://", "https://")):
        query = f"ytsearch:{query}"

    # extract audio stream url
    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]

        if not info or 'url' not in info:
            await ctx.followup.send("Failed to extract audio stream.")
            return

        audio_url = info['url']
        title = info.get('title', 'Title is Unknown')

    # enqueue the song
    await queue.put((audio_url, title))
    await ctx.followup.send(f"Queued: {title}")

    # start player task if not already running
    if ctx.guild.id not in player_tasks:
        player_tasks[ctx.guild.id] = asyncio.create_task(player_loop(ctx))

@client.tree.command(
    name='skip',
    description='Skip the currently playing song'
)
async def skip(ctx: discord.Interaction):
    voice_client = ctx.guild.voice_client
    if not voice_client or not voice_client.is_playing():
        await ctx.response.send_message("There is nothing playing right now...", ephemeral=True)
        return

    voice_client.stop()
    await ctx.response.send_message("Skipped the current song.")

@client.tree.command(
    name='queue',
    description='List all songs currently in the queue'
)
async def list_queue(ctx: discord.Interaction):
    queue = get_guild_queue(ctx.guild.id)

    if queue.empty():
        await ctx.response.send_message("The queue is empty!", ephemeral=True)
        return

    items = list(queue._queue) # safe for read-only display
    text = "\n".join(f"{i+1}. {title}" for i, (_, title) in enumerate(items))
    await ctx.response.send_message(f"Current queue:\n{text}")

@client.tree.command(
    name='clear',
    description='Clear the entire music bot queue'
)
async def clear(ctx: discord.Interaction):
    queue = get_guild_queue(ctx.guild.id)
    while not queue.empty():
        await queue.get()
    await ctx.response.send_message("The queue has been cleared")

@client.tree.command(
    name='leave',
    description='Dismiss the music bot'
)
async def leave(ctx: discord.Interaction):
    voice_client = ctx.guild.voice_client
    if voice_client:
        await voice_client.disconnect()

    # cleanup per-guild state
    music_queues.pop(ctx.guild.id, None)
    task = player_tasks.pop(ctx.guild.id, None)
    if task:
        task.cancel()

    await ctx.response.send_message("The bot has left the voice channel")

## Get bot token and run ##
token = os.getenv('BOT_TOKEN')
client.run(token)
