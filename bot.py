# -*- coding: utf-8 -*-
from __future__ import annotations

from utils import FarmingCouncil
from dotenv import load_dotenv
import os

load_dotenv()

bot = FarmingCouncil()

if __name__ == "__main__":
    bot.run(os.environ.get("TOKEN"))
    # os.environ.get("TOKEN")
    # "MTA1NzE2ODU3OTcxMzMxMDgyMQ.GXgQ7N.do1zwgAUZq3QmLyO8uQHepetNl7k7ObYpJx96s"