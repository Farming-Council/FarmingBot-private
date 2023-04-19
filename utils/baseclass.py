# -*- coding: utf-8 -*-
from __future__ import annotations

import pkgutil

from typing import Any, ClassVar

import aiohttp
import aiomysql
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

from errors import InvalidMinecraftUsername, PlayerNotFoundError, ProfileNotFoundError, HypixelIsDown
from _types import HypixelPlayer, HypixelSocialMedia
from cogs.tickets import CloseTicket, TicketHandler, ContactStaffTickets, AddStaff
import random
load_dotenv()

class FarmingCouncil(commands.Bot):
    API_KEY: ClassVar[str] = os.environ.get("hypixel_api_key")
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=discord.Intents.all(), help_command=None, owner_id=702385226407608341)
        self.session: aiohttp.ClientSession | None = None
        self.pool: aiomysql.Pool = None  # type: ignore

    async def on_command_error(
            self,
            context: commands.Context[FarmingCouncil],
            exception: commands.CommandError,
            /
    ) -> None:
        if isinstance(exception, commands.NotOwner):
            await context.send(
                embed=discord.Embed(
                    title="\U00002757 Error",
                    description="You need to own this bot to use this command!",
                    colour=discord.Colour.red()
                )
            )
        else:
            raise exception

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        self.pool = await aiomysql.create_pool(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USERNAME"),
            password=os.environ.get("DB_PASSWORD"),
            db=os.environ.get("DB_NAME"),
            port = 32813,
            loop=self.loop
        )
        # async with self.pool.acquire() as conn:
        #     conn: aiomysql.Connection
        #     async with conn.cursor() as cursor:
        #         cursor: aiomysql.Cursor
        #         await cursor.execute("""
        #         DROP TABLE IF EXISTS verification""")

        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS verification (
                        user_id BIGINT NOT NULL UNIQUE,
                        ign TEXT NOT NULL,
                        profile TEXT NOT NULL,
                        timestamp BIGINT DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )"""
                )
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS tickets (
                        user BIGINT NOT NULL,
                        channel_id BIGINT NOT NULL,
                        custom_id TEXT NOT NULL,
                        ticket_num INT NOT NULL,
                        ticket_status INT NOT NULL,
                        ticket_type INT NOT NULL,
                        ticket_persistent_ids TEXT,
                        timestamp BIGINT DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )"""
                )
            await conn.commit()
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute(
                    """CREATE TABLE IF NOT EXISTS logs (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        serverid BIGINT NOT NULL,
                        userid BIGINT, 
                        operatorid BIGINT,
                        event TEXT,
                        timestamp BIGINT DEFAULT CURRENT_TIMESTAMP NOT NULL
                    
                            )"""
                )
            await conn.commit()
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute(
                """CREATE TABLE IF NOT EXISTS server (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            serverid BIGINT NOT NULL,
                            verify BOOL, 
                            method INT,
                            channel BIGINT,
                            role BIGINT,
                            disabled BOOL DEFAULT False
                        );
                    """    
                )
            await conn.commit()
        for cog in pkgutil.iter_modules(["cogs"], prefix="cogs."):
                await self.load_extension(cog.name)
        self.add_view(TicketHandler())
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT user, channel_id FROM tickets")
                tiks: list[tuple[Any, ...]] = await cursor.fetchall()

        for user, channel_id in tiks:
            self.add_view(CloseTicket.from_database(user, channel_id))
            self.add_view(AddStaff(channel_id, user))

        self.add_view(ContactStaffTickets())

    async def on_ready(self) -> None:

        await self.tree.sync()
        print(f"Logged in as {self.user} ({self.user.id})")  # type: ignore

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()
        if self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
        await super().close()
    async def add_crop(self,cropname, link):
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("INSERT INTO tutorial (cropname, link) VALUES (%s, %s) ON DUPLICATE KEY UPDATE link = %s", (str(cropname), str(link), str(link)))
                await conn.commit()
    
    
    
    async def remove_crop(self,cropname):
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("DELETE FROM tutorial where cropname = %s", (str(cropname),))
                await conn.commit()
                
                
                
    async def get_uuid(self, username: str) -> str:
        if self.session is None:
            raise ConnectionError("aiohttp session has not been set")
        if not username.isalnum() and "_" not in username:
            raise InvalidMinecraftUsername(username)
        async with self.session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}") as req:
            if req.status != 200:
                raise KeyError(f"Recieved status code: {req.status}")
            js = await req.json()
            return js["id"]



    async def get_hypixel_player(self, uuid: str) -> HypixelPlayer:
        if self.session is None:
            raise ConnectionError("aiohttp session has not been set")
        async with self.session.get(
            f"https://api.hypixel.net/player?uuid={uuid}",
            headers={"API-Key": self.API_KEY}
        ) as req:
            info = await req.json()
            if not info["success"] or not info["player"]:
                raise PlayerNotFoundError(uuid=uuid)
            social_media = HypixelSocialMedia.from_dict(info["player"]["socialMedia"])
            return HypixelPlayer(
                username=info["player"]["displayname"],
                uuid=info["player"]["uuid"],
                social_media=social_media
            )



    async def get_skyblock_data(self, uuid: str, profile: str | None) -> HypixelPlayer:
        if self.session is None:
            raise ConnectionError("aiohttp session has not been set")
        async with self.session.get(
            f"https://api.hypixel.net/skyblock/profiles?uuid={uuid}",
            headers={"API-Key": self.API_KEY}
        ) as req:
            try:
                info = await req.json()
            except:
                raise HypixelIsDown()

            if not info["success"] or not info["profiles"]:
                raise PlayerNotFoundError(uuid=uuid)

            profiles = info["profiles"]
            if len(profiles) == 0:
                raise PlayerNotFoundError(uuid=uuid)

            if profile is not None:
                for profileData in profiles:
                    if profileData["cute_name"].lower() == profile.lower():
                        return profileData["members"][uuid]
                raise ProfileNotFoundError(uuid=uuid, profile=profile)
            latest_profile_index = 0
            latest_profile_last_save = 0
            i = 0
            for profileData in profiles:
                if "last_save" in profileData:  # Not all profiles have this
                    last_save = profileData["last_save"]
                    if last_save > latest_profile_last_save:
                        latest_profile_index = i
                        latest_profile_last_save = last_save
                i += 1
            return profiles[latest_profile_index]["members"][uuid]
        
        
        
    async def get_most_recent_profile(self, uuid):
        if self.session is None:
            raise ConnectionError("aiohttp session has not been set")
        async with self.session.get(
            f"https://api.hypixel.net/skyblock/profiles?uuid={uuid}",
            headers={"API-Key": self.API_KEY}
        ) as req:
            try:
                info = await req.json()
            except:
                raise HypixelIsDown()

            if not info["success"] or not info["profiles"]:
                raise PlayerNotFoundError(uuid=uuid)

            profiles = info["profiles"]
            if len(profiles) == 0:
                raise PlayerNotFoundError(uuid=uuid)

            latest_profile_index = 0
            latest_profile_last_save = 0
            i = 0
            for profileData in profiles:
                if "last_save" in profileData:  # Not all profiles have this
                    last_save = profileData["last_save"]
                    if last_save > latest_profile_last_save:
                        latest_profile_index = i
                        latest_profile_last_save = last_save
                i += 1
            return(profiles[latest_profile_index]["cute_name"])
        
        
        
    async def get_db_info(self,discord_id):
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT * FROM verification WHERE user_id = %s", (discord_id,))
                ign = await cursor.fetchone()
        if ign:
            return ign[0]
        else:
            return None
        
        
        
    async def newserver(self, id):
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT * FROM server WHERE serverid = %s", (int(id),))
                item = await cursor.fetchone()

        if item:
            return(1)
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("INSERT INTO server(serverid) VALUES (%s)", (int(id),))
                await conn.commit()
        return(0)



    async def getserver(self, id):
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT * FROM server WHERE serverid = %s", (int(id),))
                item = await cursor.fetchone()
        return(item)



    async def changesettings(self,serverid,setting,value):
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute("SELECT * FROM server WHERE serverid =%s", (int(serverid),))
                item = await cursor.fetchone()

        if not item:
            return(0)
        async with self.pool.acquire() as conn:
            conn: aiomysql.Connection
            async with conn.cursor() as cursor:
                cursor: aiomysql.Cursor
                await cursor.execute(f"UPDATE server SET {setting} = %s WHERE serverid = %s", (value,int(serverid),))
                await conn.commit()
        return(1)



    def get_ran(self,list):
        a = random.randint(-50,100)
        if a in list:
            return(self.get_ran(list))
        else:
            return a