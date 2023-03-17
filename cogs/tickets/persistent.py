# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal
{1:"Support", 2:"Buy", 3:"Sell", 4:"Broken"}
import discord
import re
import random
from numerize import numerize
from discord import ui
import datetime 
from . import CloseTicket
import chat_exporter
import io
import aiomysql
import asyncio
import string
import json
import pymysql
import utils
import aiohttp
from errors import PlayerNotFoundError, InvalidMinecraftUsername, ProfileNotFoundError, HypixelIsDown
import os 
from dotenv import load_dotenv
from cogs.tickets.close import close_ticket
if TYPE_CHECKING:
    from utils import FarmingCouncil
load_dotenv()


class ContactStaffTickets(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.gray, emoji="<:Contact_Staff:1071770393628639342>", custom_id="tickets:contactstaff")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ContactStaffForm())
        await interaction.edit_original_response(view=self)

class ContactStaffForm(ui.Modal):
    topic: ClassVar[ui.TextInput[Form]] = ui.TextInput(
        label="How can we help you?",
        style=discord.TextStyle.long,
        max_length=1024
    )

    ign: ClassVar[ui.TextInput[Form]] = ui.TextInput(
        label="What's your Minecraft username?",
    )

    def __init__(self) -> None:
        super().__init__(title=f"Contact Staff")

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        bot: FarmingCouncil = interaction.client  # type: ignore
        guild = interaction.guild
        assert guild is not None
        async with bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT * FROM tickets WHERE user = %s AND ticket_type = 1 AND ticket_status = 0", (interaction.user.id,))
                await conn.commit()
                exist = await cursor.fetchone()
                if exist:
                    channel = bot.get_channel(int(exist[1]))
                    if channel:
                        return await interaction.response.send_message(f"You already have a ticket! {channel.mention}", ephemeral=True)
                    else:
                        pass

        async with bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT COUNT(*) FROM tickets WHERE ticket_type = 1")
                exist = await cursor.fetchone()
        ticket_id = exist[0]+1
        ticket_channel = bot.get_channel(int(os.environ.get("TICKET_CHANNEL")))
        thread = await ticket_channel.create_thread(
        name = f"support-{ticket_id}",
        type=discord.ChannelType.private_thread
        )
        await thread.add_user(interaction.user)
        embed = discord.Embed(title=f"Contact Staff", color=0x2F3136)
        embed.add_field(name=self.topic.label, value=self.topic.value, inline=False)
        embed.add_field(name=self.ign.label, value=self.ign.value, inline=False)
        embed.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
        view = CloseTicket(thread, interaction.user.id)
        staff_role = guild.get_role(int(os.environ.get("STAFF_TICKET_ROLE")))
        try:
            await thread.send(f"{staff_role.mention}", delete_after=1)
        except:
            pass
        await thread.send(embed = embed, view = view)

        try:
            await view.create(bot,ticket_id = ticket_id,type = 1)
        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1062:
                await thread.delete()
                return await interaction.response.send_message(f"Please wait for a few minutes before creating a ticket.", ephemeral=True)
        await interaction.response.send_message(f"You can find your ticket here: {thread.mention}", ephemeral=True)

"""

Negotiation

"""
class FirstOffer(discord.ui.View):
    def __init__(self, hoe, price):
        super().__init__()
        self.hoe = hoe
        self.price = price
        self.message: discord.Message

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirm.disabled = True
        self.deny.disabled = True
        await interaction.response.edit_message(view=self)
        bot: FarmingCouncil = interaction.client
        async with bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT ign FROM verification WHERE user_id = %s", (interaction.user.id,))
                data = await cursor.fetchone()
                ign = data[0]
        e = discord.Embed(description=f"Thank you for utilizing our services. A representative will be in touch with you soon. Please wait patiently.\n*Disclaimer:* The buyer might change the price if he is not willing to pay the calculated amount.\n\n**__{re.sub('§.', '', '' + str(self.hoe.name))}__:**\nCounter: **{self.hoe.mined:,}**\nOffered price: **{numerize.numerize(self.price)}**\nSeller: **{ign}**", color=0x2F3136)
        e.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
        await interaction.channel.send("<@&1072436775668174898>", embed=e)

        new_name = f"{interaction.channel.name}-done"
        await interaction.channel.edit(name=new_name)


 
    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        offer = 0
        if "3" in self.hoe.item_id:
            offer = round(self.price * 1.23)
        if "2" in self.hoe.item_id:
            offer = round(self.price * 1.23)
        if "1" in self.hoe.item_id:
            offer = round(self.price * 1.20)
        self.deny.disabled = True
        self.confirm.disabled = True
        e = discord.Embed(description=f"We regret that our offer did not meet your expectations. Our NEW maximum offer is **{numerize.numerize(offer)}**. Are you willing to accept this amount?", color=0x2F3136)
        e.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
        await interaction.response.edit_message(embed=e, view=SecondOffer(self.hoe, offer))


            
