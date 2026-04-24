import os
import time
import sys
from pathlib import Path

# Add the parent backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.import_excel import run_import

RAW_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"

def get_latest_mtime() -> float:
    """Returns the latest modification time of any .xlsx file in the raw data directory"""
    latest_time = 0.0
    if not RAW_DATA_DIR.exists():
        return latest_time
    
    for file_path in RAW_DATA_DIR.glob("*.xlsx"):
        # Ignore temporary excel files like ~$filename.xlsx
        if file_path.name.startswith("~"):
            continue
        try:
            mtime = os.path.getmtime(file_path)
            if mtime > latest_time:
                latest_time = mtime
        except Exception:
            pass
    return latest_time

def main():
    print(f"Starting data watcher on {RAW_DATA_DIR}...")
    
    # Store initial modification time
    last_mtime = get_latest_mtime()
    
    try:
        while True:
            time.sleep(2)  # Check every 2 seconds
            
            current_mtime = get_latest_mtime()
            if current_mtime > last_mtime:
                print(f"\n[WATCHER] Detected changes in Excel data. Re-running import...")
                
                # Small delay to ensure the file finishes saving before we read it
                time.sleep(1)
                
                try:
                    run_import()
                    print(f"[WATCHER] Import completed successfully. Database and embeddings synced at {time.strftime('%X')}.")
                    last_mtime = get_latest_mtime()
                except Exception as e:
                    print(f"[WATCHER] Error during import: {e}")
                    # Update mtime anyway so we don't infinitely retry a broken file
                    last_mtime = current_mtime
                    
    except KeyboardInterrupt:
        print("\nStopping data watcher.")

if __name__ == "__main__":
    main()
