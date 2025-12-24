"""Internet Speed Tester & Worker Optimizer

Tests your internet connection and recommends optimal worker count
for the Snapchat Memories downloader.

Author: Anton Johannesson
"""

import urllib.request
import time
import statistics

# Test files from reliable CDNs (various sizes)
TEST_URLS = [
    ("1MB", "http://speedtest.tele2.net/1MB.zip"),
    ("10MB", "http://speedtest.tele2.net/10MB.zip"),
]

# Fallback test URLs if primary fails
FALLBACK_URLS = [
    ("1MB", "http://ipv4.download.thinkbroadband.com/1MB.zip"),
    ("5MB", "http://ipv4.download.thinkbroadband.com/5MB.zip"),
]


def test_latency(url, attempts=3):
    """Test connection latency (time to first byte)."""
    latencies = []
    for _ in range(attempts):
        try:
            start = time.time()
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=10) as resp:
                latency = (time.time() - start) * 1000  # ms
                latencies.append(latency)
        except:
            continue
    return statistics.mean(latencies) if latencies else None


def test_download_speed(url, label):
    """Download a test file and measure speed in Mbps."""
    try:
        print(f"  Downloading {label} test file...", end=" ", flush=True)
        start = time.time()
        
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
        
        elapsed = time.time() - start
        size_bytes = len(data)
        size_mb = size_bytes / (1024 * 1024)
        speed_mbps = (size_bytes * 8) / (elapsed * 1_000_000)
        
        print(f"✓ {size_mb:.1f} MB in {elapsed:.1f}s = {speed_mbps:.1f} Mbps")
        return speed_mbps
    except Exception as e:
        print(f"✗ Failed: {e}")
        return None


def recommend_workers(speed_mbps, latency_ms):
    """Recommend optimal worker count based on speed and latency."""
    if speed_mbps is None:
        return 8, "Could not test speed, using safe default"
    
    # Base recommendation on speed
    if speed_mbps < 10:
        workers = 4
        reason = "Slow connection - fewer workers prevent congestion"
    elif speed_mbps < 25:
        workers = 8
        reason = "Moderate connection - balanced worker count"
    elif speed_mbps < 50:
        workers = 12
        reason = "Good connection - can handle more parallel downloads"
    elif speed_mbps < 100:
        workers = 16
        reason = "Fast connection - optimal parallel throughput"
    elif speed_mbps < 200:
        workers = 24
        reason = "Very fast connection - high parallelism"
    else:
        workers = 32
        reason = "Excellent connection - maximum recommended"
    
    # Adjust for high latency (slower connections benefit less from many workers)
    if latency_ms and latency_ms > 200:
        workers = max(4, workers - 4)
        reason += " (reduced due to high latency)"
    
    # Cap at 32 to avoid server rate limits
    workers = min(32, workers)
    
    return workers, reason


def update_parallel_script(workers):
    """Update MAX_WORKERS in import_json_parallel.py"""
    import os
    script_path = os.path.join(os.path.dirname(__file__), "import_json_parallel.py")
    
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find and replace MAX_WORKERS line
        import re
        new_content = re.sub(
            r"MAX_WORKERS\s*=\s*\d+",
            f"MAX_WORKERS = {workers}",
            content
        )
        
        if new_content != content:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
        return False
    except Exception as e:
        print(f"Could not update script: {e}")
        return False


def main():
    print("=" * 60)
    print("  Internet Speed Test & Worker Optimizer")
    print("=" * 60)
    print()
    
    # Test latency first
    print("Testing latency...")
    latency = test_latency(TEST_URLS[0][1])
    if latency:
        print(f"  Latency: {latency:.0f} ms")
    else:
        print("  Could not measure latency")
    print()
    
    # Test download speed
    print("Testing download speed...")
    speeds = []
    
    # Try primary URLs
    for label, url in TEST_URLS:
        speed = test_download_speed(url, label)
        if speed:
            speeds.append(speed)
        if len(speeds) >= 2:
            break
    
    # Fallback if needed
    if not speeds:
        print("  Trying fallback servers...")
        for label, url in FALLBACK_URLS:
            speed = test_download_speed(url, label)
            if speed:
                speeds.append(speed)
            if speeds:
                break
    
    print()
    
    # Calculate average speed
    avg_speed = statistics.mean(speeds) if speeds else None
    
    # Get recommendation
    workers, reason = recommend_workers(avg_speed, latency)
    
    # Display results
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    if avg_speed:
        print(f"  Average Speed:    {avg_speed:.1f} Mbps")
    if latency:
        print(f"  Latency:          {latency:.0f} ms")
    print()
    print(f"  Recommended Workers: {workers}")
    print(f"  Reason: {reason}")
    print()
    
    # Ask to update
    response = input(f"Update import_json_parallel.py to use {workers} workers? [y/N]: ").strip().lower()
    if response == 'y':
        if update_parallel_script(workers):
            print(f"✓ Updated MAX_WORKERS to {workers}")
        else:
            print("  No changes made (already set or file not found)")
    else:
        print(f"  To set manually: MAX_WORKERS = {workers}")
    
    print()
    print("Done!")


if __name__ == "__main__":
    main()
