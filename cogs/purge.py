# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from utils import FarmingCouncil


class purge(commands.Cog):
    def __init__(self, bot: FarmingCouncil):
        self.bot: FarmingCouncil = bot


    @app_commands.command(description="Purge Messages")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    @app_commands.describe(limit = "Amount of messages you'd like to purge")
    async def purge(self, interaction: discord.Interaction,limit: int):
        await interaction.defer()
        await interaction.channel.purge(limit=limit)
        await interaction.response.send_message(f'Cleared {limit} messages by by {self.interaction.author.mention}',ephemeral=True)

        
        
async def setup(bot: commands.Bot):
    await bot.add_cog(purge(bot))
