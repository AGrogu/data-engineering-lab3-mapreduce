import mapreduce

original_map = mapreduce.map_chunk
calls = 0


def failing_map(chunk):
    global calls
    calls += 1

    if calls == 3:
        raise RuntimeError("Тестовый отказ маппера")

    return original_map(chunk)


mapreduce.map_chunk = failing_map

try:
    mapreduce.main()
except RuntimeError as error:
    print("Обнаружена ошибка:", error)
    print("Обработано чанков до отказа:", calls - 1)
    print("Неполные результаты не сохранены")
else:
    print("ОШИБКА: отказ маппера не обнаружен")
