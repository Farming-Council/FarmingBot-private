# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING,Literal

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from utils import FarmingCouncil


class misc(commands.Cog):
    def __init__(self, bot: FarmingCouncil):
        self.bot: FarmingCouncil = bot
        self.good_user = [242063157122564106, 650431108370137088]

    @app_commands.command(description="Purge Messages")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    @app_commands.describe(limit = "Amount of messages you'd like to purge")
    async def purge(self, interaction: discord.Interaction,limit: int):
        await interaction.channel.purge(limit=limit)
        await interaction.response.send_message('Cleared by {}'.format(self.interaction.author.mention))
    @app_commands.command()
    @app_commands.guild_only()
    async def addtutorial(self, interaction: discord.Interaction, topic: Literal["Carrots", "Potato", "Wheat", "Sugar Cane", "Pumpkin", "Melon", "Teleport Pads"], video: str):
        role =interaction.guild.get_role(1028636883879743558)
        if role:
            if role not in interaction.user.roles and interaction.user.id not in self.good_user:
                await interaction.response.send_message("This command is not for you", ephemeral=True)
                return
        else:
            if interaction.user.id not in self.good_user:
                await interaction.response.send_message("This command is not for you", ephemeral=True)
                return
        await self.bot.add_crop(str(topic), str(video))
        await interaction.response.send_message("Done lol")
    
    @app_commands.command()
    @app_commands.guild_only()
    async def removetutorial(self, interaction: discord.Interaction, topic: Literal["Carrots", "Potato", "Wheat", "Sugar Cane", "Pumpkin", "Melon", "Teleport Pads"]):
        role =interaction.guild.get_role(1028636883879743558)
        if role:
            if role not in interaction.user.roles and interaction.user.id not in self.good_user:
                await interaction.response.send_message("This command is not for you", ephemeral=True)
                return
        else:
            if interaction.user.id not in self.good_user:
                await interaction.response.send_message("This command is not for you", ephemeral=True)
                return
        await self.bot.remove_crop(str(topic))
        await interaction.response.send_message("Done lol")
async def setup(bot: commands.Bot):
    await bot.add_cog(misc(bot))