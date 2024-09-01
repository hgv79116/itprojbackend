from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os
import requests

def parsesubject(name, soup):
    print(name)
    output = {}
    
    # blocks start with h2
    for h2 in soup.find_all("h2"):
        section_name = h2.get_text(strip=True).lower()
        
        if "overview" in section_name:
            content = h2.find_next(class_ = "course__overview-wrapper")
            output["overview"] = process_overview(content)
            # print(output["overview"])
        
        elif "ilo" in section_name or "intended learning outcomes" in section_name:
            content = h2
            output["ilo"] = process_ilo_gs(content)
            # print(output["ilo"])
        
        elif "generic skills" in section_name:
            content = h2
            # you might think to yourself it can"t be that generic, to that iI shall quote:
            # "The capacity to solve problems"
            output["generic_skills"] = process_ilo_gs(content)
            # print(output["generic_skills"])

        elif "assessment" in section_name:
            content = h2.find_next(class_ = "assessment-table")
            output["assessment"] = process_assessment(content)
            # print(output["assessment"])

        elif "dates & times" in section_name:
            content = h2
            output["date_times"] = process_datetimes(h2)
            # print(output["date_times"])
        
        elif "eligibility and requirements" in section_name:
            content = h2
            output["elig_req"] = process_eligibility_and_requirements(content)
            print(output["elig_req"])

        else:
            pass

    with open(f"./subject-list/result/metadata/json/{name}.json", "w") as outfile:
        json.dump(output, outfile, indent=4)

def process_overview(content):    
    elements = []
    current_element = content.find_next()

    while current_element:
        # because these h2 of same importance should absolutely contain each other
        if current_element.get("id") in ["learning-outcomes", "generic-skills"]:
            break
        elif current_element.name != "div":
            # this is so retarded that I refuse to parse its html. 
            # take a shot every time they add a <br> that does absolutely nothing 
            elements.append(str(current_element).replace("\n", ""))
        current_element = current_element.find_next_sibling()

    return elements

def process_ilo_gs(content):
    # print(content)
    # sometimes they wont use ticked lists at all! however it is all fine because according to the client,
    # the formatting inconsistencies are entirely explained by "a LaRgE sEt Of cOuRsE rUlEs"
    # ul = content.find_next("ul", class_ = "ticked-list")
    ul = content.find_next("ul")
    # print(ul)
    learning_outcomes = [li.get_text(strip=True) for li in ul.find_all("li")]
    
    return learning_outcomes

def process_assessment(content):
    assessments = []
    table = content.find("table", class_="assessment-details")
    if not table:
        content = content.find_next(class_="assessment-description")
        if content:
            return [{"brief": content.text}]
        else: # i dont fucking know what else is there. they will come up with more of the same shit to describe the same data. i give up.
            return []

    rows = table.find_all("tr")[1:]

    for row in rows:
        cols = row.find_all("td")
        # it is so sensible that this is totally nullable
        brief = cols[0].find("p").get_text(strip=True) if cols[0].find("p") else None
        bullets = [li.get_text(strip=True) for li in cols[0].find_all("li")]
        hurdle = None
        hurdle_strong = cols[0].find("strong", style="color: #ea4f62;")
        if hurdle_strong:
            # because why the fuck would they ever need to wrap a paragraph in a PARAGRAPH TAG
            hurdle = (cols[0].text.split("Hurdle requirement: ") + [""])[1] # oh yeah sometimes the hurdle requirement is just blank because FUCK ME

        timing = cols[1].get_text(strip=True)
        percentage = cols[2].get_text(strip=True)

        assessment = {
            "brief": brief,
            "bullets": bullets if bullets else None,
            "hurdle": hurdle,
            "timing": timing,
            "percentage": percentage
        }
        assessments.append(assessment)

    return assessments

