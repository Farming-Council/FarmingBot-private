
import discord
from discord.ext import commands
from discord import app_commands
import sqlite3 as sl
from typing import Literal
import os
from dotenv import load_dotenv
import datetime
import asyncio


class errors(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        bot.tree.on_error = self.app_command_errora
        
    async def app_command_errora(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            embed=discord.Embed(title="Error", description="You are missing permission needed to run this command!", color=discord.Color.red())
            embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            try:
                await interaction.response.send_message(embed=embed,ephemeral=True)
            except:
                try: 
                    await interaction.followup.send(embed=embed,ephemeral=True)
                except:
                    pass
        elif isinstance(error, app_commands.BotMissingPermissions):
            embed=discord.Embed(title="Error", description="I dont have permission for this to work!", color=discord.Color.red())
            embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            try:
                await interaction.response.send_message(embed=embed,ephemeral=True)
            except:
                try: 
                    await interaction.followup.send(embed=embed,ephemeral=True)
                except:
                    pass
        else:
            embed=discord.Embed(title="Error", description=f"An error has occured\nThis was recorded and sent to the devs!", color=discord.Color.red())
            embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            channel = self.bot.get_channel(1078460509872984126)
            try:
                await interaction.response.send_message(embed=embed,ephemeral=True)
            except:
                try: 
                    await interaction.followup.send(embed=embed,ephemeral=True)
                except:
                    pass
            try:
                embed = discord.Embed(title="Error", description=f"An error has occured: {error}", color=discord.Color.red())
                embed.add_field(name="Command", value=f"{interaction.data['name']}")
                embed.add_field(name="User", value=f"{interaction.user}")
                embed.add_field(name="Guild", value=f"{interaction.guild}")
                embed.add_field(name="Data", value=f"{interaction.data}")
                embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
                embed.timestamp = datetime.datetime.utcnow()
                channel = self.bot.get_channel(1078460509872984126)
                await channel.send(embed=embed)
            except:
                print(error)

async def setup(bot: commands.Bot):
    await bot.add_cog(errors(bot))
