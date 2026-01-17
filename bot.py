from config import *
from logic import *
import discord
from discord.ext import commands
from config import TOKEN

# Menginisiasi pengelola database
manager = DB_Map("database.db")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot started")

@bot.command()
async def start(ctx: commands.Context):
    await ctx.send(f"Halo, {ctx.author.name}. Masukkan !help_me untuk mengeksplorasi daftar perintah yang tersedia")

@bot.command()
async def help_me(ctx: commands.Context):
    await ctx.send(
        "**Daftar Perintah:**\n"
        "`!start` → Mulai bot\n"
        "`!remember_city <city>` → Simpan kota\n"
        "`!show_city <city>` → Tampilkan kota di peta\n"
        "`!show_my_cities` → Tampilkan semua kota yang kamu simpan"
    )


@bot.command()
async def show_city(ctx: commands.Context, *, city_name=""):
    if not city_name:
        await ctx.send("Masukkan nama kota.")
        return

    path = "city.png"
    manager.create_graph(path, [city_name])
    await ctx.send(file=discord.File(path))


@bot.command()
async def show_my_cities(ctx: commands.Context):
    cities = manager.select_cities(ctx.author.id)

    if not cities:
        await ctx.send("Kamu belum menyimpan kota apa pun.")
        return

    path = "my_cities.png"
    manager.create_graph(path, cities)
    await ctx.send(file=discord.File(path))

if __name__ == "__main__":
    bot.run(TOKEN)