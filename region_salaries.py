import csv
from collections import defaultdict
from statistics import median

PATH = "/Users/macbook/Downloads/it_vacancies_2024.csv"

REGIONS = [
    "Москва",
    "Санкт-Петербург",
    "Екатеринбург",
]

counts = defaultdict(int)
salaries = defaultdict(list)


def get_salary(row):
    if row["currency"] != "RUR":
        return None

    salary_from = row["salary_from"]
    salary_to = row["salary_to"]

    if not salary_from and not salary_to:
        return None

    if salary_from and salary_to:
        return (float(salary_from) + float(salary_to)) / 2

    return float(salary_from or salary_to)


with open(PATH, encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        name = (row["name"] or "").lower()
        role = row["role"] or ""
        region = (row["area"] or "").strip()

        if role != "Программист, разработчик":
            continue

        if "python" not in name:
            continue

        if region not in REGIONS:
            continue

        counts[region] += 1

        salary = get_salary(row)

        if salary is not None:
            salaries[region].append(salary)


with open(
    "region_salaries.csv",
    "w",
    encoding="utf-8",
    newline=""
) as file:
    writer = csv.writer(file)

    writer.writerow([
        "region",
        "vacancies",
        "vacancies_with_salary",
        "median_salary_rub",
    ])

    print("РЕГИОНАЛЬНЫЙ АНАЛИЗ ЗАРПЛАТ")

    for region in REGIONS:
        values = salaries[region]
        med = median(values) if values else None

        writer.writerow([
            region,
            counts[region],
            len(values),
            med,
        ])

        print(
            region,
            "| вакансий:", counts[region],
            "| с зарплатой:", len(values),
            "| медиана:", round(med, 2) if med is not None else "нет данных",
            "руб."
        )

print("\nСохранено: region_salaries.csv")
