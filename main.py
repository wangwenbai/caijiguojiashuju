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

# ---------- 国家信息字典 (语言, 时区, 洲) ----------
# 可根据需要扩展
COUNTRY_INFO = {
    "中国": ("汉语", "UTC+8", "亚洲"),
    "美国": ("英语", "UTC-5", "北美洲"),
    "埃及": ("阿拉伯语", "UTC+2", "非洲"),
    "尼日利亚": ("英语", "UTC+1", "非洲"),
    # 这里可以继续填入所有国家主要语言、时区和洲
}

# ---------- 读取国家列表 ----------
def read_countries():
    countries = []
    if os.path.exists(COUNTRY_FILE):
        with open(COUNTRY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split("\t")  # 双列分隔
                    if len(parts) == 2:
                        cn_name, en_name = parts
                    else:
                        cn_name = en_name = parts[0]
                    countries.append((cn_name, en_name))
    return countries

# ---------- 抓取城市函数 ----------
def fetch_country_cities(cn_name, en_name):
    urls = [
        f"https://zh.wikipedia.org/wiki/{cn_name}城市列表",  # 中文 Wikipedia
        f"https://en.wikipedia.org/wiki/List_of_cities_in_{en_name.replace(' ', '_')}"  # 英文 Wikipedia
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
            print(f"{cn_name}抓取失败: {e}")
            continue
    return [("未找到数据", 0)]

# ---------- API ----------
@app.get("/generate_excel")
def generate_excel():
    rows = []
    countries = read_countries()
    for cn_name, en_name in countries:
        cities = fetch_country_cities(cn_name, en_name)
        lang, tz, continent = COUNTRY_INFO.get(cn_name, ("未知", "未知", "未知"))
        for city, pop in cities:
            rows.append([city, pop, cn_name, en_name, lang, tz, continent])
        time.sleep(1)  # 防止请求过快
    df = pd.DataFrame(
        rows,
        columns=["城市", "人口", "国家中文名", "国家英文名", "主要语言", "时区", "洲"]
    )
    file_path = os.path.join(DATA_DIR, "country_population.xlsx")
    df.to_excel(file_path, index=False)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="country_population.xlsx"
    )
