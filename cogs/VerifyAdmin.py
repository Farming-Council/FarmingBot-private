import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal
import os
import datetime
from discord.app_commands import AppCommandError
from utils.baseclass import FarmingCouncil

class VerifyAdmin(commands.Cog):
    def __init__(self, bot: FarmingCouncil) -> None:
        self.bot = bot
    setting = app_commands.Group(name="settings", description="Bot settings")

    @setting.command(name = "setup")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup(self,interaction: discord.Interaction):
        """ Sets up the server in the database"""
        await interaction.response.defer()
        server = await self.bot.newserver(interaction.guild.id)
        if server == 0:
            embed=discord.Embed(title="Server added!", description="Server added in our database!", color=discord.Color.green())
            embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
            embed.add_field(name = "Finish setting up your server with /settings!",value = "To delete your servers data please contact CosmicCrow")
            embed.timestamp = datetime.datetime.utcnow()
            await interaction.followup.send(embed=embed)
        else:
            embed=discord.Embed(title="Error!", description="It looks like the setup command was already run in the server!", color=discord.Color.red())
            embed.timestamp = datetime.datetime.utcnow()
            await interaction.followup.send(embed=embed)


    
    @setting.command()
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def all(self, interaction: discord.Interaction) -> None:
        """ Gets all settings """
        server = await self.bot.getserver(interaction.guild.id)
        if server:
            embed=discord.Embed(title="Settings", description="Change a setting with /setting name", color=discord.Color.green())
            embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
            embed.add_field(name = "Create a verification panel with /panel",value = f"{':green_circle:' if server[6]==True else ':red_circle:'} Bot status: {'active' if server[6]==True else 'disabled'}\nLoging Channel: {interaction.guild.get_channel(int(server[4])).mention if server[4]!=None else 'Not set up'}\nRole given when verified: {interaction.guild.get_role(int(server[5])).mention if server[5]!=None else 'Not set up'}")
        else:
            embed=discord.Embed(title="Error", description="Server not setup!", color=discord.Color.red())
            embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        await interaction.response.send_message(embed=embed)
    

    @setting.command(name="channel") # 
    @app_commands.guild_only()
    @app_commands.describe(channel="Channel that all logs go to. ")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def channel(self, interaction: discord.Interaction,channel:discord.TextChannel=None) -> None:
        """ Changes the logging channel """
        tr = True
        if channel:
            try:
                await interaction.guild.get_channel(channel.id).send("logging channel test...", delete_after=1)
            except:
                embed=discord.Embed(title="Error", description="Bot dose not have perms to see that channel!", color=discord.Color.red())
                tr = False
            if tr:
                change = await self.bot.changesettings(interaction.guild.id,"channel",channel.id)
        else:
            change = await self.bot.changesettings(interaction.guild.id,"channel",None)
        if tr:
            if change ==1:
                if channel:
                    embed=discord.Embed(title="Settings", description=f"Changed logging channel to {channel.mention}", color=discord.Color.green())
                    embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
                else:
                    embed=discord.Embed(title="Settings", description=f"Removed logging channel", color=discord.Color.green())
                    embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)    
            else:
                embed=discord.Embed(title="Error", description="Server not setup!", color=discord.Color.red())
                embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
        
        embed.timestamp = datetime.datetime.utcnow()
        await interaction.response.send_message(embed=embed)


    @setting.command(name="role") 
    @app_commands.guild_only()
    @app_commands.describe(role="Role that member gets when they verify")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def role(self, interaction: discord.Interaction,role:discord.Role=None) -> None:
        """ Changes the verifacation role """
        tr = True
        if role:
            try:
                await interaction.user.add_roles(interaction.guild.get_role(role.id))
                await asyncio.sleep(1)
                await interaction.user.remove_roles(interaction.guild.get_role(role.id))
            except:
                embed=discord.Embed(title="Error", description=f"Bot dose not have perms to add/remove `{role.name}`!", color=discord.Color.red())
                tr = False
        if tr:
            if role:
                change = await self.bot.changesettings(interaction.guild.id,"role",role.id)
            else:
                change = await self.bot.changesettings(interaction.guild.id,"role",None)
            if change ==1:
                if role:
                    embed=discord.Embed(title="Settings", description=f"Changed verifacation role to {role.mention}", color=discord.Color.green())
                    embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
                else:
                    embed=discord.Embed(title="Settings", description=f"Removed verifacation role", color=discord.Color.green())
                    embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
            else:
                embed=discord.Embed(title="Error", description="Server not setup!", color=discord.Color.red())
                embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        await interaction.response.send_message(embed=embed)

    @setting.command(name="activate") 
    @app_commands.guild_only()
    @app_commands.describe(bot_on="Bot active or disabled ")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def activate(self, interaction: discord.Interaction,bot_on:bool) -> None:
        """ Turns on or off the bot """
        change = await self.bot.changesettings(interaction.guild.id,"disabled",bot_on)
        if change ==1:
            embed=discord.Embed(title="Settings", description=f"Changed disabled to {bot_on}", color=discord.Color.green())
            embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
        else:
            embed=discord.Embed(title="Error", description="Server not setup!", color=discord.Color.red())
            embed.set_footer(text = f"{interaction.user.name}",icon_url=interaction.user.avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        await interaction.response.send_message(embed=embed)




async def setup(bot: commands.Bot):
    await bot.add_cog(VerifyAdmin(bot))
