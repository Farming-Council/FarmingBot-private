# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from . import CloseTicket
import asyncio
import aiomysql
import io
import chat_exporter
import os
from dotenv import load_dotenv
from cogs.tickets.close import close_ticket
from cogs.tickets.persistent import TicketHandler,ContactStaffTickets
load_dotenv()

if TYPE_CHECKING:
    from utils import FarmingCouncil

__all__ = ("Ticketing",)

class Ticketing(commands.Cog):
    def __init__(self, bot: FarmingCouncil) -> None:
        self.bot: FarmingCouncil = bot
        self.staff_role: discord.Role 

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        guild = self.bot.get_guild(int(os.environ.get("GUILD_ID")))
        assert guild is not None
        self.staff_role: discord.Role = discord.utils.get(guild.roles, name="Staff")  # type: ignore
        assert self.staff_role is not None


    
    @app_commands.command(description="Admin Command")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def forceclose(self, interaction: discord.Interaction, member:discord.Member) -> None:
        assert interaction.guild is not None
        await interaction.response.send_message("Searching for tickets...", ephemeral=True)
        total = 0
        if interaction.guild.id != int(os.environ.get("GUILD_ID")):
            await interaction.followup.send("You can only use this command in the main server", ephemeral=True)
            return
        if interaction.user.guild_permissions.administrator == False:
            await interaction.followup.send("You do not have permission to use this command", ephemeral=True)
            return
        async with self.bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cur:
                await cur.execute(f"SELECT * FROM tickets WHERE user = {member.id} AND ticket_status = 0")
                tickets = await cur.fetchall()
                for ticket in tickets:
                    chan = self.bot.get_channel(ticket[1])
                    if chan:
                        await close_ticket(self.bot, chan, interaction.user)
            await conn.commit()

        try:
            await interaction.followup.send(f"Done! Deleted {total} tickets", ephemeral=True)
        except discord.HTTPException:
            pass

    @app_commands.command(description="Close ALL tickets BE VERY CAREFUL WITH THIS COMMAND")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def closeall(self, interaction: discord.Interaction):
        if interaction.guild.id != int(os.environ.get("GUILD_ID")):
            await interaction.response.send_message("You can only use this command in the main server", ephemeral=True)
            return
        if interaction.user.guild_permissions.administrator == False:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        assert interaction.guild is not None
        await interaction.response.send_message("Closing all tickets...", ephemeral=True)
        total = 0
        async with self.bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM tickets")
                tickets = await cur.fetchall()
                for ticket in tickets:
                    chan = self.bot.get_channel(ticket[1])
                    await cur.execute(
                        f"DELETE FROM tickets WHERE channel_id = {ticket[1]}"
                    )
                    if chan is None:
                        continue
                    else:
                        await chan.delete()
                        total =total+1
                        await asyncio.sleep(1)
            await conn.commit()
        await interaction.followup.send(f"Done! Deleted {total} tickets", ephemeral=True)

    @app_commands.command(description="Close this ticket")
    @app_commands.guild_only()
    async def close(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        if interaction.guild.id != int(os.environ.get("GUILD_ID")):
            await interaction.followup.send("You can only use this command in the main server", ephemeral=True)
            return

        async with self.bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cur:
                await cur.execute(f"SELECT * FROM tickets WHERE channel_id = {interaction.channel.id}")
                tickets = await cur.fetchone()

        if not tickets:
            embed = discord.Embed(title="Error", description="This is not a ticket channel", color=discord.Color.red())
            return await interaction.followup.send(embed=embed,ephemeral=True)
        
        us  = self.bot.get_user(tickets[0])
        if not us:
            await interaction.channel.send("User not found\nDeleting ticket in 10 seconds")
            await asyncio.sleep(10)
            async with self.bot.pool.acquire() as conn:
                conn: aiomysql.Connection
                async with conn.cursor() as cur:
                    await cur.execute(f"DELETE FROM tickets WHERE channel_id = {interaction.channel.id}")
                await conn.commit()

            return await interaction.channel.delete()
        
        embed = discord.Embed(title="Do you want to support us?", description = """
Thanks for reaching us to out, I hope we were able to resolve your issue!
In case you want to support us so that we can continue to work on this community and the <@1070710324447166484> please consider subscribing to our **Patreon**!

__**https://www.patreon.com/FarmingCouncil**__

Have a nice day :wave: """, color=0x2b2d31)
        await interaction.channel.send(embed=embed)
        await interaction.channel.send(f"{us.mention}",delete_after=1)
        name = interaction.channel.name
        await interaction.channel.edit(name=f"{name}-closed")
        await interaction.followup.send("Ticket closing...", ephemeral=True)
        await asyncio.sleep(120)
        try:
            await close_ticket(self.bot, interaction.channel,interaction.user)
        except discord.NotFound:
            pass
    


    async def send_msg(self,message,type):   
        totala = 0
        async with self.bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cur:
                await cur.execute(f"SELECT * FROM tickets WHERE ticket_status = 0 AND {type}")
                tickets = await cur.fetchall()
                for ticket in tickets:
                    chan = self.bot.get_channel(ticket[1])
                    if chan is None:
                        continue
                    else:
                        try:
                            await chan.send(message)
                            user = await self.bot.fetch_user(ticket[0])
                            if user:
                                await chan.send(f"{user.mention}",delete_after=1)
                            totala =totala+1
                            await asyncio.sleep(1)
                        except:
                            pass
        return totala
                
    @app_commands.command(description="Send a message to all tickets")
    @app_commands.choices(channel_type=[
        app_commands.Choice(name="buy", value="buy"),
        app_commands.Choice(name="sell", value="sell"),
        app_commands.Choice(name="support", value="support"),
        app_commands.Choice(name="all", value="all"),
        app_commands.Choice(name="shop", value="shop"),
        ])
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def ticketmessage(self, interaction: discord.Interaction, channel_type: app_commands.Choice[str], message: str) -> None:
        if interaction.guild.id != int(os.environ.get("GUILD_ID")):
            await interaction.response.send_message("You can only use this command in the main server", ephemeral=True)
            return
        if interaction.user.guild_permissions.administrator == False:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        assert interaction.guild is not None
        await interaction.response.defer()
        total = 0
        if channel_type.value == "all":
            total = total + await self.send_msg(message,"ticket_type = 1 OR ticket_type = 2 OR ticket_type = 3")
        if channel_type.value == "shop":
            total = total + await self.send_msg(message,"ticket_type = 2 OR ticket_type = 3")
        if channel_type.value == "support":
            total = total + await self.send_msg(message,"ticket_type = 1 OR ticket_type = 2 OR ticket_type = 3")
        if channel_type.value == "buy":
            total = total + await self.send_msg(message,"ticket_type = 2")
        if channel_type.value == "sell":
            total = total + await self.send_msg(message,"ticket_type = 3")
        await interaction.followup.send(f"Sent message to {total} tickets", ephemeral=True)
    


    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def setup_contact(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != 242063157122564106:
            return
        assert interaction.channel is not None
        assert isinstance(interaction.channel, (discord.TextChannel, discord.Thread))
        maybe_tickets = discord.utils.find(lambda v: isinstance(v, ContactStaffTickets), self.bot.persistent_views)
        if maybe_tickets:
            maybe_tickets.stop()
        await interaction.response.send_message("Creating ticket view...", ephemeral=True)
        e = discord.Embed(title="Contact Staff",
                          description="""
                          If you're in need of assistance or have any questions, our dedicated staff team is here to help you out. Whether it's a technical issue, a server-related question, or any other concern, don't hesitate to reach out to us. You can also contact us to claim won prizes from events or similar.

To ensure a smooth and efficient resolution, we kindly ask you to provide as much detail as possible when describing your issue. This will help our team to better understand your situation and provide you with the most accurate assistance.

Please remember to be respectful and patient while awaiting a response. Our staff members are committed to helping everyone in a timely manner, but response times may vary based on the complexity of the request and the current workload.

Cheers 🍸
""", color=0x2b2d31)
        e.set_image(url="https://i.imgur.com/KMTZJxm.png")
        e.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
        image_embed = discord.Embed(color=0x2b2d31)
        image_embed.set_image(url="https://i.imgur.com/gYpLMvA.png")
        await interaction.channel.send(
            embeds=[image_embed, e],
            view=ContactStaffTickets()
        )

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def setup_tickets(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != 242063157122564106:
            return
        """Sets up a persistent buy or sell message in the channel in which this command is executed."""
        assert interaction.channel is not None
        assert isinstance(interaction.channel, (discord.TextChannel, discord.Thread))
        maybe_tickets = discord.utils.find(lambda v: isinstance(v, TicketHandler), self.bot.persistent_views)
        if maybe_tickets:
            maybe_tickets.stop()
        await interaction.response.send_message("Creating ticket view...", ephemeral=True)
        #  Copied from https://canary.discord.com/channels/1020742260683448450/1025890799906459698/1053695874070495253,
        #  change as needed
        embed = discord.Embed(
            title="The Shop",
            description="""
            Welcome at **The Shop**. Please make sure to read the instructions thoroughly to avoid confusion during the process. It is also necessary to have your **API enabled** during the buying or selling process. All items that you want to sell **have to be** in your inventory/backpack/enderchest, otherwise the bot won't be able to detect them.

            Please fill out the form properly to avoid any waiting times.
In addition to that send us an image of the item you are trying to sell/buy right after submitting the ticket.

Current prices are for non enchanted items _(Last updated: 11th of March.)_:

> **Mathematical BP:** 4.2m
> 
> **Melon and Pumpkin Dicer:** 4.2m
> **Coco Chopper:** 4.2m
> **Fungi Cutter/Cactus Knife:** 4.2m
> 
> **Baskets/Pouches:** 2.8m
> **Greater Hoe of Tilling:** 700k
> **Greatest Hoe of Tilling:** 1.4m
> **Prismapumps:** 250k

**We will process your request as soon as possible. Please be patient and don't ping any of our Staff.**
            """,
            color=0x2b2d31
        )
        embed.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
        embed.set_image(url="https://i.imgur.com/KMTZJxm.png")
        image_embed = discord.Embed(color=0x2b2d31)
        image_embed.set_image(url="https://i.imgur.com/e8ctdI0.png")
        await interaction.channel.send(
            embeds=[image_embed, embed],
            view=TicketHandler()
        )
