# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import NamedTuple


class HypixelSocialMedia(NamedTuple):
    instagram: str | None = None
    youtube: str | None = None
    twitch: str | None = None
    twitter: str | None = None
    hypixel: str | None = None
    mixer: str | None = None
    discord: str | None = None
    beam: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, str | None], /) -> HypixelSocialMedia:
        links: dict[str, str | None] | None = d.get("links")  # type: ignore
        if links is None:
            return HypixelSocialMedia(
                instagram=d.get("INSTAGRAM"),
                youtube=d.get("YOUTUBE"),
                twitch=d.get("TWITCH"),
                beam=d.get("BEAM"),
            )
        return HypixelSocialMedia(
            instagram=d.get("INSTAGRAM"),
            youtube=links.get("YOUTUBE"),
            hypixel=links.get("HYPIXEL"),
            twitter=links.get("TWITTER"),
            mixer=links.get("MIXER"),
            discord=links.get("DISCORD"),
            twitch=d.get("TWITCH"),
            beam=d.get("BEAM"),
        )


class HypixelPlayer(NamedTuple):
    username: str
    uuid: str
    social_media: HypixelSocialMedia
