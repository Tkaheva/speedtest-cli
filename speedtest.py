


import argparse
import sys
import time
import urllib.request
import urllib.error

# Сколько запросов делаем по условию задачи
REQUEST_COUNT = 10
# Таймаут на один запрос, чтобы не висеть вечно на «тяжёлом» адресе
TIMEOUT_SEC = 60
# Размер чанка при чтении тела ответа
CHUNK_SIZE = 64 * 1024  # 64 КБ
# Пауза между запросами в секундах, чтобы не получить бан от сервера
SLEEP_BETWEEN_REQUESTS = 1.0


def download_once(url: str) -> int:
    """
    Делает один GET-запрос, полностью вычитывает тело ответа
    и возвращает количество полученных байт.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "speedtest-cli/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as response:
        total = 0
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
        return total


def run_benchmark(url: str) -> None:
    print(f"URL: {url}")
    print(f"Запросов: {REQUEST_COUNT}, таймаут на запрос: {TIMEOUT_SEC} с")
    print("-" * 60)

    total_bytes = 0
    total_time = 0.0
    successful_requests = 0  # Считаем только успешные запросы

    for i in range(1, REQUEST_COUNT + 1):
        start = time.perf_counter()
        try:
            size = download_once(url)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"[{i:2}/{REQUEST_COUNT}] Ошибка 429: Сервер блокирует частые запросы. Пропускаем...", file=sys.stderr)
            else:
                print(f"[{i:2}/{REQUEST_COUNT}] HTTP Ошибка {e.code}: {e.reason}", file=sys.stderr)
            time.sleep(SLEEP_BETWEEN_REQUESTS + 0.5) # Чуть большая пауза при ошибке
            continue # Переходим к следующему запросу
        except urllib.error.URLError as e:
            print(f"[{i:2}/{REQUEST_COUNT}] Ошибка сети: {e.reason}", file=sys.stderr)
            time.sleep(SLEEP_BETWEEN_REQUESTS + 0.5)
            continue
        except Exception as e:
            print(f"[{i:2}/{REQUEST_COUNT}] Неизвестная ошибка: {e}", file=sys.stderr)
            time.sleep(SLEEP_BETWEEN_REQUESTS + 0.5)
            continue

        elapsed = time.perf_counter() - start

        total_bytes += size
        total_time += elapsed
        successful_requests += 1

        speed_mb_s = (size / (1024 * 1024)) / elapsed if elapsed > 0 else 0
        print(
            f"[{i:2}/{REQUEST_COUNT}] "
            f"{size / 1024:.1f} КБ за {elapsed:.3f} с  →  {speed_mb_s:.2f} МБ/с"
        )
        
        # ДЕЛАЕМ ПАУЗУ, чтобы не злить сервер
        if i < REQUEST_COUNT:
            time.sleep(SLEEP_BETWEEN_REQUESTS)

    print("-" * 60)
    
    if successful_requests == 0:
        print("Итоги: Не удалось выполнить ни одного успешного запроса.")
        return

    avg_time = total_time / successful_requests
    avg_bytes = total_bytes / successful_requests
    # Скорость считаем по суммарным значениям — это устойчивее к выбросам
    avg_speed_mb_s = (total_bytes / (1024 * 1024)) / total_time if total_time > 0 else 0
    avg_speed_mbit_s = avg_speed_mb_s * 8

    print(f"Итоги (успешных запросов: {successful_requests}/{REQUEST_COUNT}):")
    print(f"  Среднее время запроса:   {avg_time:.3f} с")
    print(f"  Средний размер ответа:   {avg_bytes / 1024:.1f} КБ")
    print(f"  Всего скачано:           {total_bytes / (1024 * 1024):.2f} МБ")
    print(f"  Средняя скорость:        {avg_speed_mb_s:.2f} МБ/с  ({avg_speed_mbit_s:.2f} Мбит/с)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Замер скорости скачивания по 10 последовательным запросам."
    )
    parser.add_argument("url", help="Адрес ресурса (например, ссылка на тяжёлую картинку)")
    args = parser.parse_args()

    run_benchmark(args.url)


if __name__ == "__main__":
    main()
