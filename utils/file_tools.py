import pandas as pd
from pathlib import Path

def sum_column(csv_path: str, column: str) -> float:
    """
    Sum the numeric values of a column in a CSV file.

    Args:
        csv_path (str): Path to the CSV file.
        column (str): Name of the column to sum.

    Returns:
        float: Sum of the column values.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the column is missing or contains no numeric values.
    """
    csv_file = Path(csv_path)
    if not csv_file.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    try:
        df = pd.read_csv(csv_file, encoding='utf-8', errors='ignore')
    except Exception as e:
        raise ValueError(f"Failed to read CSV {csv_path}: {e}")

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in {csv_path}")

    # Convert column to numeric, coercing errors to NaN
    numeric_values = pd.to_numeric(df[column], errors='coerce')

    if numeric_values.isna().all():
        raise ValueError(f"Column '{column}' contains no numeric values in {csv_path}")

    return numeric_values.sum()
