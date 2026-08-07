from asyncio import sleep
from os import getenv
from dotenv import load_dotenv
from discord import app_commands, Interaction
from shared import error_handler
from bot import Bot

load_dotenv()
bot: Bot = Bot()


@bot.event
async def on_ready():
    print(f"Logged as {bot.user}")


@bot.tree.command(name="sign")
async def sign(interaction: Interaction):
    async with error_handler(interaction):
        user = interaction.user
        bot.db.upsert({"username": user.name, "id": user.id})
        bot.game.set_tribute(id=user.id, username=user.name)
        await interaction.response.send_message(
            "Te anotaste a los juegos.", ephemeral=True
        )


@bot.tree.command(name="start")
@app_commands.checks.has_permissions(administrator=True)
async def start(interaction: Interaction):
    async with error_handler(interaction):
        bot.game.is_playing = True
        count: int = 3
        await interaction.response.send_message(f"Los juegos empezarán en: {count}")
        while count > 1:
            await sleep(1)
            count -= 1
            await interaction.edit_original_response(
                content=f"Los juegos empezarán en: {count}"
            )
        await sleep(1)
        await interaction.edit_original_response(content=f"Suerte")


if __name__ == "__main__":
    try:
        bot.run(getenv("DISCORD_TOKEN"))
    except KeyboardInterrupt:
        print("Server closed.")
