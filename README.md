# Last Letter Discord Bot

A fun word chain game bot for Discord where users have to respond with words that start with the last letter of the previous word.

## Features

- Play the classic Last Letter word game in designated Discord channels
- Real-time word validation using a dictionary API
- Prevents same user from playing twice in a row
- Minimum word length requirement (3 letters)
- Prevents duplicate words
- Server-specific settings and word history

### Commands

- `/setup <channel>` - Set up the bot in a specific channel
- `/words [direction]` - View all words used (with pagination)
  - `direction`: "newest" or "oldest" to control display order
- `/lastword` - See the last valid word played
- `/leaderboard` - View top 10 players by word count
- `/mywords` - See all words you've submitted
- `/resetwords` - Reset all words (admin only)
- `/ping` - Check if the bot is online

## Setup

1. Clone this repository
```bash
git clone https://github.com/sheepie20/LastLetter
cd LastLetter
```
2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Linux/MacOS: source .venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Discord bot token:
```env
DISCORD_TOKEN=your_token_here
```

5. Run the bot:
```bash
python main.py
```

## Game Rules

1. Each word must start with the last letter of the previous word
2. Words must be at least 3 letters long
3. Words must be valid English words
4. No duplicate words allowed
5. Same player cannot play twice in a row
6. Commands must be used in the designated channel

## Database Structure

The bot uses SQLite with SQLAlchemy for data storage:
- `GuildConfig`: Stores channel settings for each server
- `Words`: Tracks all words used, who used them, and in which server

## Requirements

- Python 3.8+
- discord.py
- SQLAlchemy
- aiosqlite
- aiohttp

## License

MIT License

## Contributing

Feel free to open issues or submit pull requests to improve the bot!
