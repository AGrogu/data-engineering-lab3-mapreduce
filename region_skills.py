import csv
from collections import Counter
from itertools import combinations

PATH = "/Users/macbook/Downloads/it_vacancies_2024.csv"

REGIONS = [
    "Москва",
    "Санкт-Петербург",
    "Екатеринбург",
]

counts = {
    region: {1: Counter(), 2: Counter(), 3: Counter()}
    for region in REGIONS
}

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

        skills = sorted({
            skill.strip()
            for skill in (row["key_skills"] or "").split(";")
            if skill.strip()
        })

        for size in (1, 2, 3):
            counts[region][size].update(
                combinations(skills, size)
            )

with open(
    "region_skills.csv",
    "w",
    encoding="utf-8",
    newline=""
) as file:
    writer = csv.writer(file)

    writer.writerow([
        "region",
        "combination_size",
        "skills",
        "frequency"
    ])

    for region in REGIONS:
        print(f"\nРЕГИОН: {region}")

        for size in (1, 2, 3):
            print(f"\nТоп-5 комбинаций из {size} навыков:")

            for skills, frequency in counts[region][size].most_common(5):
                print(" + ".join(skills), frequency)

                writer.writerow([
                    region,
                    size,
                    "; ".join(skills),
                    frequency,
                ])

print("\nСохранено: region_skills.csv")
