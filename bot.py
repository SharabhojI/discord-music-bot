## Imports ##
import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp

load_dotenv() # load the .env file with the bot token

## Discord intents ##
intents = discord.Intents.all()
client = commands.Bot(command_prefix='-', intents=intents)

## Queue and Settings ##
music_queue = asyncio.Queue()
inactivity_time = 600 # Auto-disconnect timer (in s)
FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
}
last_activity = {} # track last time bot had activity

## Bot Event Handlers ##
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} Command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

## Bot Commands ##
@client.tree.command(
    name='play',
    description='Play the input url or queue it if something is already playing'
)
async def play(ctx: discord.Interaction, query: str):
    try:
        await ctx.response.defer() # defer response to allow for processing

        # join voice channel if not already in it
        if not ctx.guild.voice_client:
            if ctx.user.voice and ctx.user.voice.channel:
                await ctx.user.voice.channel.connect()
            else:
                await ctx.followup.send("You must be in a voice channel to use this command!")
                return

        voice_client = ctx.guild.voice_client

        # check if input query is a URL or a search query
        ydl_options = {
            'format': 'bestaudio',
            'noplaylist': True,
            'quiet': True
        }
        if not (query.startswith("http://") or query.startswith("https://")):
            query = f"ytsearch:{query}" # query is a search query

        # extract audio stream url
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            audio_url =  info['url']
            title = info.get('title', 'Title is Unknown')

        # queue song if one is playing, otherwise play it
        if voice_client.is_playing():
            await music_queue.put((audio_url, title))
            await ctx.followup.send(f"Queued: {title}")
        else:
            voice_client.play(
                discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS),
                after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop)
            )
            await ctx.followup.send(f"Now playing: {title}")

    except Exception as e:
        await ctx.followup.send(f"Error plying song: {e}", ephemeral=True)

@client.tree.command(
    name='skip',
    description='Skip the currently playing song'
)
async def skip(ctx: discord.Interaction):
    try:
        voice_client = ctx.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            await ctx.response.send_message("There is nothing playing right now...", ephemeral=True)
            return

        voice_client.stop()
        asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop)
        await ctx.response.send_message("Skipped the curent song.")
    except Exception as e:
        await ctx.response.send_message("Error skipping song: {e}", ephemeral=True)

@client.tree.command(
    name='remove',
    description='Remove the specified index from the queue'
)
async def remove(ctx: discord.Interaction, index: int):
    temp_queue = [] # temp queue to dequeue into

    # dequeue music queue
    while not music_queue.empty():
        temp_queue.append(await music_queue.get())

    # remove the specified index
    if index <= len(temp_queue):
        removed = temp_items.pop(index-1)
        await ctx.response.send_message(f"Removed queue item {index}: {removed}")
    else:
        await ctx.response.send_message("Selected index out of range for queue")

    # requeue the items
    for item in temp_queue:
        await music_queue.put(item)

@client.tree.command(
    name='clear',
    description='Clear the entire music bot queue'
)
async def clear(ctx: discord.Interaction):
    try:
        while not music_queue.empty():
            await music_queue.get()
        await ctx.response.send_message("The queue has been cleared")
    except Exception as e:
        await ctx.response.send_message(f"Error clearing the queue: {e}", ephemeral=True)

@client.tree.command(
    name='leave',
    description='Dismiss the music bot'
)
async def leave(ctx: discord.Interaction):
    try:
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            await ctx.response.send_message("The bot has left the voice channel")
        else:
            await ctx.response.send_message("Bot is not in a voice channel", ephemeral=True)
    except Exception as e:
        await ctx.response.send_message(f"Error leaving: {e}", ephemeral=True)

## Internal Functions ##
async def play_next(ctx: discord.Interaction):
    voice_client = ctx.guild.voice_client

    # Check if the queue is empty
    if not music_queue.empty():
        next_url, next_title = await music_queue.get()
        voice_client.play(
            discord.FFmpegPCMAudio(next_url, **FFMPEG_OPTIONS),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop)
        )
        await ctx.channel.send(f"Now playing: {next_title}")
    else:
        # Wait for inactivity_time before disconnecting
        await asyncio.sleep(inactivity_time)
        if music_queue.empty() and voice_client:
            await voice_client.disconnect()
            await ctx.channel.send("No activity for a while, so I'm leaving the voice channel.")

## Get bot token and run ##
token = os.getenv('BOT_TOKEN')
client.run(token)
