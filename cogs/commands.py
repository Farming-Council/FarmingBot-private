# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import aiomysql
import json
import sys, os
import time
import datetime
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from utils import FarmingCouncil

class commands(commands.Cog):
    def __init__(self, bot: FarmingCouncil):
        self.bot: FarmingCouncil = bot
        self.session: aiohttp.ClientSession | None = None

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

    @app_commands.command(description="Show Commands")
    @commands.has_permissions(administrator=True)
    async def commands(self, interaction: discord.Interaction):
        if interaction.author.id not in [242063157122564106, 783275214267351062, 360993066758176768,650431108370137088]:
            return
        commands = await self.bot.get_commands()
        send = {}
        for i in commands:
            try:
                send[i[0]] = send[i[0]]+1
            except:
                send[i[0]] = 1
        sed = ''
        for i in send:
            sed += f"**{i}** - {send[i]}\n"
        embed = discord.Embed(title="Interactions Counter", description = sed, color=0x2F3136)
        await interaction.response.send_message(embed=embed)

async def setup(bot: FarmingCouncil) -> None:
    await bot.add_cog(commands(bot))
