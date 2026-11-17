import argparse
import sys
import time
import urllib.error
import urllib.request

CHUNK_SIZE = 64 * 1024
USER_AGENT = "Mozilla/5.0 (speedtest-cli-script)"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Measure download speed by fetching a URL several times in a row."
    )
    parser.add_argument("url", help="address to download, e.g. a large image")
    parser.add_argument("-n", "--count", type=int, default=10, help="number of requests (default: 10)")
    parser.add_argument("-t", "--timeout", type=float, default=30, help="timeout per request in seconds (default: 30)")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be at least 1")
    if not args.url.startswith(("http://", "https://")):
        args.url = "https://" + args.url
    return args


def download(url, timeout):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"},
    )
    start = time.perf_counter()
    received = 0
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            received += len(chunk)
    elapsed = time.perf_counter() - start
    return received, elapsed


def format_megabytes(num_bytes):
    return f"{num_bytes / 1_000_000:.2f} MB"


def main():
    args = parse_args()
    print(f"URL: {args.url}")
    print(f"Requests: {args.count}\n")

    sizes = []
    durations = []
    failures = 0

    for i in range(1, args.count + 1):
        try:
            size, duration = download(args.url, args.timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            failures += 1
            print(f"[{i:>2}/{args.count}] error: {error}")
            continue
        sizes.append(size)
        durations.append(duration)
        print(f"[{i:>2}/{args.count}] {format_megabytes(size):>10}  {duration:7.3f} s")

    if not durations:
        print("\nAll requests failed, nothing to measure.")
        return 1

    total_bytes = sum(sizes)
    total_time = sum(durations)
    average_time = total_time / len(durations)
    speed_mbit = total_bytes * 8 / total_time / 1_000_000
    speed_mbyte = total_bytes / total_time / 1_000_000

    print("\nResults")
    print(f"  Successful requests: {len(durations)}/{args.count}")
    print(f"  Average request time: {average_time:.3f} s")
    print(f"  Total downloaded:     {format_megabytes(total_bytes)}")
    print(f"  Download speed:       {speed_mbit:.2f} Mbit/s ({speed_mbyte:.2f} MB/s)")

    return 0 if failures == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
