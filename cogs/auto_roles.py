# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
import sys, os
import time
import aiohttp
from discord.utils import get

if TYPE_CHECKING:
    from utils import FarmingCouncil


class autoroles(commands.Cog):
    def __init__(self, bot: FarmingCouncil):
        self.bot: FarmingCouncil = bot
        self.session: aiohttp.ClientSession | None = None

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

    @app_commands.guild_only()
    @app_commands.describe(ign = "Hypixel username", profile = "Skyblock profile name")
    @app_commands.command(description="Update to see if you are eligible for Certified Farmer")
    async def updates(self, interaction: discord.Interaction, ign: str=None, profile: str=""):
        try:
            if ign is None:
                ign = await self.bot.get_db_info(interaction.user.id)[1]
            if ign is None:
                await interaction.response.send_message("Please provide a valid Minecraft username or link your account with /link")
                return
            if profile == "":
                req = await self.bot.get_db_info(interaction.user.id)
                if req:
                    profile = req[2]
                else:
                    uuid = await self.bot.get_uuid(ign)
                    profile = await self.bot.get_most_recent_profile(uuid)
            weight = await calculate_farming_weight(self.bot,uuid)
            if weight == 0:
                embed = discord.Embed(title="Error",description=weight)            
                return
            if weight >= 1500:
                embed = discord.Embed(title="You are eligible for **Certified Farmer**!", description = f"""Congratulations {interaction.user}\n\nThe role "Certified Farmer" should be added to you.""")
                guild = interaction.guild
                role = interaction.guild.get_role(1023315201875005520)
                await interaction.user.add_roles(role)
            else:
                embed = discord.Embed(title="You do not meet the requirements for certified farmer", description = f"""Sorry {interaction.user}\n\nYou need 1500+ farming weight to get the certified farmer role, and you currently have {round(weight, 2)}""", color=0x2F3136)
                embed.set_image(url='attachment://image.png')
                embed.set_footer(text="Made by FarmingCouncil",
                            icon_url="https://i.imgur.com/4YXjLqq.png")
            await interaction.edit_original_response(embed=embed)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
    
    @app_commands.command(description="Checks everyone for certified farmer")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def forceupdate(self, interaction: discord.Interaction):
        members = interaction.guild.members
        channel =  self.bot.get_channel(1095291940007845950)
        await interaction.response.send_message(f"Running through {len(members)} Members")
        for user in members:
            try:
                idroles = [i.id for i in user.roles]
                if 1023315201875005520 not in idroles:
                    await channel.send(f"{user} Not Linked")
                    continue
                ign = user.nick
                if ign == None:
                    ign = user.name
                if ign != None:
                    uuid = await self.bot.get_uuid(ign)
                    weight = await calculate_farming_weight(self.bot, uuid)
                    await channel.send(f"```Discord Name: {user}\nDiscord ID: {user.id}\nMinecraft IGN: {ign}\nWeight: {round(weight, 2)}```")
                    role = get (interaction.guild.roles, name = "Certified Farmer")
                    if weight >= 1500:
                        await user.add_roles(role)
                    else:
                        await user.remove_roles(role)
            except:
                await channel.send("user isnt a IGN")
                pass
                
    

        
def try_it(member,collat):
    try:
        return int(member["collection"][collat])
    except:
        return 1
        
async def calculate_farming_weight(self, uuid):
    # Get profile and player data
    async with self.session.get(f"https://elitebot.dev/api/weight/{uuid}") as req:
        try:
            response = await req.json()
        except Exception as e:
            return [0,"Hypixel is down"]
    return response['highest']['farming']['weight']

async def setup(bot: commands.Bot):
    await bot.add_cog(autoroles(bot))
