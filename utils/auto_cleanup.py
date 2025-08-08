# utils/auto_cleanup.py
import os
import time
import logging

# Limit przestrzeni w bajtach (np. 10GB)
DISK_SPACE_LIMIT = 10 * 1024**3  # 10 GB

# Katalogi do czyszczenia (dodaj tu kolejne foldery, które mogą się rozrastać)
CLEAN_PATHS = [
    "logs",
    "tmp",
    "cache",
    "data/temp",
    "data/history/temp",
    "sensors/temp",
    "engines/temp",
    "core/temp"
]

# Typowe rozszerzenia plików do czyszczenia w pierwszej kolejności
PRIORITY_EXT = ['.log', '.tmp', '.bak', '.cache', '.dat']

def get_folder_size(path='.'):
    """Oblicz rozmiar folderu (rekurencyjnie)"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except Exception:
                pass
    return total

def collect_files(paths, priority_ext=PRIORITY_EXT):
    """Zbierz pliki do potencjalnego usunięcia – najpierw te z określonymi rozszerzeniami, posortowane po dacie modyfikacji (najstarsze pierwsze)"""
    files = []
    for path in paths:
        if not os.path.exists(path):
            continue
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    ext = os.path.splitext(f)[1].lower()
                    mtime = os.path.getmtime(fp)
                    size = os.path.getsize(fp)
                    priority = 0 if ext in priority_ext else 1
                    files.append((priority, mtime, fp, size))
                except Exception:
                    continue
    # Sortuj: najpierw priorytetowe, najstarsze
    files.sort()
    return files

def auto_cleanup(max_size=DISK_SPACE_LIMIT, clean_paths=CLEAN_PATHS, verbose=False):
    """Automatyczne czyszczenie plików przy przekroczeniu limitu przestrzeni"""
    project_size = get_folder_size('.')
    if verbose:
        print(f"[AutoCleanup] Project size: {project_size/1024**3:.2f} GB (limit: {max_size/1024**3} GB)")

    if project_size <= max_size:
        if verbose:
            print("[AutoCleanup] No cleanup needed.")
        return

    files = collect_files(clean_paths)
    deleted = 0
    freed = 0

    for priority, mtime, fp, size in files:
        if project_size - freed <= max_size:
            break
        try:
            os.remove(fp)
            freed += size
            deleted += 1
            if verbose:
                print(f"[AutoCleanup] Deleted: {fp} ({size/1024**2:.2f} MB)")
        except Exception as e:
            if verbose:
                print(f"[AutoCleanup] Failed to delete {fp}: {e}")

    # Po usunięciu plików spróbuj usunąć puste katalogi
    for path in clean_paths:
        for dirpath, dirnames, filenames in os.walk(path, topdown=False):
            try:
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    if verbose:
                        print(f"[AutoCleanup] Removed empty dir: {dirpath}")
            except Exception:
                continue

    if verbose:
        print(f"[AutoCleanup] Freed space: {freed/1024**2:.2f} MB. Files deleted: {deleted}")

def run_auto_cleanup_loop(interval=3600, verbose=True):
    """Agent cykliczny: sprawdza co określony czas (domyślnie co godzinę)"""
    print(f"[AutoCleanup] Starting autonomous cleanup agent. Interval: {interval}s")
    while True:
        auto_cleanup(verbose=verbose)
        time.sleep(interval)

if __name__ == "__main__":
    # Jednorazowe czyszczenie, lub uruchomienie w trybie agenta (pętla nieskończona)
    import argparse
    parser = argparse.ArgumentParser(description="GIE 2.0 Auto Cleanup Tool")
    parser.add_argument('--loop', action='store_true', help='Run in infinite loop (as background agent)')
    parser.add_argument('--interval', type=int, default=3600, help='Interval for loop mode (seconds)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    if args.loop:
        run_auto_cleanup_loop(interval=args.interval, verbose=args.verbose)
    else:
        auto_cleanup(verbose=args.verbose)
