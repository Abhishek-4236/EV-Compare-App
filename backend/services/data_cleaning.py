import re
import pandas as pd
from typing import Any

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names: lowercase, snake_case, remove symbols.
    """
    def clean_name(name: str) -> str:
        # Convert to string and handle case
        name = str(name).lower().strip()
        # Replace spaces and symbols with underscores
        name = re.sub(r'[^a-z0-9]+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        return name
    
    df.columns = [clean_name(col) for col in df.columns]
    return df

def transform_row(row: pd.Series) -> dict[str, Any]:
    """
    Handle data type conversions and basic cleanup for a single row.
    """
    data = row.to_dict()
    
    # Handle category mapping
    category_map = {
        'scooter': '2W',
        'bike': '2W',
        'motorcycle': '2W',
        'car': '4W',
        '3-wheeler': '3W',
        '3w': '3W',
        'auto': '3W',
        'bus': 'Bus',
        'truck': 'Truck'
    }
    
    current_cat = str(data.get('category', '')).lower()
    for key, val in category_map.items():
        if key in current_cat:
            data['category'] = val
            break
            
    # Basic string cleanup
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = value.strip()
            
    return data
