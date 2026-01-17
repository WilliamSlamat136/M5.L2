import sqlite3
import matplotlib

matplotlib.use('Agg')  # Menginstal backend Matplotlib untuk menyimpan file dalam memori tanpa menampilkan jendela
import matplotlib.pyplot as plt
import cartopy.crs as ccrs  # Mengimpor modul yang akan memungkinkan kita bekerja dengan proyeksi peta
import cartopy.feature as cfeature
import requests
from datetime import datetime, timedelta
import pytz
from config import WEATHER_API_KEY


def get_time(self, city):
    conn = sqlite3.connect(self.database)
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timezone FROM cities WHERE city = ?",
            (city,)
        )
        result = cursor.fetchone()

    if not result:
        return None

    tz = pytz.timezone(result[0])
    return datetime.now(tz).strftime("%H:%M:%S")


def get_weather(self, city):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
    )
    r = requests.get(url).json()

    if r.get("main"):
        return {
            "temp": r["main"]["temp"],
            "desc": r["weather"][0]["description"]
        }
    return None


class DB_Map():
    def __init__(self, database):
        self.database = database  # Menginisiasi jalur database

    def create_user_table(self):
        conn = sqlite3.connect(self.database)  # Menghubungkan ke database
        with conn:
            # Membuat tabel, jika tidak ada, untuk menyimpan kota pengguna
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()  # Menyimpan perubahan

    def add_city(self, user_id, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            # Mencari kota dalam database berdasarkan nama
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]
                # Menambahkan kota ke daftar kota pengguna
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1  # Menunjukkan bahwa operasi berhasil
            else:
                return 0  # Menunjukkan bahwa kota tidak ditemukan

    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            # Memilih semua kota pengguna
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))
            cities = [row[0] for row in cursor.fetchall()]
            return cities  # Mengembalikan daftar kota pengguna

    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            # Mendapatkan koordinat kota berdasarkan nama
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates  # Mengembalikan koordinat kota

    def create_graph(self, path, cities, marker_color="red"):
        """
        Membuat peta dunia dengan:
        - Benua & lautan berwarna
        - Objek geografis
        - Marker kota dengan warna pilihan user
        """

        fig = plt.figure(figsize=(12, 6))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # 🌊 Lautan
        ax.add_feature(cfeature.OCEAN, facecolor="#AADAFF")

        # 🌍 Daratan / benua
        ax.add_feature(cfeature.LAND, facecolor="#E6E6C3")

        # 🗺️ Objek geografis
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.LAKES, alpha=0.5)
        ax.add_feature(cfeature.RIVERS)

        for city in cities:
            coords = self.get_coordinates(city)
            if coords:
                lat, lng = coords
                ax.plot(
                    lng, lat,
                    marker='o',
                    color=marker_color,
                    markersize=8,
                    transform=ccrs.PlateCarree()
                )
                ax.text(
                    lng + 0.8, lat + 0.8,
                    city,
                    fontsize=9,
                    transform=ccrs.PlateCarree()
                )

        plt.savefig(path, bbox_inches="tight")
        plt.close()

    def get_cities_by_country(self, country):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT city FROM cities WHERE country = ?",
                (country,)
            )
            return [row[0] for row in cursor.fetchall()]

    def get_cities_by_population(self, min_population):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT city FROM cities WHERE population >= ?",
                (min_population,)
            )
            return [row[0] for row in cursor.fetchall()]

    def get_cities_by_country_and_population(self, country, min_pop):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT city FROM cities
                WHERE country = ? AND population >= ?""",
                (country, min_pop)
            )
        return [row[0] for row in cursor.fetchall()]
    
    def get_weather(self, city):
        try:
            url = (
                "https://api.openweathermap.org/data/2.5/weather"
                f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
            )
            response = requests.get(url, timeout=10)
            data = response.json()

            if response.status_code != 200:
                return None

            return {
                "temp": data["main"]["temp"],
                "desc": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"]
            }

        except Exception as e:
            print("Weather error:", e)
            return None

    def get_time(self, city):
        try:
            url = (
                "https://api.openweathermap.org/data/2.5/weather"
                f"?q={city}&appid={WEATHER_API_KEY}"
            )
            r = requests.get(url, timeout=10).json()

            if "timezone" not in r:
                return None

            timezone_offset = r["timezone"]  # detik dari UTC
            utc_time = datetime.utcnow()
            local_time = utc_time + timedelta(seconds=timezone_offset)

            return local_time.strftime("%H:%M:%S")

        except Exception as e:
            print("Time API error:", e)
            return None

    def draw_distance(self, city1, city2, line_color="blue"):
        coords1 = self.get_coordinates(city1)
        coords2 = self.get_coordinates(city2)

        if not coords1 or not coords2:
            return None

        lat1, lng1 = coords1
        lat2, lng2 = coords2

        fig = plt.figure(figsize=(12, 6))
        ax = plt.axes(projection=ccrs.PlateCarree())

        ax.add_feature(cfeature.OCEAN, facecolor="#AADAFF")
        ax.add_feature(cfeature.LAND, facecolor="#E6E6C3")
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.add_feature(cfeature.COASTLINE)

        # ✈️ Garis jarak
        ax.plot(
            [lng1, lng2], [lat1, lat2],
            color=line_color,
            linewidth=2,
            transform=ccrs.PlateCarree()
        )

        ax.scatter(
            [lng1, lng2], [lat1, lat2],
            color="red",
            transform=ccrs.PlateCarree()
        )

        ax.text(lng1, lat1, city1, transform=ccrs.PlateCarree())
        ax.text(lng2, lat2, city2, transform=ccrs.PlateCarree())

        path = "distance.png"
        plt.savefig(path, bbox_inches="tight")
        plt.close()

        return path
    
    
if __name__ == "__main__":
    m = DB_Map("database.db")  # Membuat objek yang akan berinteraksi dengan database
    m.create_user_table()   # Membuat tabel dengan kota pengguna, jika tidak sudah ada