class SecondOffer(discord.ui.View):
    def __init__(self, hoe, price):
        super().__init__()
        self.hoe = hoe
        self.price = price

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirm.disabled = True
        self.deny.disabled = True
        await interaction.response.edit_message(view=self)
        bot: FarmingCouncil = interaction.client
        async with bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT ign FROM verification WHERE user_id = %s", (interaction.user.id,))
                data = await cursor.fetchone()
                ign = data[0]

        e = discord.Embed(description=f"Thank you for utilizing our services. A representative will be in touch with you soon. Please wait patiently.\n*Disclaimer:* The buyer might change the price if he is not willing to pay the calculated amount.\n\n**__{re.sub('§.', '', '' + str(self.hoe.name))}__:**\nCounter: **{self.hoe.mined:,}**\nOffered price: **{numerize.numerize(self.price)}**\nSeller: **{ign}**", color=0x2F3136)
        e.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
        await interaction.channel.send("<@&1072436775668174898>", embed=e)
        new_name = f"{interaction.channel.name}-done"
        await interaction.channel.edit(name=new_name)


    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        e = discord.Embed(description=f"We apologize for failing to meet your expectations. We wish you the best of luck in selling your item in the future. If you reconsider, don't hesitate to open a new ticket. You can now close this ticket.", color=0x2F3136)
        e.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
        self.deny.disabled = True
        self.confirm.disable = True
        await interaction.response.edit_message(embed=e, view=CloseTicket(interaction.channel, interaction.user))
        await asyncio.sleep(60)
        assert interaction.channel is not None
        await close_ticket(interaction.client,interaction.channel, interaction.user)
        