def process_datetimes(content):
    warning_notice = content.find_next("p", class_="notice--warning")

    # print(warning_notice)
    if warning_notice:
        return []
    
    data = []
    accordion = content.find_next("ul", class_="accordion")
    
    if not accordion:
        return data

    for item in accordion.find_all("li"):
        title = item.find("div", class_="accordion__title")
        details = item.find("div", class_="accordion__hidden")
        contact_details = item.find("div", class_="course__body__inner__contact_details")

        if not title or not details:
            continue
        
        semester = title.get_text(strip=True)
        table = details.find("table", class_="zebra contact_details")
        
        principal_coordinator = None
        mode_of_delivery = None
        contact_hours = None
        total_time_commitment = None
        teaching_period = None
        last_self_enrol_date = None
        census_date = None
        last_date_to_withdraw_without_fail = None
        assessment_period_ends = None
        contact_name = None
        contact_email = None
        
        if table:
            for row in table.find_all("tr"):
                th = row.find("th").get_text(strip=True)
                td = row.find("td").get_text(strip=True)
                
                if th == "Principal coordinator":
                    principal_coordinator = td
                elif th == "Mode of delivery":
                    mode_of_delivery = td
                elif th == "Contact hours":
                    contact_hours = td
                elif th == "Total time commitment":
                    total_time_commitment = td
                elif th == "Teaching period":
                    teaching_period = td
                elif th == "Last self-enrol date":
                    last_self_enrol_date = td
                elif th == "Census date":
                    census_date = td
                elif th == "Last date to withdraw without fail":
                    last_date_to_withdraw_without_fail = td
                elif th == "Assessment period ends":
                    assessment_period_ends = td
        
        # either or both of the ps can be nullable. HAHAHAHAHA
        if contact_details:
            for p in contact_details.find_all("p"):
                a = p.find("a")
                if a and a.get("href"):
                    contact_email = a.get_text(strip=True)
                else:
                    contact_name = p.get_text(strip=True)

        data.append({
            "semester": semester,
            "principal_coordinator": principal_coordinator,
            "mode_of_delivery": mode_of_delivery,
            "contact_hours": contact_hours,
            "total_time_commitment": total_time_commitment,
            "teaching_period": teaching_period,
            "last_self_enrol_date": last_self_enrol_date,
            "census_date": census_date,
            "last_date_to_withdraw_without_fail": last_date_to_withdraw_without_fail,
            "assessment_period_ends": assessment_period_ends,
            "contact_name": contact_name,
            "contact_email": contact_email
        })
    
    return data

def process_eligibility_and_requirements(content):
    sections = {}

    # Find all sections
    section_headers = ["Prerequisites", "Corequisites", "Non-allowed subjects", "Recommended background knowledge", "Inherent requirements (core participation requirements)"]
    for header in section_headers:
        section = content.find_next("h3", string=header)
        if section:
            subcontent = section.find_next_sibling()
            sections[header] = parse_section(subcontent)

    return sections

def parse_section(content):
    items = []
    print(content)
    current_element = content.find_next()   

    # there is LITEARALLY no rules to the any of these. they are absolutely not well formatted. and it's absolutely not because of any complex course rules.
    while current_element:
        print(current_element, "dit")
        # do you know that sometimes the paragraph literally contains the table following it?
        if current_element.name == "p":
            if "last-updated" in current_element.get("class", []):
                break
            items.append({
                "type": "paragraph",
                # welcome to "is no requisites represented by <p>None</p> or <p></p>"! 
                "content": current_element.get_text(strip=True)
            })
        elif current_element.name == "ul":
            list_items = [li.get_text(strip=True) for li in current_element.find_all("li")]
            items.append({
                "type": "list",
                "content": list_items
            })
        # with this neat table whose sole purpose is to display subject prerequisites,
        # they wont ever straight up use a paragraph to write "DNCE30011 Dance Technique 5" anywhere right?
        # even worse, they wont ever use a 6 digit nh code in the 2024 handbook like "433-371 Interactive System Design" right?
        elif current_element.name == "table":
            headers = [th.get_text(strip=True) for th in current_element.find_all("th")]
            rows = current_element.find_all("tr")[1:]  # skip header row
            table_data = []
            for row in rows:
                cols = row.find_all("td")
                table_data.append({
                    headers[i]: col.get_text(strip=True)
                    for i, col in enumerate(cols)
                })
            items.append({
                "type": "table",
                "content": table_data
            })
        elif current_element.name == "h3":
            break
        else: # there might very well be some h6 somewhere containing crucial data that i am skipping here. because this is the unimelb handbook written by very professional people with high standards. oh well!
            pass
        current_element = current_element.find_next()

    print("lon\n")
    return items

def parse_subject(code):
    with open(f"./subject-list/result/metadata/raw/{code}.html", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    
    parsesubject(code, soup)

def handle_page(page_id):
    page_path = os.path.join(os.getcwd(), "subject-list", "result", "subjects", f"page{page_id}.json")
    try:
        with open(page_path, "r") as file:
            data = json.load(file)
            codes = [item["code"] for item in data]
            for code in codes:
                parse_subject(code)
    except FileNotFoundError:
        print(f"File page{page_id}.json not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from page{page_id}.json.")

def main():
    load_dotenv() 

    YEAR = os.getenv("YEAR")
    URL = "https://handbook.unimelb.edu.au/search?types%5B%5D=subject&year=" + YEAR
    subjects_page = requests.get(URL)
    subjects_soup = BeautifulSoup(subjects_page.content, "html.parser")
    page_cnt= int(subjects_soup.find(class_ = "search-results__paginate").find_all("option")[-1].text)

    for i in range(1, page_cnt + 1):
        handle_page(i)
    
if __name__ == "__main__":
    main()
    