import os
import requests
from dotenv import load_dotenv

load_dotenv()

HH_API_URL = os.getenv("HH_API_URL")
COUNTRY_NAME = os.getenv("COUNTRY_NAME")

def get_city_id(city_name: str):
    response = requests.get(f"{HH_API_URL}/areas")
    if response.status_code != 200:
        return None

    data = response.json()
    russia = next((country for country in data if country["name"].lower() == COUNTRY_NAME.lower()), None)
    if not russia:
        return None

    city_name_lower = city_name.lower()

    def search_in_areas(areas):
        for area in areas:
            if area["name"].lower() == city_name_lower:
                return area["id"]
            if area.get("areas"):
                result = search_in_areas(area["areas"])
                if result:
                    return result
        return None

    return search_in_areas(russia["areas"])


def get_vacancies(city_name, keyword, experience):
    city_id = get_city_id(city_name)
    if not city_id:
        return None

    params = {
        "text": keyword,
        "area": city_id,
        "experience": experience,
        "per_page": 5
    }

    response = requests.get(f"{HH_API_URL}/vacancies", params=params)
    if response.status_code != 200:
        return None

    data = response.json()
    vacancies = []

    for item in data.get("items", []):
        salary = item.get("salary")
        if salary:
            if salary.get("from") and salary.get("to"):
                salary_text = f"{salary['from']}–{salary['to']} {salary.get('currency', '')}"
            elif salary.get("from"):
                salary_text = f"от {salary['from']} {salary.get('currency', '')}"
            elif salary.get("to"):
                salary_text = f"до {salary['to']} {salary.get('currency', '')}"
            else:
                salary_text = "Не указана"
        else:
            salary_text = "Не указана"

        vacancies.append({
            "name": item["name"],
            "employer": item["employer"]["name"] if item.get("employer") else "Не указано",
            "area": item["area"]["name"],
            "salary": salary_text,
            "alternate_url": item["alternate_url"]
        })

    return vacancies