class Dropdown(discord.ui.Select):
    def __init__(self, hoes,bot,channel):
        self.hoes = hoes
        self.bot = bot
        self.channel = channel
        if len(hoes) != 1:
            options = [discord.SelectOption(
                        label=f"{re.sub('§.', '', '' + str(hoe.name))}",
                        value=f"{hoe.item_id}_{random.choice(string.ascii_letters)}{random.choice(string.ascii_letters)}",
                        description=f"{hoe.mined:,} Counter") for hoe in self.hoes]
        else:
            options = [discord.SelectOption(
                        label=f"{re.sub('§.', '', '' + str(hoes[0].name))}",
                        value=f"{hoes[0].item_id}",
                        description=f"{hoes[0].mined:,} Counter")]
        super().__init__(placeholder='Select which hoe you are trying to sell', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_hoe_item = None
        offer = 0
        if len(self.hoes) != 1:
            for hoe in self.hoes:
                #print(hoe.item_id, self.values[0][:-3])
                if str(hoe.item_id) == self.values[0][:-3]:
                    selected_hoe_item = hoe
        else:
            selected_hoe_item = self.hoes[0]
        if "3" in selected_hoe_item.item_id:
            offer = round(selected_hoe_item.value * 0.40, -3)
        if "2" in selected_hoe_item.item_id:
            offer = round(selected_hoe_item.value * 0.50, -3)
        if "1" in selected_hoe_item.item_id:
            offer = round(selected_hoe_item.value * 0.50, -3)
        e = discord.Embed(title="Offer", description=f"We are offering you **{numerize.numerize(offer)}** for that hoe. Please click the button below to confirm or deny.", color=0x2F3136)
        e.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
        view = FirstOffer(selected_hoe_item, offer)
        self.disabled = True
        view2 = discord.ui.View().add_item(self)
        await interaction.response.edit_message(embed=e, view=view)

    async def on_timeout(self):
        await close_ticket(self.bot,self.channel, self.bot)
    
class Form(ui.Modal):
    description: ClassVar[ui.TextInput[Form]] = ui.TextInput(
        label="Describe the item you want to buy!",
        style=discord.TextStyle.long,
        default="Type of item:\nCounter (if hoe):\nRecombabulated: yes/no",
        max_length=1024
    )
    price: ClassVar[ui.TextInput[Form]] = ui.TextInput(
        label="Your offer in coins?",
        placeholder="e.g: 11M coins"
    )
    user_info: ClassVar[ui.TextInput[Form]] = ui.TextInput(
        label="What is your IGN and Discord tag?",
        placeholder="e.g: _TheThe, TheThe#0000"
    )

    def __init__(self) -> None:
        super().__init__(title=f"Buy your item")

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        # Type checking stuff
        await interaction.response.defer()
        bot: FarmingCouncil = interaction.client  # type: ignore
        guild = interaction.guild
        assert guild is not None

        async with bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT COUNT(*) FROM tickets WHERE ticket_type = 2")
                exist = await cursor.fetchone()
        ticket_id = exist[0] + 1
        buy_channel = bot.get_channel(int(os.environ.get("TICKET_CHANNEL")))

        thread = await buy_channel.create_thread(
        name = f"buy-{ticket_id}",
        type=discord.ChannelType.private_thread
        )
        await thread.add_user(interaction.user)

        embed = discord.Embed(title=f"{interaction.user} wants to buy an item", colour=0x2F3136)
        embed.add_field(name=self.description.label, value=self.description.value, inline=False)
        embed.add_field(name=self.price.label, value=self.price.value, inline=False)
        embed.add_field(name=self.user_info.label, value=self.user_info.value, inline=False)
        embed.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
        view = CloseTicket(thread, interaction.user.id)
        await thread.send(
            embed=embed,
            view=view
        )
        await view.create(bot, ticket_id=ticket_id,type=2)
        await interaction.followup.send(f"You can find your ticket here: {thread.mention}", ephemeral=True)


class TicketHandler(ui.View):
    OPTIONS: ClassVar[tuple[discord.SelectOption, ...]] = (
        discord.SelectOption(label="Sell", value="sell", emoji="<:Sell:1071098483068637245>"),
        discord.SelectOption(label="Buy", value="buy", emoji="<:Buy:1071098479516074074>")
    )
    def __init__(self) -> None:
        super().__init__(timeout=None)
    def on_cog_load(self):
        self.load_prices(self.bot)

    async def send_channel_error_response(self, channel: discord.TextChannel, error: str, description: str,id:int) -> None:
        return await channel.send(
            embed=discord.Embed(
                title=error,
                description=description,
                color=discord.Colour.red()
            ), view = CloseTicket(channel, id)
        )
    @ui.select(options=list(OPTIONS), custom_id="farmingbot:ticket", placeholder="Select an action...")
    async def callback(self, interaction: discord.Interaction, select: ui.Select[TicketHandler]) -> None:
        bot: FarmingCouncil = interaction.client # type: ignore
        
        if select.values[0] == "buy":
            async with bot.pool.acquire() as conn:
                conn: aiomysql.Connection
                async with conn.cursor() as cursor:
                    cursor: aiomysql.Cursor
                    await cursor.execute("SELECT * FROM verification WHERE user_id = %s", (interaction.user.id,))
                    ign = await cursor.fetchone()
                    if not ign:
                        await interaction.response.send_message("Your IGN is not stored in our database! Please go to <#1020759880849703013> and un-link using `/unlink` and re-link using `/link`!", ephemeral=True)
                        await interaction.message.edit(view=self)
                        return 
                    await cursor.execute("SELECT * FROM tickets WHERE user = %s AND ticket_type = 2 AND ticket_status = 0", (interaction.user.id,))
                    exist = await cursor.fetchone()
                    if exist:
                        channel = bot.get_channel(exist[1])
                        if channel:
                            try:
                                await interaction.response.send_message(f"You already have a ticket! {channel.mention}", ephemeral=True)
                                await interaction.message.edit(view=self)
                                return
                            except:
                                return
            await interaction.response.send_modal(Form())  # type: ignore
            await interaction.edit_original_response(view=self)
        else:
            await interaction.response.defer(ephemeral=True)
            bot: FarmingCouncil = interaction.client  # type: ignore
            async with bot.pool.acquire() as conn:
                conn: aiomysql.Connection
                async with conn.cursor() as cursor:
                    cursor: aiomysql.Cursor
                    await cursor.execute("SELECT * FROM verification WHERE user_id = %s", (interaction.user.id,))
                    ign = await cursor.fetchone()
                    if not ign:
                        await interaction.edit_original_response(view=self)
                        return await interaction.followup.send("Your IGN is not stored in our database! Please go to <#1020759880849703013> and unlink using `/unlink` and re-link using `/link`!", ephemeral=True)
                    await cursor.execute("SELECT * FROM tickets WHERE user = %s AND ticket_type = 3 AND ticket_status = 0", (interaction.user.id,))
                    exist = await cursor.fetchone()
                    if exist:
                        channel = bot.get_channel(exist[1])
                        if channel:
                            await interaction.edit_original_response(view=self)
                            return await interaction.followup.send(f"You already have a ticket! {channel.mention}", ephemeral=True)
                        else:
                            pass

            guild = interaction.guild
            assert guild is not None
            async with bot.pool.acquire() as conn:
                conn: aiomysql.Connection
                async with conn.cursor() as cursor:
                    cursor: aiomysql.Cursor
                    await cursor.execute("SELECT COUNT(*) FROM tickets WHERE ticket_type = 3")
                    exist = await cursor.fetchone()
            ticket_id = exist[0] + 1
            sell_channel = bot.get_channel(int(os.environ.get("TICKET_CHANNEL")))
            thread = await sell_channel.create_thread(
            name = f"sell-{ticket_id}",
            type=discord.ChannelType.private_thread
            )
            await thread.add_user(interaction.user)

            view = CloseTicket(thread, interaction.user.id)
            
            try:
                await view.create(bot, ticket_id = ticket_id, type = 3)
            except pymysql.err.IntegrityError as e:
                    await thread.delete()
                    await interaction.edit_original_response(view=self)
                    return await interaction.followup.send(f"Please wait for a few minutes before creating a ticket.", ephemeral=True)

            await interaction.followup.send(f"You can find your ticket here: {thread.mention}", ephemeral=True)
            await interaction.edit_original_response(view=self)
            import cogs.farming_items as Farming
            async with bot.pool.acquire() as conn:
                conn: aiomysql.Connection
                async with conn.cursor() as cursor:
                    cursor: aiomysql.Cursor
                    await cursor.execute("SELECT * FROM verification WHERE user_id = %s",
                        (interaction.user.id,))
                data = await cursor.fetchone()
                ign = data[1]
                profile = data[2]
            try:
                uuid = await bot.get_uuid(ign)
            except ConnectionError as exception:
                print(exception)  # Not caused by user, hence printing
                return await self.send_channel_error_response(thread, "Internal Server Error",
                                                    "Our backend servers encountered an error fetching this information.  If this issue persists, please contact a developer.", interaction.user.id)
            except (InvalidMinecraftUsername, KeyError):
                return await self.send_channel_error_response(thread, "Invalid User", "This account doesn't exist!", interaction.user.id)
            try:
                data = await bot.get_skyblock_data(uuid, profile)
            except ConnectionError as exception:
                print(exception)  # Not caused by user, hence printing
                return await self.send_channel_error_response(thread, "Internal Server Error",
                                                    "Our backend servers encountered an error fetching this information.  If this issue persists, please contact a developer.", interaction.user.id)
            except PlayerNotFoundError:
                return await self.send_channel_error_response(thread, "Invalid User",
                                                    "This player hasn't joined SkyBlock before!", interaction.user.id)
            except ProfileNotFoundError:
                return await self.send_channel_error_response(thread, "Invalid Profile",
                                                    "This profile doesn't exist!  Try a different profile name or leave it blank to default to their most recently played profile.", interaction.user.id)
            except HypixelIsDown:
                e = discord.Embed(title="Hypixel API Error", description=f"As the selling process is entirely ran automatically we rely on Hypixel's API. Sadly it seems like Hypixel's API is currently down. Please try agina soon!", color=discord.Color.red())
                e.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
                await thread.send(embed=e,view = CloseTicket(thread, interaction.user.id))
                await asyncio.sleep(60)
                await close_ticket(bot,thread,bot)

            if "inv_contents" not in data:
                return await Farming.FarmingItems.send_channel_error_response(thread, "API Disabled",
                                                    "You have your API disabled, Please enable it and create another ticket.")
            foundItems = await Farming.FarmingItems.findFarmingItems(self, data["inv_contents"]["data"])
            try:
                for i in data["backpack_contents"]:
                    temp_item = await Farming.FarmingItems.findFarmingItems(self, str(data["backpack_contents"][i]["data"]))
                    if temp_item:
                        for item in temp_item:
                            foundItems.append(item)
            except:
                pass
            try:
                enderchest_contents = await Farming.FarmingItems.findFarmingItems(self, data["ender_chest_contents"]["data"])
                if enderchest_contents:
                    for i in enderchest_contents:
                        foundItems.append(i)
            except:
                pass
            close=False
            if len(foundItems) == 0:
                embed=discord.Embed(
                title="Your Farming Items",
                description="You have no farming items in your inventory!\nNote: The API takes 2-3 minutes to update.",
                colour=0x2F3136)
                view = CloseTicket(thread, interaction.user.id)
                msg = await thread.send(embed=embed)
                tried_times = 0 
                while tried_times < 10:
                    await asyncio.sleep(60)
                    try:
                        user_data = await bot.get_skyblock_data(uuid, profile)
                        new = await Farming.FarmingItems.findFarmingItems(self, user_data["inv_contents"]["data"])
                        for i in data["backpack_contents"]:
                            temp_item = await Farming.FarmingItems.findFarmingItems(self, str(data["backpack_contents"][i]["data"]))
                            if temp_item:
                                for item in temp_item:
                                    new.append(item)
                        enderchest_contents = await Farming.FarmingItems.findFarmingItems(self, data["ender_chest_contents"]["data"])
                        if enderchest_contents:
                            for i in enderchest_contents:
                                new.append(i)
                    except HypixelIsDown:
                        e = discord.Embed(title="Hypixel API Error", description=f"As the selling process is entirely ran automatically we rely on Hypixel's API. Sadly it seems like Hypixel's API is currently down. Please try again soon!\n Trying again in 60 seconds.", color=discord.Color.red())
                        e.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
                        await msg.edit(embed=e)
                        continue
                    if len(new) == 0:
                        embed=discord.Embed(
                            title="Your Farming Items",
                            description=f"You have no farming items in your inventory!\nNote: The API takes 2-3 minutes to update.\nTimes tried: {tried_times}",
                            colour=0x2F3136)
                        await msg.edit(embed=embed)
                        tried_times += 1
                    else:
                        tried_times = 100
                        foundItems=new
                if tried_times!=100 and not tried_times<10:
                    embed=discord.Embed(
                        title="Your Farming Items",
                        description=f"This user has no farming items in their inventory!\nI have tried a total of 10 times.\nPlease place farming items in your inventory and open a new ticket.\nIf you think this is a error, please open a support ticket and tell a admin.\nTicket closing in 60 seconds",
                        colour=0x2F3136)
                    close=True
                    await msg.edit(embed=embed)

            if not close:
                embed=discord.Embed(
                    title="Your Farming Items",
                    description="We have found several items in your inventory. Please select the item you are trying to sell.",
                    colour=0x2F3136
                )
                if len(foundItems) > 24:
                    embed.description = "We have found several items in your inventory. Please select the item you are trying to sell.\nNote: Not all items may be shown as there are too many items to display, please remove some items from your storage or inventory."
                view = discord.ui.View(timeout=300).add_item(Dropdown(foundItems[0:25],bot,thread))
                embed.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")
                await thread.send(embed=embed, view=view)
            if close:
                await asyncio.sleep(60)
                await close_ticket(bot,thread,bot)
