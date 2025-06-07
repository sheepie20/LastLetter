from discord.ext import commands
import discord
from settings import *
from db import SessionLocal, engine, Base, GuildConfig
import asyncio
import sqlalchemy
import signal

bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=INTENTS,
    help_command=HELP_COMMAND
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print("------")
    await bot.change_presence(activity=discord.Game(name="with letters"))
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = f"cogs.{filename[:-3]}"
            if cog_name not in bot.extensions:
                await bot.load_extension(cog_name)
                print(f"Loaded cog: {filename[:-3]}")
            else:
                print(f"Cog already loaded: {filename[:-3]}")
    print("All cogs loaded successfully.")
    await bot.tree.sync()
    print("Bot is ready!")


@bot.hybrid_command(name="setup", description="Sets up the bot in the specified channel.")
async def setup_channel(ctx, channel: discord.TextChannel):
    """Sets up the bot in the specified channel."""
    async with SessionLocal() as session:
        # Upsert guild config
        result = await session.execute(
            sqlalchemy.select(GuildConfig).where(GuildConfig.guild_id == ctx.guild.id)
        )
        config = result.scalar_one_or_none()
        if config:
            config.channel_id = channel.id
        else:
            config = GuildConfig(guild_id=ctx.guild.id, channel_id=channel.id)
            session.add(config)
        await session.commit()
    await ctx.send(f"Setup complete! Bot will now use {channel.mention} in this server.")


@bot.command()
async def activate(ctx, cog: str):
    if ctx.author.id != 1117914448745738444:
        await ctx.send("You do not have permission to use this command.")
        return
    try:
        await bot.load_extension(f"cogs.{cog}")
        await ctx.send(f"Activated cog: {cog}")
    except Exception as e:
        await ctx.send(f"Failed to activate cog: {cog}\n{e}")

@bot.command()
async def deactivate(ctx, cog: str):
    if ctx.author.id != 1117914448745738444:
        await ctx.send("You do not have permission to use this command.")
        return
    try:
        await bot.unload_extension(f"cogs.{cog}")
        await ctx.send(f"Deactivated cog: {cog}")
    except Exception as e:
        await ctx.send(f"Failed to deactivate cog: {cog}\n{e}")

@bot.command()
async def reload(ctx, cog: str):
    if ctx.author.id != 1117914448745738444:
        await ctx.send("You do not have permission to use this command.")
        return
    try:
        await bot.reload_extension(f"cogs.{cog}")
        await ctx.send(f"Reloaded cog: {cog}")
    except Exception as e:
        await ctx.send(f"Failed to reload cog: {cog}\n{e}")

@bot.command()
async def ping(ctx):
    """Checks if the bot is online."""
    await ctx.send(f"Pong! {bot.latency * 1000:.2f}ms")

if __name__ == "__main__":
    import sys
    async def run_bot():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        if TOKEN is None:
            print("Error: DISCORD_TOKEN is not set in the environment variables.")
        else:
            loop = asyncio.get_running_loop()
            stop_event = asyncio.Event()
            def _stop(*_):
                stop_event.set()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, _stop)
            bot_task = asyncio.create_task(bot.start(TOKEN))
            await stop_event.wait()
            await bot.close()
            bot_task.cancel()
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        print("Bot shutting down cleanly.")