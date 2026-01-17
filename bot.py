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
        "🌍 **GeoMap Discord Bot — Daftar Perintah** 🌍\n\n"

        "🚀 **Dasar**\n"
        "`!start` → Mulai bot\n"
        "`!help_me` → Tampilkan daftar perintah\n\n"

        "📌 **Manajemen Kota**\n"
        "`!remember_city <nama_kota>` → Simpan kota ke daftar kamu\n"
        "`!show_city <warna> <nama_kota>` → Tampilkan satu kota di peta\n"
        "`!show_my_cities <warna>` → Tampilkan semua kota yang kamu simpan\n\n"

        "🌍 **Filter & Visualisasi Kota**\n"
        "`!cities_by_country <negara> <warna>` → Kota dari negara tertentu\n"
        "`!cities_by_population <jumlah_populasi> <warna>` → Kota dengan populasi minimum\n"
        "`!cities_filter <negara> <jumlah_populasi> <warna>` → Filter negara + populasi\n\n"

        "🎨 **Warna Marker**\n"
        "Warna yang didukung: `red`, `blue`, `green`, `purple`, `orange`, `black`\n\n"

        "🌦️ **Informasi Kota**\n"
        "`!weather <nama_kota>` → Cuaca saat ini\n"
        "`!time <nama_kota>` → Waktu lokal kota\n\n"

        "🗺️ **Catatan**\n"
        "- Nama kota & negara gunakan **Bahasa Inggris**\n"
        "- Peta menampilkan benua, lautan, sungai, dan danau\n"
        "- Data diambil dari database & API cuaca\n\n"

        "✨ Selamat menjelajah dunia!"
    )

@bot.command()
async def remember_city(ctx: commands.Context, *, city_name=""):
    if not city_name:
        await ctx.send(
            "❌ Format salah.\n"
            "Gunakan: `!remember_city <nama_kota>`\n"
            "Contoh: `!remember_city Jakarta`"
        )
        return

    result = manager.add_city(ctx.author.id, city_name)

    if result == 1:
        await ctx.send(f"✅ Kota **{city_name}** berhasil disimpan!")
    else:
        await ctx.send(
            "❌ Kota tidak ditemukan.\n"
            "Pastikan:\n"
            "- Nama kota dalam **bahasa Inggris**\n"
            "- Ejaan benar\n"
            "Contoh: `London`, `Tokyo`, `New York`"
        )

@bot.command()
async def show_city(ctx: commands.Context, color="red", *, city_name=""):
    if not city_name:
        await ctx.send("Gunakan: `!show_city <warna> <nama_kota>`")
        return

    path = "city.png"
    manager.create_graph(path, [city_name], marker_color=color)
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

@bot.command()
async def cities_by_country(ctx, country: str, color: str = "red"):
    cities = manager.get_cities_by_country(country)

    if not cities:
        await ctx.send("❌ Tidak ada kota ditemukan.")
        return

    path = "country_cities.png"
    manager.create_graph(path, cities, marker_color=color)
    await ctx.send(file=discord.File(path))

@bot.command()
async def cities_by_population(ctx, min_population: int, color: str = "red"):
    cities = manager.get_cities_by_population(min_population)

    if not cities:
        await ctx.send("❌ Tidak ada kota memenuhi kriteria.")
        return

    path = "population_cities.png"
    manager.create_graph(path, cities, marker_color=color)
    await ctx.send(file=discord.File(path))

@bot.command()
async def cities_filter(ctx, country: str, min_population: int, color: str = "red"):
    cities = manager.get_cities_by_country_and_population(country, min_population)

    if not cities:
        await ctx.send("❌ Tidak ada kota cocok.")
        return

    path = "filter_cities.png"
    manager.create_graph(path, cities, marker_color=color)
    await ctx.send(file=discord.File(path))

@bot.command()
async def weather(ctx, *, city=""):
    if not city:
        await ctx.send("Gunakan: `!weather <nama_kota>`")
        return

    data = manager.get_weather(city)

    if not data:
        await ctx.send("❌ Cuaca tidak ditemukan atau API error.")
        return

    await ctx.send(
        f"🌦️ **Cuaca di {city}**\n"
        f"🌡️ Suhu: {data['temp']}°C\n"
        f"💧 Kelembapan: {data['humidity']}%\n"
        f"☁️ Kondisi: {data['desc']}"
    )

@bot.command()
async def time(ctx, *, city=""):
    if not city:
        await ctx.send("Gunakan: `!time <nama_kota>`")
        return

    t = manager.get_time(city)

    if not t:
        await ctx.send("❌ Zona waktu kota tidak ditemukan.")
        return

    await ctx.send(f"⏰ Waktu di **{city}**: `{t}`")

if __name__ == "__main__":
    bot.run(TOKEN)