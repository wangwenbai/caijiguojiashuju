from fastapi import FastAPI
from fastapi.responses import FileResponse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time

app = FastAPI()
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
MAX_CITIES = 10  # 每个国家抓取前10城市

COUNTRY_FILE = "countries.txt"  # 根目录下的文件

# ---------- 读取国家列表 ----------
def read_countries():
    countries = []
    if os.path.exists(COUNTRY_FILE):
        with open(COUNTRY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    countries.append(name)
    return countries

# ---------- 抓取函数 ----------
def fetch_country_cities(country_name):
    urls = [
        f"https://zh.wikipedia.org/wiki/{country_name}城市列表",
        f"https://en.wikipedia.org/wiki/List_of_cities_in_{country_name}"
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=15)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"class": "wikitable"})
            if not table:
                continue
            rows = table.find_all("tr")[1:MAX_CITIES+1]
            results = []
            for row in rows:
                cols = row.find_all(["td","th"])
                if len(cols) >= 2:
                    city = cols[0].get_text(strip=True)
                    pop = cols[1].get_text(strip=True).replace(",", "")
                    try:
                        pop = int(pop)
                    except:
                        pop = 0
                    results.append((city, pop))
            if results:
                return results
        except Exception as e:
            print(f"{country_name}抓取失败: {e}")
            continue
    return [("未找到数据", 0)]

# ---------- API ----------
@app.get("/generate_excel")
def generate_excel():
    rows = []
    countries = read_countries()
    for cname in countries:
        cities = fetch_country_cities(cname)
        for city, pop in cities:
            rows.append([city, pop, cname])
        time.sleep(1)  # 防止频繁请求被封
    df = pd.DataFrame(rows, columns=["城市", "人口", "国家"])
    file_path = os.path.join(DATA_DIR, "country_population.xlsx")
    df.to_excel(file_path, index=False)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="country_population.xlsx"
    )
