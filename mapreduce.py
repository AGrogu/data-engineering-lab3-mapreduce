import csv
import io
import getpass
from collections import Counter
from itertools import combinations

import boto3
from botocore.config import Config

BUCKET = "hh-lake"
KEY = "it_vacancies_2024.csv"
CHUNK_SIZE = 1000

secret_key = getpass.getpass("Введите секретный ключ RustFS: ")

s3 = boto3.client(
    "s3",
    endpoint_url="http://127.0.0.1:9000",
    aws_access_key_id="rustfsadmin",
    aws_secret_access_key=secret_key,
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)


def is_python_vacancy(row):
    name = (row["name"] or "").lower()
    role = row["role"] or ""

    return (
        role == "Программист, разработчик"
        and "python" in name
    )


def map_chunk(chunk):
    result = {
        1: Counter(),
        2: Counter(),
        3: Counter(),
    }

    selected = 0
    with_skills = 0

    for row in chunk:
        if not is_python_vacancy(row):
            continue

        selected += 1

        skills = sorted({
            skill.strip()
            for skill in (row["key_skills"] or "").split(";")
            if skill.strip()
        })

        if not skills:
            continue

        with_skills += 1

        for size in (1, 2, 3):
            result[size].update(combinations(skills, size))

    return result, selected, with_skills


def reduce_results(total, partial):
    for size in (1, 2, 3):
        total[size].update(partial[size])


def save_results(size, counter):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["skills", "count"])

    for skills, count in sorted(
        counter.items(),
        key=lambda item: (-item[1], item[0])
    ):
        writer.writerow(["; ".join(skills), count])

    key = f"results/skills_{size}.csv"

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=output.getvalue().encode("utf-8"),
    )

    print(f"Сохранено: s3://{BUCKET}/{key}")


def main():
    response = s3.get_object(
        Bucket=BUCKET,
        Key=KEY,
    )

    stream = io.TextIOWrapper(
        response["Body"],
        encoding="utf-8-sig",
        newline="",
    )

    reader = csv.DictReader(stream)

    totals = {
        1: Counter(),
        2: Counter(),
        3: Counter(),
    }

    chunk = []

    total_rows = 0
    selected_rows = 0
    rows_with_skills = 0
    chunks_processed = 0

    def process_chunk(rows):
        nonlocal selected_rows
        nonlocal rows_with_skills
        nonlocal chunks_processed

        partial, selected, with_skills = map_chunk(rows)

        reduce_results(totals, partial)

        selected_rows += selected
        rows_with_skills += with_skills
        chunks_processed += 1

    for row in reader:
        total_rows += 1
        chunk.append(row)

        if len(chunk) == CHUNK_SIZE:
            process_chunk(chunk)
            chunk = []

    if chunk:
        process_chunk(chunk)

    stream.close()

    print("\nРЕЗУЛЬТАТЫ MAPREDUCE")
    print("Всего вакансий:", total_rows)
    print("Python-вакансий:", selected_rows)
    print("Python-вакансий с навыками:", rows_with_skills)
    print("Обработано чанков:", chunks_processed)

    for size in (1, 2, 3):
        print(f"\nКомбинации из {size} навыков:")
        print("Уникальных комбинаций:", len(totals[size]))

        for skills, count in totals[size].most_common(10):
            print(" + ".join(skills), count)

        save_results(size, totals[size])


if __name__ == "__main__":
    main()
