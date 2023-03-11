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


class AntiPing(commands.Cog):
    def __init__(self, bot: FarmingCouncil):
        self.bot: FarmingCouncil = bot
        self.rule_id: int | None = None

    @app_commands.command(name="antiping")
    @app_commands.describe(
        role="The role that shouldn't be mentionable",
        exempt="The role that can mention the blacklisted role. If not present, no roles will be removed.",
        force_create="Whether the rule should be created regardless if it already exists."
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def ensure_antiping(
            self,
            interaction: discord.Interaction,
            role: discord.Role,
            exempt: discord.Role | None = None,
            force_create: bool = False  # Should rarely be used.
    ) -> None:
        """Make all users that have a current role unable to be pinged by anyone"""
        guild = interaction.guild
        assert guild is not None
        await interaction.response.defer(ephemeral=True)
        rules = await guild.fetch_automod_rules()
        members = list(
            itertools.chain(*map(user_mention, filter(lambda m: role in m.roles, guild.members)))  # type: ignore
        )
        for rule in rules:
            if (
                    rule.name.lower() == "anti ping"
                    and rule.trigger.type is discord.AutoModRuleTriggerType.keyword
                    and rule.enabled
            ):
                #  We found our rule, now we compare it to the input
                if not all(mention in rule.trigger.keyword_filter for mention in members):
                    #  Try to add new users
                    trigger_list = {
                        *rule.trigger.keyword_filter,
                        *members
                    }
                    if len(trigger_list) > 1000:
                        #  We should never reach this part of the code, but we might as well add
                        #  some sort of handling to it while we're at it
                        return await interaction.followup.send(
                            "It appears that there are too many users in the current AutoMod rule."
                        )
                    r = await rule.edit(
                        trigger=discord.AutoModTrigger(
                            type=discord.AutoModRuleTriggerType.keyword,
                            keyword_filter=list(trigger_list)
                        ),
                        reason=f"Blacklist {role.name} ({role.id}) from being mentioned"
                    )
                    self.rule_id = r.id
                    return await interaction.followup.send(
                        f"Updated {role.mention} to the pre-existing `{rule.name}` rule."
                    )
                if exempt is not None and exempt not in rule.exempt_roles:
                    #  Try to add new exempt roles
                    exempt_roles = {*rule.exempt_roles, exempt}
                    #  If you're getting a TypeError: Role object is not JSON serializable in this line,
                    #  update discord.py. This issue has been fixed in the latest version.
                    #  See discord.py issue #9159 for more information
                    r = await rule.edit(
                        exempt_roles=list(exempt_roles),
                        reason="Add new exempt roles"
                    )
                    self.rule_id = r.id
                    return await interaction.followup.send(
                        f"Updated exempt role list and added {exempt.mention}."
                    )
                #  The rule already exists by now and is completely identical to what we currently have.
                #  We don't want to create an exact copy, so we either delete it or let the user know
                #  that it already exists
                if not force_create:
                    self.rule_id = rule.id
                    return await interaction.followup.send("An anti-ping rule already exists.")
                await rule.delete(reason="Recreate this rule.")
                break
        if not guild.me.guild_permissions.manage_guild:
            return await interaction.followup.send("I do not have enough permissions to create a new AutoMod rule.")
        r = await guild.create_automod_rule(
            name="Anti Ping",
            event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(
                type=discord.AutoModRuleTriggerType.keyword,
                keyword_filter=members
            ),
            actions=[discord.AutoModRuleAction()],
            enabled=True,
            reason=f"Blacklist role {role.name} ({role.id}) from being mentioned",
            exempt_roles=([exempt] if exempt is not None else [])  # type: ignore
        )
        self.rule_id = r.id
        await interaction.followup.send(
            f"Successfully removed the ability to mention anyone that current the {role.mention} role."
        )

    @commands.Cog.listener()
    async def on_automod_action(self, execution: discord.AutoModAction):
        if execution.rule_id == self.rule_id:
            channel = execution.channel
            if channel is not None:
                assert execution.member is not None
                embed = discord.Embed(
                    title=f"{execution.member} said:",
                    description=f"{execution.content}",
                    colour=discord.Colour.blue()
                )
                embed.set_footer(
                    text="This message got sent because you are not allowed to mention Administrators in this server. "
                         "Mentions in embeds don't ping users."
                )
                embed.set_footer(text="Made by FarmingCouncil", icon_url="https://i.imgur.com/4YXjLqq.png")

                await channel.send(embed=embed)  # type: ignore

async def setup(bot: FarmingCouncil) -> None:
    await bot.add_cog(AntiPing(bot))