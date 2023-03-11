# -*- coding: utf-8 -*-
from __future__ import annotations


class PlayerNotFoundError(Exception):
    def __init__(self, *, username: str | None = None, uuid: str | None = None) -> None:
        self.username: str | None = username
        self.uuid: str | None = uuid
        if username is not None and uuid is not None:
            uuid = f" ({uuid})"
        fmt = "Player {0}{1} not found".format(username or "", uuid or "")
        super().__init__(fmt)


class ProfileNotFoundError(Exception):
    def __init__(self, *, username: str | None = None, uuid: str | None = None, profile: str | None = None) -> None:
        self.username: str | None = username
        self.uuid: str | None = uuid
        self.profile: str | None = profile
        if username is not None and uuid is not None:
            uuid = f" ({uuid})"
        fmt = "Profile {0} for user {1}{2} not found".format(profile or "", username or "", uuid or "")
        super().__init__(fmt)


class InvalidMinecraftUsername(Exception):
    def __init__(self, username: str, /) -> None:
        self.username: str = username
        super().__init__(f"Invalid Minecraft username: {username}")

class HypixelIsDown(Exception):
    def __init__(self) -> None:
        super().__init__(f"Hypixel is down!")
