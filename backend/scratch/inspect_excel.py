import pandas as pd
from pathlib import Path

raw_dir = Path("c:/A.P.S/College/AI ML Projects/EV-Compare-App/data/raw")
files = list(raw_dir.glob("*.xlsx"))
print(f"Files found: {[f.name for f in files]}")

for f in files:
    df = pd.read_excel(f)
    print(f"\nFile: {f.name}")
    print(f"Total rows: {len(df)}")
    print(f"Columns ({len(df.columns)}): {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df.head(3).to_string())
