# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from utils import FarmingCouncil


class QuickMessages(commands.Cog):
    def __init__(self, bot: FarmingCouncil) -> None:
        self.bot: FarmingCouncil = bot

    @app_commands.command(description="Inform a user that we don't need their item")
    @app_commands.guild_only()
    async def noneed(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Sorry,\nAt the moment we are not in need of your item/s. We will ping the <@1057291314519089223> role "
            "as soon as we are in need of them again. To obtain the role simply head to the <#1057291314519089223> "
            "channel and select the Buying Alert option. If you need to sell it quicker though you can use our "
            "<#1057291314519089223> channel too.\n__Thanks a lot!__"
        )

    @app_commands.command(description="Know why you are blacklisted")
    @app_commands.guild_only()
    async def whyamiblacklisted(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "You are **blacklisted** because you didn't verify yet!\n\nYou can verify by simply heading to the "
            "<#1057291728979230741> channel and typing **/verify [IGN]**.\n**NOTE:** Your Discord account needs to be "
            "connected to your Ingame account!"
        )

    @app_commands.command(description="Inform a user to visit us!")
    @app_commands.guild_only()
    async def visitus(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Please visit **_TheThe** or **FussionVirus** and take a look at all the hoes they got!\nAfter finding "
            "a hoe you like simply send us a screenshot of what you need."
        )

    @app_commands.command(description="Tell a user how to use our shop")
    @app_commands.guild_only()
    async def ourshop(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "You can **Buy/Sell** items by simply heading to the <#1057291921313239072> channel!\nMake sure to read "
            "instructions carefully!"
        )


async def setup(bot: FarmingCouncil) -> None:
    await bot.add_cog(QuickMessages(bot))
