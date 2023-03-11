# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from .close import CloseTicket,AddStaff
from .cog import Ticketing
from .persistent import Form, TicketHandler, Dropdown, ContactStaffTickets

if TYPE_CHECKING:
    from utils import FarmingCouncil

__all__ = ("CloseTicket", "Form", "TicketHandler", "Ticketing", "setup", "ContactStaffTickets", "AddStaff")

async def setup(bot: FarmingCouncil) -> None:
    await bot.add_cog(Ticketing(bot))