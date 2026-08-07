from discord.ext import commands
from discord import Intents, app_commands
from database import Database
from classes import Game


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=Intents.all())

    async def setup_hook(self):
        await self.tree.sync()
        self.db: Database = Database()
        self.game: Game = Game()
        print("Commands OK")

    async def close(self):
        if hasattr(self, "db"):
            self.db.close()
            print("DB closed.")
        await super().close()
