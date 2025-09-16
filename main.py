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

MAX_CITIES = 10  # 每个国家抓取前10城市，可修改

# ---------- 国家列表 ----------
countries = [
    ("中国","China","汉语","UTC+8","亚洲"),
    ("美国","United States","英语","UTC-5","北美洲"),
    ("埃及","Egypt","阿拉伯语","UTC+2","非洲"),
    ("尼日利亚","Nigeria","英语","UTC+1","非洲"),
    ("印度","India","印地语","UTC+5:30","亚洲"),
    # ... 可继续添加全球其他国家
]

# ---------- 抓取函数 ----------
def fetch_country_cities(country_cn, country_en):
    urls = [
        f"https://zh.wikipedia.org/wiki/{country_cn}城市列表",
        f"https://en.wikipedia.org/wiki/List_of_cities_in_{country_en}"
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
            print(f"{country_cn}抓取失败: {e}")
            continue
    return [("未找到数据",0)]

# ---------- API ----------
@app.get("/generate_excel")
def generate_excel():
    rows = []
    for cname_cn, cname_en, lang, tz, continent in countries:
        cities = fetch_country_cities(cname_cn, cname_en)
        for city, pop in cities:
            rows.append([city, pop, cname_cn, lang, tz, continent])
        time.sleep(1)  # 防止频繁请求被封
    df = pd.DataFrame(rows, columns=["城市","人口","国家","语言","时区","洲"])
    file_path = os.path.join(DATA_DIR, "global_country_population.xlsx")
    df.to_excel(file_path, index=False)
    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="global_country_population.xlsx")
