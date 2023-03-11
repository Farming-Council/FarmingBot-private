# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import base64
import nbt
import discord

from typing import Any, Literal, overload

FARMING_ITEMS = [
    "COCO_CHOPPER", 
    "MELON_DICER",
    "PUMPKIN_DICER",
    "CACTUS_KNIFE",
    "FUNGI_CUTTER",
    "THEORETICAL_HOE_WHEAT_1",
    "THEORETICAL_HOE_WHEAT_2",
    "THEORETICAL_HOE_WHEAT_3",
    "THEORETICAL_HOE_POTATO_1",
    "THEORETICAL_HOE_POTATO_2",
    "THEORETICAL_HOE_POTATO_3",
    "THEORETICAL_HOE_CARROT_1",
    "THEORETICAL_HOE_CARROT_2",
    "THEORETICAL_HOE_CARROT_3",
    "THEORETICAL_HOE_WARTS_1",
    "THEORETICAL_HOE_WARTS_2",
    "THEORETICAL_HOE_WARTS_3",
    "THEORETICAL_HOE_CANE_1",
    "THEORETICAL_HOE_CANE_2",
    "THEORETICAL_HOE_CANE_3"
]

GOLD_MEDAL = 1_000_000
SILVER_MEDAL = int(GOLD_MEDAL / 4)
BRONZE_MEDAL = int(SILVER_MEDAL / 2)

CARROT_ITEMS = ["CARROT_ITEM", "ENCHANTED_CARROT", "ENCHANTED_GOLDEN_CARROT"]
POTATO_ITEMS = ["POTATO_ITEM", "ENCHANTED_POTATO", "ENCHANTED_BAKED_POTATO"]
WART_ITEMS = ["NETHER_STALK", "ENCHANTED_NETHER_STALK", "MUTANT_NETHER_STALK"]
WHEAT_ITEMS = ["WHEAT", "ENCHANTED_HAY_BLOCK", "TIGHTLY_TIED_HAY_BALE"]
CANE_ITEMS = ["SUGAR_CANE", "ENCHANTED_SUGAR", "ENCHANTED_SUGAR_CANE"]
jacob_tickets = ["JACOBS_TICKET"]


@overload
def user_mention(_id: int | str | discord.Object, /, regex: Literal[True]) -> str:
    ...


@overload
def user_mention(_id: int | str | discord.Object, /, regex: Literal[False]) -> tuple[str, str]:
    ...


def user_mention(_id: int | str | discord.Object, /, regex: bool = False) -> Any:
    """Creates a mention format that satisfies both <@!12345> and <@12345> mentions.

    Parameters
    ----------
    _id: Union[:class:`int`, :class:`str`, :class:`discord.Object`]
        The ID of the user.
    regex: :class:`bool`
        Whether the returned value should be a regex-like string.
        If disabled, the 2 mentions are returned inside a tuple.
        Defaults to `False`.

    Returns
    -------
    Union[:class:`str`, Tuple[:class:`str`, :class:`str`]]
        A regex-like string that satisfies both mention formats, or a tuple with both mentions if *regex* is `False`.
    """
    if hasattr(_id, "id"):
        _id = _id.id  # type: ignore
    if regex:
        return fr"<@(!)?{_id}>"
    return f"<@!{_id}>", f"<@{_id}>"


def decode_skyblock_item_data(encoded_string: str):
    """Returns the decoded NBT data from the given encoded string

    Parameters
    ----------
    encoded_string: :class:`str`
        The encoded item data

    Returns
    -------
    :class:`nbt.nbt.NBTFile`
        The decoded NBT data from the given encoded string
    """
    return nbt.nbt.NBTFile(fileobj=io.BytesIO(base64.b64decode(encoded_string)))
    
