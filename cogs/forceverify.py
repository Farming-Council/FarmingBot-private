# -*- coding: utf-8 -*-
from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils import user_mention

if TYPE_CHECKING:
    from utils import FarmingCouncil


class ForceVerify(commands.Cog):
    def __init__(self, bot: FarmingCouncil):
        self.bot: FarmingCouncil = bot


    @app_commands.command(description="Unlink your in-game hypixel account")
    @app_commands.guild_only()
    @app_commands.guilds(test_guild)
    async def forceunlink(self, interaction: discord.Interaction,user:discord.Member):
        async with self.bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT * FROM verification WHERE user_id = %s", (user.id))
                result = await cursor.fetchone()
        if result is None:
            return await interaction.response.send_message("User was not linked!", ephemeral=True)
        async with self.bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("DELETE FROM verification WHERE user_id = %s", (user.id))
                await conn.commit()
        try:
            verified_role = discord.utils.get(interaction.guild.roles, name="Verified")
            unverified_role = discord.utils.get(interaction.guild.roles, name="Unverified")
            await user.remove_roles(verified_role)
            await user.add_roles(unverified_role)
        except:
            embed = discord.Embed(title="\U0000274c Failed", description="There was an issue while unverifying, please contact a staff member.", color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        embed = discord.Embed(title="Success", description=f"Successfully unlinked {user.mention} account.", color=0x2F3136)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(description="Force verify a user")
    @app_commands.guild_only()
    @app_commands.guilds(test_guild)
    @app_commands.describe(user = "Discord user",ign="Minecraft username", profile="Skyblock profile, leave blank for most recently played.")
    async def forcelink(self,interaction:discord.Interaction,user:discord.Member,ign:str,profile:str=None):
        assert isinstance(interaction.user, discord.Member)
        ign = ign or interaction.user.display_name
        await interaction.response.defer(ephemeral=True)
        try:
            uuid = await self.bot.get_uuid(ign)
        except (KeyError, InvalidMinecraftUsername):
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="\U0000274c Failed",
                    description="The given username is invalid or contains special characters.",
                    color=discord.Colour.red()
                )
            )
        try:
            player = await self.bot.get_hypixel_player(uuid)
        except PlayerNotFoundError:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="\U0000274c Failed",
                    description=f"Player `{ign}` not found.",
                    color=discord.Colour.red()
                )
            )
        except KeyError:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="\U0000274c Failed",
                    description=f"You do not have a linked Discord account.",
                    color=discord.Color.red()
                )
            )
        assert interaction.guild is not None
        try:
            account = await self.bot.get_hypixel_player(uuid)
            if profile == None:
                profile = await self.bot.get_most_recent_profile(uuid)
            await self.bot.get_skyblock_data(uuid, profile)
        except ProfileNotFoundError:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="\U0000274c Failed",
                    description=f"Profile `{profile}` not found.",
                    color=discord.Colour.red()
                )
            )
        except HypixelIsDown:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="\U0000274c Failed",
                    description="Hypixel is currently down, please try again later.",
                    color=discord.Colour.red()
                )
            )
        
        async with self.bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT * FROM verification WHERE user_id = %s", (user.id))
                result = await cursor.fetchone()
        if result is not None:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="\U0000274c Failed",
                    description=f"User is already linked with IGN {result[1]} ({result[2]})",
                    color=discord.Colour.red()
                )
            )
        discord_name = str(user)
        if player.social_media.discord == discord_name:
            if interaction.guild.id in [1040291074410819594,1020742260683448450]:
                try:
                    verified_role = discord.utils.get(interaction.guild.roles, name="Verified")
                    unverified_role = discord.utils.get(interaction.guild.roles, name="Unverified")
                    await user.add_roles(verified_role)
                    await user.remove_roles(unverified_role)
                except:
                    embed = discord.Embed(title="\U0000274c Failed", description="There was an issue while verifying.", color=discord.Color.red())
                    return await interaction.followup.send(embed=embed)
                try:
                    await user.edit(nick=player.username)
                except:
                    pass
            try:
                async with self.bot.pool.acquire() as conn:
                    conn: aiomysql.Connection
                    async with conn.cursor() as cursor:
                        cursor: aiomysql.Cursor
                        await cursor.execute("INSERT INTO verification (user_id, ign, profile) VALUES (%s, %s, %s)",
                            (user.id, ign, profile))
                    await conn.commit()
            except pymysql.IntegrityError as e:
                if e.args[0] == 1062:
                    await interaction.followup.send("Please wait before doing this.", ephemeral=True)
                    return
            embed=discord.Embed(
                title="Success",
                description=f"Verified {user.mention} as {player.username} ({profile})!",
                colour=0x2F3136
            )
            embed.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
            return await interaction.followup.send(embed=embed)
        await interaction.followup.send(
            embed=discord.Embed(
                title="\U0000274c Failed",
                description="This Discord account is not linked to the Hypixel account.",
                colour=discord.Colour.red()
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(ForceVerify(bot))
