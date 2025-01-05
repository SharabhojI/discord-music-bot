# Discord Music Bot

This is a Discord music bot that allows users to play music from YouTube links or search queries in voice channels. The bot features a queue system and will automatically disconnect after a period of inactivity to conserve resources.

## Features

- **YouTube Playback**: Play music from YouTube URLs or search queries
- **Queue System**: Queue up songs to play next while another is playing
- **Queue Management**: Remove specific songs from the queue or clear it entirely
- **Skip Function**: Skip the currently playing song
- **Automatic Disconnection**: Automatically disconnects from voice channels after a period of inactivity to conserve resources

## Setup and Installation

### Prerequisites

- Docker installed on your system
- A Discord Bot Token from the Discord Developer Portal

### Configuration

1. Create a `.env` file in the root directory with your Discord bot token:
`BOT_TOKEN=your_discord_bot_token_here`

2. Build the Docker image:
```bash
docker build -t music-bot .
```

3. Run the container:
```bash
docker run -d --env-file .env music-bot
```

## Usage

### Commands
- **/play [query]**: Play a song from a YouTube URL or search query. If a song is already playing, it will be queued.
- **/skip**: Skip the currently playing song and play the next song in the queue.
- **/remove [index]**: Remove a specific song from the queue by its position number.
- **/clear**: Clear the entire music queue.
- **/leave**: Disconnect the bot from the voice channel.

### Playing Music
1. Join a voice channel
2. Use the /play command with either a YouTube URL or a search query
3. The bot will join your channel and begin playing the requested song
4. Additional song requests will be added to the queue
