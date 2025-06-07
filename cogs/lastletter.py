import discord
from discord.ext import commands
from db import SessionLocal, Words
import asyncio
import aiohttp

class LastLetterCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def word_exists(self, word: str):
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200

    async def get_all_words(self, guild_id=None):
        async with SessionLocal() as session:
            query = Words.__table__.select()
            if guild_id is not None:
                query = query.where(Words.guild_id == guild_id)
            result = await session.execute(query)
            return [row.word for row in result.fetchall()]

    async def get_word(self, word, guild_id=None):
        async with SessionLocal() as session:
            query = Words.__table__.select().where(Words.word == word)
            if guild_id is not None:
                query = query.where(Words.guild_id == guild_id)
            result = await session.execute(query)
            return result.fetchone()

    async def get_last_word(self, guild_id=None):
        async with SessionLocal() as session:
            query = Words.__table__.select()
            if guild_id is not None:
                query = query.where(Words.guild_id == guild_id)
            query = query.order_by(Words.id.desc()).limit(1)
            result = await session.execute(query)
            row = result.fetchone()
            return row.word if row else None

    async def add_word(self, word, author_id=None, guild_id=None):
        async with SessionLocal() as session:
            new_word = Words(word=word, author_id=author_id, guild_id=guild_id)
            session.add(new_word)
            await session.commit()

    async def get_channel(self, guild_id):
        from db import SessionLocal, GuildConfig
        async with SessionLocal() as session:
            result = await session.execute(
                GuildConfig.__table__.select().where(GuildConfig.guild_id == guild_id)
            )
            row = result.fetchone()
            return row.channel_id if row else None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        if message.content.startswith("ll") or message.content.startswith("<@"):
            return
        
        guild_id = message.guild.id if message.guild else None
        channel_id = await self.get_channel(guild_id)

        if channel_id is not None and message.channel.id != channel_id:
            return
        
        last_word = await self.get_last_word(guild_id=guild_id)
        all_words = await self.get_all_words(guild_id=guild_id)
        
        content = str(message.content)

        if all_words:
            async with SessionLocal() as session:
                query = Words.__table__.select().where(Words.guild_id == guild_id).order_by(Words.id.desc()).limit(1)
                result = await session.execute(query)
                last_row = result.fetchone()
                if last_row and last_row.author_id == message.author.id:
                    await message.add_reaction("❌")
                    await asyncio.sleep(1.5)
                    await message.delete()
                    return
            if content[0].lower() == last_word[-1].lower() and (await self.get_word(content)) is None and len(content) >= 3 and (await self.word_exists(content)):
                await message.add_reaction("✅")
                await self.add_word(content, author_id=message.author.id, guild_id=guild_id)
            else:
                await message.add_reaction("❌")
                await asyncio.sleep(1.5)
                await message.delete()
        else:
            await self.add_word(content, author_id=message.author.id, guild_id=guild_id)
            await message.add_reaction("✅")
        await self.bot.process_commands(message)

            
    @commands.hybrid_command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context):
        """Show the top users by number of valid words submitted in this guild."""
        await ctx.defer()
        guild_id = ctx.guild.id
        from sqlalchemy import select, func
        async with SessionLocal() as session:
            stmt = select(Words.author_id, func.count(Words.id).label("word_count")).where(Words.guild_id == guild_id).group_by(Words.author_id).order_by(func.count(Words.id).desc()).limit(10)
            result = await session.execute(stmt)
            rows = result.fetchall()
        if not rows:
            await ctx.send("No words have been submitted yet!")
            return
        leaderboard = []
        for i, row in enumerate(rows, 1):
            user = ctx.guild.get_member(row.author_id)
            name = user.display_name if user else f"User {row.author_id}"
            leaderboard.append(f"{i}. {name}: {row.word_count} words")
        await ctx.send("**Leaderboard:**\n" + "\n".join(leaderboard))

    @commands.hybrid_command(name="resetwords")
    @commands.has_permissions(administrator=True)
    async def reset_words(self, ctx: commands.Context):
        """Reset all words for this guild (admin only)."""
        await ctx.defer()
        guild_id = ctx.guild.id
        async with SessionLocal() as session:
            await session.execute(Words.__table__.delete().where(Words.guild_id == guild_id))
            await session.commit()
        await ctx.send("All words have been reset for this server.")

    @commands.hybrid_command(name="mywords")
    async def my_words(self, ctx: commands.Context):
        """Show all words you've submitted in this guild."""
        await ctx.defer()
        guild_id = ctx.guild.id
        author_id = ctx.author.id
        async with SessionLocal() as session:
            result = await session.execute(
                Words.__table__.select().where(
                    (Words.guild_id == guild_id) & (Words.author_id == author_id)
                ).order_by(Words.id.desc())
            )
            rows = result.fetchall()
        if not rows:
            await ctx.send("You haven't submitted any words yet!")
            return
        words = [row.word for row in rows]
        await ctx.send(f"Your words: {', '.join(words)}")

    @commands.hybrid_command(name="lastword")
    async def last_word_cmd(self, ctx: commands.Context):
        """Show the last valid word in this guild."""
        await ctx.defer()
        guild_id = ctx.guild.id
        last_word = await self.get_last_word(guild_id=guild_id)
        if last_word:
            await ctx.send(f"The last word was: **{last_word}**")
        else:
            await ctx.send("No words have been submitted yet!")
    
    class WordsView(discord.ui.View):
        def __init__(self, words, per_page=15):
            super().__init__(timeout=60)
            self.words = words
            self.per_page = per_page
            self.current_page = 0
            self.total_pages = max((len(self.words) - 1) // self.per_page + 1, 1)

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray, disabled=True)
        async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.current_page = max(0, self.current_page - 1)
            await self.update_buttons(interaction)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.current_page = min(self.total_pages - 1, self.current_page + 1)
            await self.update_buttons(interaction)

        async def update_buttons(self, interaction: discord.Interaction):
            # Update button states
            self.prev_button.disabled = self.current_page == 0
            self.next_button.disabled = self.current_page >= self.total_pages - 1

            # Get current page content
            start_idx = self.current_page * self.per_page
            end_idx = start_idx + self.per_page
            current_words = self.words[start_idx:end_idx]

            # Create embed
            embed = discord.Embed(title="Word List", color=discord.Color.blue())
            embed.description = "\n".join(f"{i+1}. {word}" for i, word in enumerate(current_words, start=start_idx))
            embed.set_footer(text=f"Page {self.current_page + 1} of {self.total_pages}")

            await interaction.response.edit_message(embed=embed, view=self)

    @commands.hybrid_command(name="words")
    async def words_command(self, ctx: commands.Context, direction: str = "newest"):
        """Shows the list of words used in this guild with pagination.
        
        Parameters
        ----------
        direction : str
            The order to show words in. Can be 'newest' or 'oldest' (default: newest)
        """
        await ctx.defer()
        guild_id = ctx.guild.id

        if direction.lower() not in ["newest", "oldest"]:
            await ctx.send("Invalid direction! Use 'newest' or 'oldest'.")
            return

        async with SessionLocal() as session:
            query = Words.__table__.select().where(Words.guild_id == guild_id)
            # Order by ID ascending for oldest->newest, descending for newest->oldest
            if direction.lower() == "oldest":
                query = query.order_by(Words.id.asc())
            else:
                query = query.order_by(Words.id.desc())
            
            result = await session.execute(query)
            words = [row.word for row in result.fetchall()]

        if not words:
            await ctx.send("No words have been used in this guild yet!")
            return

        view = self.WordsView(words)
        
        # Create initial embed with direction info
        embed = discord.Embed(
            title="Word List", 
            description="\n".join(f"{i+1}. {word}" for i, word in enumerate(words[:15])),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Page 1 of {view.total_pages} | Showing {direction} first")

        await ctx.send(embed=embed, view=view)
        

async def setup(bot):
    await bot.add_cog(LastLetterCog(bot))
