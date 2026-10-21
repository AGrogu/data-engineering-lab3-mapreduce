import csv
import getpass
import os
import subprocess
import time

import psutil

PROGRAMS = ["mapreduce.py", "duckdb_skills.py"]
RUNS = 3

secret = getpass.getpass("Введите секретный ключ RustFS: ")
results = []

for program in PROGRAMS:
    for run in range(1, RUNS + 1):
        print(f"\n{program}: запуск {run}/{RUNS}", flush=True)

        start = time.perf_counter()

        process = subprocess.Popen(
            [".venv/bin/python", program],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        process.stdin.write(secret + "\n")
        process.stdin.close()

        peak_memory = 0
        monitored = psutil.Process(process.pid)

        while process.poll() is None:
            try:
                peak_memory = max(
                    peak_memory,
                    monitored.memory_info().rss,
                )
            except psutil.NoSuchProcess:
                break

            time.sleep(0.01)

        stdout = process.stdout.read()
        stderr = process.stderr.read()
        process.wait()

        if process.returncode != 0:
            print(stderr)
            raise RuntimeError(f"Ошибка: {program}")

        elapsed = time.perf_counter() - start
        memory_mb = peak_memory / 1024**2

        print(f"Время: {elapsed:.3f} с")
        print(f"Пик памяти: {memory_mb:.2f} MiB")

        results.append([
            program,
            run,
            round(elapsed, 3),
            round(memory_mb, 2),
        ])

with open(
    "benchmark_results.csv",
    "w",
    newline="",
    encoding="utf-8",
) as file:
    writer = csv.writer(file)
    writer.writerow([
        "program",
        "run",
        "time_seconds",
        "peak_memory_mib",
    ])
    writer.writerows(results)

print("\nСохранено: benchmark_results.csv")
