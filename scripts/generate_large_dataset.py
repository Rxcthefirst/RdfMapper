#!/usr/bin/env python3
"""
High-performance data generator using Polars for creating large test datasets.

Usage:
    python generate_large_dataset.py --config config.json --output loans_500k.csv
    python generate_large_dataset.py --rows 500000 --output loans_500k.csv  # Use default mortgage config
"""

import argparse
import json
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import polars as pl
import numpy as np


class DataGenerator:
    """High-performance data generator using Polars."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.num_rows = config.get('num_rows', 10000)
        self.columns = config.get('columns', [])
        self.seed = config.get('seed', 42)
        random.seed(self.seed)
        np.random.seed(self.seed)

    def generate_column(self, col_config: Dict[str, Any]) -> pl.Series:
        """Generate a single column based on configuration."""
        name = col_config['name']
        dtype = col_config['type']
        format_spec = col_config.get('format', None)

        print(f"Generating column: {name} ({dtype}, format={format_spec})")

        if dtype == 'id':
            return self._generate_id(name, format_spec)
        elif dtype == 'string':
            return self._generate_string(name, format_spec)
        elif dtype == 'integer':
            return self._generate_integer(name, col_config)
        elif dtype == 'float':
            return self._generate_float(name, col_config)
        elif dtype == 'date':
            return self._generate_date(name, format_spec)
        elif dtype == 'boolean':
            return self._generate_boolean(name)
        elif dtype == 'email':
            return self._generate_email(name)
        elif dtype == 'phone':
            return self._generate_phone(name)
        elif dtype == 'address':
            return self._generate_address(name)
        elif dtype == 'name':
            return self._generate_name(name)
        elif dtype == 'enum':
            return self._generate_enum(name, col_config.get('values', []))
        else:
            raise ValueError(f"Unknown data type: {dtype}")

    def _generate_id(self, name: str, format_spec: str) -> pl.Series:
        """Generate ID column with optional prefix."""
        prefix = format_spec or 'ID'
        ids = [f"{prefix}-{i+1:06d}" for i in range(self.num_rows)]
        return pl.Series(name, ids, dtype=pl.Utf8)

    def _generate_string(self, name: str, format_spec: str) -> pl.Series:
        """Generate random strings."""
        length = int(format_spec) if format_spec and format_spec.isdigit() else 10
        strings = [''.join(random.choices(string.ascii_letters, k=length)) for _ in range(self.num_rows)]
        return pl.Series(name, strings, dtype=pl.Utf8)

    def _generate_integer(self, name: str, config: Dict[str, Any]) -> pl.Series:
        """Generate random integers in range."""
        min_val = config.get('min', 0)
        max_val = config.get('max', 1000000)
        integers = np.random.randint(min_val, max_val + 1, size=self.num_rows)
        return pl.Series(name, integers, dtype=pl.Int64)

    def _generate_float(self, name: str, config: Dict[str, Any]) -> pl.Series:
        """Generate random floats in range."""
        min_val = config.get('min', 0.0)
        max_val = config.get('max', 1.0)
        decimals = config.get('decimals', 4)
        floats = np.round(np.random.uniform(min_val, max_val, size=self.num_rows), decimals)
        return pl.Series(name, floats, dtype=pl.Float64)

    def _generate_date(self, name: str, format_spec: str) -> pl.Series:
        """Generate random dates in range."""
        # Format: "2020-01-01:2023-12-31" or just use recent years
        if format_spec and ':' in format_spec:
            start_str, end_str = format_spec.split(':')
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_str, '%Y-%m-%d')
        else:
            start_date = datetime(2020, 1, 1)
            end_date = datetime(2023, 12, 31)

        delta = (end_date - start_date).days
        random_days = np.random.randint(0, delta + 1, size=self.num_rows)
        dates = [start_date + timedelta(days=int(d)) for d in random_days]
        date_strings = [d.strftime('%Y-%m-%d') for d in dates]
        return pl.Series(name, date_strings, dtype=pl.Utf8)

    def _generate_boolean(self, name: str) -> pl.Series:
        """Generate random booleans."""
        bools = np.random.choice([True, False], size=self.num_rows)
        return pl.Series(name, bools, dtype=pl.Boolean)

    def _generate_email(self, name: str) -> pl.Series:
        """Generate random email addresses."""
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'example.com', 'company.com']
        emails = [
            f"user{i}_{random.randint(1000, 9999)}@{random.choice(domains)}"
            for i in range(self.num_rows)
        ]
        return pl.Series(name, emails, dtype=pl.Utf8)

    def _generate_phone(self, name: str) -> pl.Series:
        """Generate random phone numbers."""
        phones = [
            f"{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
            for _ in range(self.num_rows)
        ]
        return pl.Series(name, phones, dtype=pl.Utf8)

    def _generate_address(self, name: str) -> pl.Series:
        """Generate random addresses."""
        street_names = ['Oak', 'Pine', 'Maple', 'Elm', 'Cedar', 'Birch', 'Willow', 'Ash']
        street_types = ['St', 'Ave', 'Dr', 'Ln', 'Ct', 'Rd', 'Blvd', 'Way']
        addresses = [
            f"{random.randint(1, 9999)} {random.choice(street_names)} {random.choice(street_types)}"
            for _ in range(self.num_rows)
        ]
        return pl.Series(name, addresses, dtype=pl.Utf8)

    def _generate_name(self, name: str) -> pl.Series:
        """Generate random person names."""
        first_names = ['Alex', 'Jamie', 'Taylor', 'Jordan', 'Casey', 'Morgan', 'Riley', 'Avery',
                       'Quinn', 'Dakota', 'Sage', 'River', 'Phoenix', 'Skyler', 'Cameron']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                      'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson']
        names = [
            f"{random.choice(first_names)} {random.choice(last_names)}"
            for _ in range(self.num_rows)
        ]
        return pl.Series(name, names, dtype=pl.Utf8)

    def _generate_enum(self, name: str, values: List[str]) -> pl.Series:
        """Generate random values from a list."""
        if not values:
            values = ['Option1', 'Option2', 'Option3']
        random_values = [random.choice(values) for _ in range(self.num_rows)]
        return pl.Series(name, random_values, dtype=pl.Utf8)

    def generate(self) -> pl.DataFrame:
        """Generate the complete dataset."""
        print(f"Generating {self.num_rows:,} rows with {len(self.columns)} columns...")
        start_time = datetime.now()

        # Generate all columns
        series_list = []
        for col_config in self.columns:
            series = self.generate_column(col_config)
            series_list.append(series)

        # Create DataFrame
        df = pl.DataFrame(series_list)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Generated {len(df):,} rows in {elapsed:.2f} seconds")
        print(f"Speed: {len(df) / elapsed:,.0f} rows/second")

        return df


def get_mortgage_config(num_rows: int = 500000) -> Dict[str, Any]:
    """Get default mortgage loan configuration."""
    return {
        "num_rows": num_rows,
        "seed": 42,
        "columns": [
            {"name": "LoanID", "type": "id", "format": "L"},
            {"name": "BorrowerID", "type": "id", "format": "B"},
            {"name": "BorrowerName", "type": "name"},
            {"name": "PropertyID", "type": "id", "format": "P"},
            {"name": "PropertyAddress", "type": "address"},
            {"name": "Principal", "type": "integer", "min": 100000, "max": 1000000},
            {"name": "InterestRate", "type": "float", "min": 0.03, "max": 0.08, "decimals": 4},
            {"name": "OriginationDate", "type": "date", "format": "2020-01-01:2023-12-31"},
            {"name": "LoanTerm", "type": "enum", "values": ["180", "240", "300", "360"]},
            {"name": "Status", "type": "enum", "values": ["Active", "Paid Off", "Delinquent", "Foreclosed"]}
        ]
    }


def main():
    parser = argparse.ArgumentParser(
        description='Generate large CSV datasets for performance testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate 500k rows with default mortgage config
  python generate_large_dataset.py --rows 500000 --output loans_500k.csv
  
  # Use custom config file
  python generate_large_dataset.py --config my_config.json --output data.csv
  
  # Generate and print sample
  python generate_large_dataset.py --rows 1000 --output sample.csv --sample 10
        '''
    )
    parser.add_argument('--config', type=str, help='Path to JSON configuration file')
    parser.add_argument('--rows', type=int, help='Number of rows to generate (overrides config)')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file path')
    parser.add_argument('--sample', type=int, default=5, help='Number of sample rows to display')
    parser.add_argument('--save-config', type=str, help='Save the used configuration to a file')

    args = parser.parse_args()

    # Load or create configuration
    if args.config:
        print(f"Loading configuration from {args.config}")
        with open(args.config, 'r') as f:
            config = json.load(f)
        if args.rows:
            config['num_rows'] = args.rows
    else:
        print("Using default mortgage loan configuration")
        config = get_mortgage_config(args.rows or 500000)

    # Save config if requested
    if args.save_config:
        config_path = Path(args.save_config)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {config_path}")

    # Generate data
    generator = DataGenerator(config)
    df = generator.generate()

    # Display sample
    print(f"\nFirst {args.sample} rows:")
    print(df.head(args.sample))

    # Write to CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nWriting to {output_path}...")
    start_time = datetime.now()
    df.write_csv(output_path)
    elapsed = (datetime.now() - start_time).total_seconds()

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✅ Saved {len(df):,} rows to {output_path}")
    print(f"   File size: {file_size_mb:.2f} MB")
    print(f"   Write time: {elapsed:.2f} seconds ({file_size_mb / elapsed:.2f} MB/s)")


if __name__ == '__main__':
    main()

