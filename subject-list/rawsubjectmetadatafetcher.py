import asyncio
import aiohttp
import requests
import os
import json
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv() 

YEAR = os.getenv("YEAR")
URL = "https://handbook.unimelb.edu.au/search?types%5B%5D=subject&year=" + YEAR
subjects_page = requests.get(URL)

subjects_soup = BeautifulSoup(subjects_page.content, "html.parser")

page_cnt= int(subjects_soup.find(class_ = "search-results__paginate").find_all("option")[-1].text)
# print(page_cnt)
# exit()

async def fetch_and_save(session, code):
    url = f"https://handbook.unimelb.edu.au/{YEAR}/subjects/{code}/print"
    metadata_path = os.path.join(os.getcwd(), "subject-list", "result", "metadata", "raw", f"{code}.html")
    if os.path.exists(metadata_path):
        return

    async with session.get(url) as response:
        content = await response.text()
        with open(metadata_path, "w", encoding="utf-8") as file:
            file.write(content)

async def handle_page(page_id, session):
    page_path = os.path.join(os.getcwd(), "subject-list", "result", "subjects", f"page{page_id}.json")
    try:
        with open(page_path, "r") as file:
            data = json.load(file)
            codes = [item["code"] for item in data]
            tasks = [fetch_and_save(session, code) for code in codes]
            await asyncio.gather(*tasks)
    except FileNotFoundError:
        print(f"File page{page_id}.json not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from page{page_id}.json.")

async def bounded_handle_page(sem, page_id, session):
    async with sem:
        await handle_page(page_id, session)

async def main(page_cnt):
    sem = asyncio.Semaphore(10)
    async with aiohttp.ClientSession() as session:
        tasks = [bounded_handle_page(sem, i, session) for i in range(1, page_cnt + 1)]
        await asyncio.gather(*tasks)

asyncio.run(main(page_cnt))