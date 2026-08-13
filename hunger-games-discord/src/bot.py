from discord.ext import commands
from discord import Intents
from classes import Game
from os import getenv
from dotenv import load_dotenv


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=Intents.all())
        self.game: Game = Game()

    async def setup_hook(self):
        await self.load_extension("cogs.guest")
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.tribute")
        await self.tree.sync()
        print("Commands OK")


load_dotenv()
bot: Bot = Bot()


@bot.event
async def on_ready():
    print(f"{bot.user} OK")


if __name__ == "__main__":
    try:
        bot.run(getenv("DISCORD_TOKEN"))
    except KeyboardInterrupt:
        print("Server closed.")
