# -*- coding: utf-8 -*-
from __future__ import annotations

import io
from typing import TYPE_CHECKING, Literal, NamedTuple
import chat_exporter
import discord
from discord import ui
import os
if TYPE_CHECKING:
    import aiomysql
    from utils import FarmingCouncil

__all__ = (
    "CloseTicket",
)

from dotenv import load_dotenv

load_dotenv()

class AddStaff(discord.ui.View):
    def __init__(self, id, userid):
        super().__init__(timeout=None)
        self.id = id
        self.num = 0
        self.userid = userid
    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary, custom_id="join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        thread = discord.utils.get(interaction.guild.threads,id = self.id)
        user= await interaction.client.fetch_user(self.userid)
        if thread:
            msg = await thread.send(f"{interaction.user.mention}")
            await msg.delete()
            self.num = self.num + 1
            if user:
                embed  = discord.Embed(title="New ticket",description=f"Ticket created by {user.mention} in {thread.mention}\nNumber of staff added: {self.num}",color=0xfcbe03)
                await interaction.followup.send(f"Added to the ticket at {thread.mention}",ephemeral=True)
                await interaction.message.edit(embed=embed,view=self)
            else:
                await thread.send("User left the server\nClose this ticket")
                await interaction.message.edit(view=self)
        else:
            self.join.disabled=True
            await interaction.message.delete()

class _PartialTextChannel(NamedTuple):
    id: int

async def close_ticket(bot:FarmingCouncil,ticket_channel:discord.Thread, close_user: discord.Member):
    transcript = await chat_exporter.export(
        channel=ticket_channel,
        guild=ticket_channel.guild,
        bot=bot,
        support_dev=False
    )
    file = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{ticket_channel.name}.html")
    async with bot.pool.acquire() as conn:
        conn: aiomysql.Connection
        async with conn.cursor() as cursor:
            cursor: aiomysql.Cursor
            await cursor.execute("SELECT * FROM tickets WHERE channel_id = %s", (ticket_channel.id,))
            result = await cursor.fetchone()
    if result:
        if result[5] == 1:
            t_type = "Support "
        else:
            t_type = ""
        embed = discord.Embed(
        title=f"{t_type}Ticket Closed in Farming Council",
        colour=0x2F3136
        )
        embed.add_field(name="\U0001f194 Ticket ID", value=str(result[3]))
        embed.add_field(name="\U0001f512 Closed By", value=close_user.mention)
        embed.add_field(name="\U0001f552 Opened", value=discord.utils.format_dt(ticket_channel.created_at))
        staff_channel = bot.get_channel(int(os.environ.get("SUPPORT_TICKET_CHANNEL")))

        try:
            msg = await staff_channel.fetch_message(result[6])
            await msg.delete()
        except discord.NotFound: 
            pass
    else:
        embed = discord.Embed(
        title=f"Ticket Closed in Farming Council",
        colour=0x2F3136
        )
        embed.add_field(name="\U0001f194 Ticket ID", value="Unknown")
        embed.add_field(name="\U0001f512 Closed By", value=close_user.mention)
        embed.add_field(name="\U0001f552 Opened", value=discord.utils.format_dt(ticket_channel.created_at))
    try:
        user = await bot.fetch_user(result[0])
        message = await user.send(file=file)
    except discord.HTTPException:
        pass
    else:
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="View Transcript Online",
                url=await chat_exporter.link(message),
                emoji="\U0001f4f0"
            )
        )
        #await user.send(embed=embed, view=view)
    transcript_channel = bot.get_channel(int(os.environ.get("LOGS_CHANNEL")))
    if transcript_channel:
        file = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{ticket_channel.name}.html")
        await transcript_channel.send(embed=embed, file=file)
    async with bot.pool.acquire() as conn:
        conn: aiomysql.Connection
        async with conn.cursor() as cursor:
            cursor: aiomysql.Cursor
            await cursor.execute(f"UPDATE tickets SET ticket_status = 1 WHERE channel_id = %s",(ticket_channel.id,))
        await conn.commit()
    await ticket_channel.delete()

class CloseTicket(ui.View):
    def __init__(self, channel: discord.TextChannel, author: int, /) -> None:
        super().__init__(timeout=None)
        self.channel: discord.TextChannel = channel
        self.author: int = author
        self.close_button.custom_id = f"{channel.id}:{author}"

    @classmethod
    def from_database(
            cls,    
            user: int,
            channel_id: int
    ) -> CloseTicket:
        return cls(
            _PartialTextChannel(channel_id),  # type: ignore
            user
        )
    
    async def create(self, bot: FarmingCouncil,/, ticket_id: int ,type:int):
        async with bot.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute(
                    "INSERT INTO tickets (user, channel_id, custom_id, ticket_num, ticket_status, ticket_type) VALUES (%s, %s, %s, %s, %s, %s)",
                    (self.author, self.channel.id, self.close_button.custom_id, ticket_id, 0, type)
                )
            await conn.commit()
        staff_channel = bot.get_channel(int(os.environ.get("SUPPORT_TICKET_CHANNEL")))

        if staff_channel:
            user = await bot.fetch_user(self.author)
            if user:
                embed  = discord.Embed(title="New ticket",description=f"Ticket created by {user.mention} in {self.channel.mention}\nNumber of staff added: 0",color=0x2F3136)
                staff_msg = await staff_channel.send(embed=embed,view = AddStaff(self.channel.id, user.id))
                async with bot.pool.acquire() as conn:
                    conn: aiomysql.Connection
                    async with conn.cursor() as cursor:
                        cursor: aiomysql.Cursor
                        await cursor.execute(f"UPDATE tickets SET ticket_persistent_ids = %s WHERE channel_id = %s",(staff_msg.id, self.channel.id))
                    await conn.commit()
            else:
                await close_ticket(bot,self.channel,bot.user)
    @ui.button(
        label="Close",
        emoji="\U0001f512",
        style=discord.ButtonStyle.danger
    )
    async def close_button(self, interaction: discord.Interaction, button: ui.Button[CloseTicket]) -> None:
        assert interaction.channel is not None
        assert isinstance(interaction.channel, discord.Thread)
        await close_ticket(interaction.client,interaction.channel,interaction.user)