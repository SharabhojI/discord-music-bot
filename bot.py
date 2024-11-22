## Imports ##
import discord
import asyncio
import yt_dlp

load_dotenv() # load the .env file with the bot token
intents = discord.Intents.default()

music_queue = asyncio.Queue()
inactivity_time = 600 # Auto-disconnect timer (in s)
last_activity = {} # track last time bot had activity

## Bot Commands ##
@client.tree.command(
    name='play'
    description='Play the input url or queue it if something is already playing'
)
async def play(ctx: discord.Interaction):
    await ctx.response.send_message("To be implemented")

@client.tree.command(
    name='skip'
    description='Skip the currently playing song'
)
async def skip(ctx: discord.Interaction):
    await ctx.response.send_message("To be implemented")

@client.tree.command(
    name='remove'
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
    name='clear'
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
            await ctx.guild.voice_clint.disconnect()
            await ctx.response.send_message("The bot has left the voice channel")
        else:
            await ctx.response.send_message("Bot is not in a voice channel", ephemeral=True)
    except Exception as e:
        await ctx.response.send_message(f"Error leaving: {e}", ephemeral=True)

## Get bot token and run ##
token = os.getenv('BOT_TOKEN')
client.run(token)
