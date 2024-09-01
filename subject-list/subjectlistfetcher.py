import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv() 

YEAR = os.getenv("YEAR")
URL = "https://handbook.unimelb.edu.au/search?types%5B%5D=subject&year=" + YEAR
subjects_page = requests.get(URL)

subjects_soup = BeautifulSoup(subjects_page.content, "html.parser")

page_list = [item.text for item in subjects_soup.find(class_ = "search-results__paginate").find_all("option")]

for page_id in page_list:

    file_path = os.path.join(os.getcwd(), "subject-list", "result", "subjects", f"page{page_id}.json")
    if os.path.exists(file_path):
        continue

    print(page_id)
    URL = "https://handbook.unimelb.edu.au/search?types%5B%5D=subject&year=" + YEAR + "&page=" + page_id + "&sort=external_code%7Csc"
    subjects_page = requests.get(URL)

    subjects_soup = BeautifulSoup(subjects_page.content, "html.parser")
    subject_items = subjects_soup.find(class_ = "search-results__list").find_all(class_ = "search-result-item--subject")
    cur_page_subjects = []
    for subject_item in subject_items:
        new_subject = dict()
        new_subject["code"] = subject_item.find(class_ = "search-result-item__code").text
        new_subject["name"] = subject_item.find(class_ = "search-result-item__name").find("h3").text
        new_subject["availability"] = subject_item.find(class_ = "search-result-item__meta-primary").text
        level_credit = subject_item.find(class_ = "search-result-item__meta-secondary").text.split(", ") + ["null credit points "]
        new_subject["level"] = level_credit[0]
        new_subject["credit"] = level_credit[1][:-1]
        cur_page_subjects.append(new_subject)

    with open(file_path, "w") as file:
        json.dump(cur_page_subjects, file, indent=4)