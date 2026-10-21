import csv
from itertools import combinations

MIN_COUNT = 5


def load_data(size):
    result = {}

    with open(
        f"salary_medians_{size}.csv",
        encoding="utf-8",
        newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            skills = tuple(row["skills"].split("; "))

            result[skills] = {
                "count": int(row["count"]),
                "median": float(row["median_salary"])
            }

    return result


singles = load_data(1)
pairs = load_data(2)
triples = load_data(3)


def calculate_impact(data, bases):
    results = []

    for skills, info in data.items():
        possible_bases = []

        for base in combinations(skills, len(skills) - 1):
            if base in bases:
                possible_bases.append((base, bases[base]))

        if not possible_bases:
            continue

        base, base_info = max(
            possible_bases,
            key=lambda item: item[1]["count"]
        )

        difference = info["median"] - base_info["median"]

        results.append({
            "skills": skills,
            "base": base,
            "count": info["count"],
            "base_count": base_info["count"],
            "median": info["median"],
            "base_median": base_info["median"],
            "difference": difference,
        })

    return results


def show_results(title, results):
    print(f"\n{title}")

    positive = sorted(
        [r for r in results if r["difference"] > 0],
        key=lambda r: -r["difference"]
    )[:10]

    negative = sorted(
        [r for r in results if r["difference"] < 0],
        key=lambda r: r["difference"]
    )[:10]

    for label, items in [
        ("ПОВЫШАЮТ МЕДИАНУ", positive),
        ("ПОНИЖАЮТ МЕДИАНУ", negative),
    ]:
        print(f"\n{label}:")

        for r in items:
            print(
                " + ".join(r["skills"]),
                "| база:", " + ".join(r["base"]),
                "| вакансий:", r["count"],
                "| базовая медиана:", round(r["base_median"]),
                "| медиана:", round(r["median"]),
                "| изменение:", round(r["difference"])
            )


def save_results(filename, results):
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "skills",
            "base_skills",
            "count",
            "base_count",
            "base_median",
            "median",
            "difference"
        ])

        for r in sorted(
            results,
            key=lambda r: -r["difference"]
        ):
            writer.writerow([
                "; ".join(r["skills"]),
                "; ".join(r["base"]),
                r["count"],
                r["base_count"],
                r["base_median"],
                r["median"],
                r["difference"]
            ])


pair_impact = calculate_impact(pairs, singles)
triple_impact = calculate_impact(triples, pairs)

show_results("ПАРЫ НАВЫКОВ", pair_impact)
show_results("ТРОЙКИ НАВЫКОВ", triple_impact)

save_results("salary_impact_pairs.csv", pair_impact)
save_results("salary_impact_triples.csv", triple_impact)

print("\nРезультаты сохранены.")
