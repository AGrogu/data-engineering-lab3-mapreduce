import csv
from collections import defaultdict
from itertools import combinations
from statistics import median

PATH = "/Users/macbook/Downloads/it_vacancies_2024.csv"

salaries = {
    1: defaultdict(list),
    2: defaultdict(list),
    3: defaultdict(list),
}

vacancies_with_salary = 0
vacancies_with_salary_and_skills = 0


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

        if role != "Программист, разработчик":
            continue

        if "python" not in name:
            continue

        salary = get_salary(row)

        if salary is None:
            continue

        vacancies_with_salary += 1

        skills = sorted({
            skill.strip()
            for skill in (row["key_skills"] or "").split(";")
            if skill.strip()
        })

        if not skills:
            continue

        vacancies_with_salary_and_skills += 1

        for size in (1, 2, 3):
            for combo in combinations(skills, size):
                salaries[size][combo].append(salary)


print("Python-вакансий с зарплатой в рублях:",
      vacancies_with_salary)

print("Из них с заполненными навыками:",
      vacancies_with_salary_and_skills)


for size in (1, 2, 3):
    results = []

    for combo, values in salaries[size].items():
        if len(values) >= 5:
            results.append(
                (combo, len(values), median(values))
            )

    results.sort(key=lambda x: (-x[1], x[0]))

    filename = f"salary_medians_{size}.csv"

    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["skills", "count", "median_salary"])

        for combo, count, med in results:
            writer.writerow([
                "; ".join(combo),
                count,
                med
            ])

    print(f"\nКомбинации из {size} навыков")
    print("Комбинаций с минимум 5 вакансиями:", len(results))
    print("Топ-10 по количеству вакансий:")

    for combo, count, med in results[:10]:
        print(
            " + ".join(combo),
            "| вакансий:", count,
            "| медиана:", round(med, 2), "руб."
        )

    print("Сохранено:", filename)
