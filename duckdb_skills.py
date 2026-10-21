import duckdb
import boto3
import csv
import io
import getpass
from botocore.config import Config

secret = getpass.getpass("Введите секретный ключ RustFS: ")

con = duckdb.connect()

con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")

con.execute("""
    CREATE SECRET rustfs_secret (
        TYPE S3,
        KEY_ID 'rustfsadmin',
        SECRET ?,
        REGION 'us-east-1',
        ENDPOINT '127.0.0.1:9000',
        USE_SSL false,
        URL_STYLE 'path'
    )
""", [secret])

s3 = boto3.client(
    "s3",
    endpoint_url="http://127.0.0.1:9000",
    aws_access_key_id="rustfsadmin",
    aws_secret_access_key=secret,
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)

base_sql = """
WITH vacancies AS (
    SELECT
        row_number() OVER () AS vacancy_num,
        key_skills
    FROM read_csv(
        's3://hh-lake/it_vacancies_2024.csv',
        header = true,
        all_varchar = true
    )
    WHERE role = 'Программист, разработчик'
      AND contains(lower(coalesce(name, '')), 'python')
),
skills AS (
    SELECT DISTINCT
        vacancy_num,
        trim(skill) AS skill
    FROM vacancies,
    UNNEST(
        string_split(coalesce(key_skills, ''), ';')
    ) AS t(skill)
    WHERE trim(skill) <> ''
)
"""

queries = {
    1: """
        SELECT a.skill AS s1, COUNT(*) AS frequency
        FROM skills a
        GROUP BY a.skill
    """,
    2: """
        SELECT a.skill AS s1, b.skill AS s2,
               COUNT(*) AS frequency
        FROM skills a
        JOIN skills b
          ON a.vacancy_num = b.vacancy_num
         AND a.skill < b.skill
        GROUP BY a.skill, b.skill
    """,
    3: """
        SELECT a.skill AS s1, b.skill AS s2,
               c.skill AS s3,
               COUNT(*) AS frequency
        FROM skills a
        JOIN skills b
          ON a.vacancy_num = b.vacancy_num
         AND a.skill < b.skill
        JOIN skills c
          ON b.vacancy_num = c.vacancy_num
         AND b.skill < c.skill
        GROUP BY a.skill, b.skill, c.skill
    """,
}

for size, sql in queries.items():
    print(f"\nПроверка комбинаций из {size} навыков")

    rows = con.execute(base_sql + sql).fetchall()

    duckdb_counts = {
        tuple(row[:-1]): row[-1]
        for row in rows
    }

    obj = s3.get_object(
        Bucket="hh-lake",
        Key=f"results/skills_{size}.csv",
    )

    content = obj["Body"].read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    mapreduce_counts = {
        tuple(row["skills"].split("; ")): int(row["count"])
        for row in reader
    }

    print("DuckDB:", len(duckdb_counts))
    print("MapReduce:", len(mapreduce_counts))

    if duckdb_counts == mapreduce_counts:
        print("Результаты полностью совпадают!")
    else:
        print("ОШИБКА: результаты различаются!")

        differences = [
            key for key in duckdb_counts.keys() | mapreduce_counts.keys()
            if duckdb_counts.get(key) != mapreduce_counts.get(key)
        ]

        print("Количество расхождений:", len(differences))

        for key in sorted(differences)[:10]:
            print(
                key,
                "DuckDB:", duckdb_counts.get(key),
                "MapReduce:", mapreduce_counts.get(key),
            )

con.close()
