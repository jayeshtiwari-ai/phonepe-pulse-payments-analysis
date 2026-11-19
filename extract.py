"""
extract.py - PhonePe Pulse Data Extractor
Extracts raw JSON files from the PhonePe Pulse repository into clean, structured DataFrames.
"""

import os
import glob
import json
import re
import time
from typing import Dict, Tuple
import pandas as pd


def format_state(name: str) -> str:
    """Standardise state names to proper case, handling hyphens and ampersands."""
    if not name:
        return name
    name = name.strip().lower()
    name = name.replace('-&-', ' & ').replace('-', ' ')
    parts = name.split()
    return ' '.join(['&' if p == '&' else p.capitalize() for p in parts])


def clean_district(name: str) -> str:
    """Standardise district names: strip trailing ' district', clean hyphens, proper case."""
    if name is None or str(name).strip().lower() in ['none', 'nan', '']:
        return 'Unknown'
    name = str(name).strip()
    name = re.sub(r'\s+district$', '', name, flags=re.IGNORECASE)
    name = name.replace('-', ' ')
    return ' '.join(p.capitalize() for p in name.split())


def clean_entity_name(name: str) -> str:
    """Standardise entity names (pincodes/districts), imputing 'Unknown' for nulls/empty."""
    if name is None or str(name).strip().lower() in ['none', 'nan', '']:
        return 'Unknown'
    return str(name).strip()


def extract_agg_transaction(data_root: str) -> pd.DataFrame:
    """Extract aggregated transaction data."""
    pattern = os.path.join(data_root, 'aggregated', 'transaction', 'country', 'india', 'state', '*', '*', '*.json')
    rows = []
    for file_path in glob.glob(pattern):
        parts = os.path.normpath(file_path).split(os.sep)
        state = format_state(parts[-3])
        year = int(parts[-2])
        quarter = int(parts[-1].replace('.json', ''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception as e:
            continue
            
        data = content.get('data', {}) or {}
        for item in data.get('transactionData') or []:
            category = item.get('name')
            for instr in item.get('paymentInstruments', []):
                count = instr.get('count')
                amount = instr.get('amount')
                rows.append((state, year, quarter, category, count, amount))
                
    df = pd.DataFrame(rows, columns=['state', 'year', 'quarter', 'category', 'count', 'amount'])
    df = df.drop_duplicates(subset=['state', 'year', 'quarter', 'category'])
    return df


def extract_agg_user(data_root: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract aggregated user and user device data.
    Splits into:
      1. agg_user: state, year, quarter, registered_users, app_opens
      2. agg_user_device: state, year, quarter, brand, count, percentage
    """
    pattern = os.path.join(data_root, 'aggregated', 'user', 'country', 'india', 'state', '*', '*', '*.json')
    user_rows = []
    device_rows = []
    
    for file_path in glob.glob(pattern):
        parts = os.path.normpath(file_path).split(os.sep)
        state = format_state(parts[-3])
        year = int(parts[-2])
        quarter = int(parts[-1].replace('.json', ''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception:
            continue
            
        data = content.get('data', {}) or {}
        agg = data.get('aggregated') or {}
        reg_users = agg.get('registeredUsers')
        app_opens = agg.get('appOpens')
        user_rows.append((state, year, quarter, reg_users, app_opens))
        
        devices = data.get('usersByDevice')
        if devices:
            for dev in devices:
                brand = dev.get('brand')
                count = dev.get('count')
                percentage = dev.get('percentage')
                device_rows.append((state, year, quarter, brand, count, percentage))
                
    df_user = pd.DataFrame(user_rows, columns=['state', 'year', 'quarter', 'registered_users', 'app_opens'])
    df_user = df_user.drop_duplicates(subset=['state', 'year', 'quarter'])
    
    df_device = pd.DataFrame(device_rows, columns=['state', 'year', 'quarter', 'brand', 'count', 'percentage'])
    df_device = df_device.drop_duplicates(subset=['state', 'year', 'quarter', 'brand'])
    
    return df_user, df_device


def extract_agg_insurance(data_root: str) -> pd.DataFrame:
    """Extract aggregated insurance data."""
    pattern = os.path.join(data_root, 'aggregated', 'insurance', 'country', 'india', 'state', '*', '*', '*.json')
    rows = []
    for file_path in glob.glob(pattern):
        parts = os.path.normpath(file_path).split(os.sep)
        state = format_state(parts[-3])
        year = int(parts[-2])
        quarter = int(parts[-1].replace('.json', ''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception:
            continue
            
        data = content.get('data', {}) or {}
        for item in data.get('transactionData') or []:
            category = item.get('name')
            for instr in item.get('paymentInstruments', []):
                count = instr.get('count')
                amount = instr.get('amount')
                rows.append((state, year, quarter, category, count, amount))
                
    df = pd.DataFrame(rows, columns=['state', 'year', 'quarter', 'category', 'count', 'amount'])
    df = df.drop_duplicates(subset=['state', 'year', 'quarter', 'category'])
    return df


def extract_map_transaction(data_root: str) -> pd.DataFrame:
    """Extract map transaction data at district level."""
    pattern = os.path.join(data_root, 'map', 'transaction', 'hover', 'country', 'india', 'state', '*', '*', '*.json')
    rows = []
    for file_path in glob.glob(pattern):
        parts = os.path.normpath(file_path).split(os.sep)
        state = format_state(parts[-3])
        year = int(parts[-2])
        quarter = int(parts[-1].replace('.json', ''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception:
            continue
            
        data = content.get('data', {}) or {}
        for item in data.get('hoverDataList') or []:
            district = clean_district(item.get('name'))
            for metric in item.get('metric', []):
                count = metric.get('count')
                amount = metric.get('amount')
                rows.append((state, district, year, quarter, count, amount))
                
    df = pd.DataFrame(rows, columns=['state', 'district', 'year', 'quarter', 'count', 'amount'])
    df = df.drop_duplicates(subset=['state', 'district', 'year', 'quarter'])
    return df


def extract_map_user(data_root: str) -> pd.DataFrame:
    """Extract map user data at district level."""
    pattern = os.path.join(data_root, 'map', 'user', 'hover', 'country', 'india', 'state', '*', '*', '*.json')
    rows = []
    for file_path in glob.glob(pattern):
        parts = os.path.normpath(file_path).split(os.sep)
        state = format_state(parts[-3])
        year = int(parts[-2])
        quarter = int(parts[-1].replace('.json', ''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception:
            continue
            
        data = content.get('data', {}) or {}
        hover = data.get('hoverData') or {}
        for dist_raw, vals in hover.items():
            district = clean_district(dist_raw)
            reg_users = vals.get('registeredUsers')
            app_opens = vals.get('appOpens')
            rows.append((state, district, year, quarter, reg_users, app_opens))
            
    df = pd.DataFrame(rows, columns=['state', 'district', 'year', 'quarter', 'registered_users', 'app_opens'])
    df = df.drop_duplicates(subset=['state', 'district', 'year', 'quarter'])
    return df


def extract_map_insurance(data_root: str) -> pd.DataFrame:
    """Extract map insurance data at district level."""
    pattern = os.path.join(data_root, 'map', 'insurance', 'hover', 'country', 'india', 'state', '*', '*', '*.json')
    rows = []
    for file_path in glob.glob(pattern):
        parts = os.path.normpath(file_path).split(os.sep)
        state = format_state(parts[-3])
        year = int(parts[-2])
        quarter = int(parts[-1].replace('.json', ''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception:
            continue
            
        data = content.get('data', {}) or {}
        for item in data.get('hoverDataList') or []:
            district = clean_district(item.get('name'))
            for metric in item.get('metric', []):
                count = metric.get('count')
                amount = metric.get('amount')
                rows.append((state, district, year, quarter, count, amount))
                
    df = pd.DataFrame(rows, columns=['state', 'district', 'year', 'quarter', 'count', 'amount'])
    df = df.drop_duplicates(subset=['state', 'district', 'year', 'quarter'])
    return df


def extract_top_transaction(data_root: str) -> pd.DataFrame:
    """
    Extract top transaction rankings.
    Includes level ('country' / 'state') and entity_type ('state', 'district', 'pincode').
    """
    pattern = os.path.join(data_root, 'top', 'transaction', '**', '[0-9].json')
    rows = []
    for file_path in glob.glob(pattern, recursive=True):
        parts = os.path.normpath(file_path).split(os.sep)
        year = int(parts[-2])
        quarter = int(parts[-1].replace('.json', ''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception:
            continue
            
        data = content.get('data', {}) or {}
        
        if 'state' in parts:
            level = 'state'
            state_idx = parts.index('state') + 1
            state = format_state(parts[state_idx])
        else:
            level = 'country'
            state = 'India'
            for item in data.get('states') or []:
                name = format_state(item.get('entityName'))
                m = item.get('metric') or {}
                rows.append((level, state, 'state', name, year, quarter, m.get('count'), m.get('amount')))
                
        for item in data.get('districts') or []:
            name = clean_district(item.get('entityName'))
            m = item.get('metric') or {}
            rows.append((level, state, 'district', name, year, quarter, m.get('count'), m.get('amount')))
            
        for item in data.get('pincodes') or []:
            name = clean_entity_name(item.get('entityName'))
            m = item.get('metric') or {}
            rows.append((level, state, 'pincode', name, year, quarter, m.get('count'), m.get('amount')))
            
    df = pd.DataFrame(rows, columns=['level', 'state', 'entity_type', 'entity_name', 'year', 'quarter', 'count', 'amount'])
    df = df.drop_duplicates(subset=['level', 'state', 'entity_type', 'entity_name', 'year', 'quarter'])
    return df


def extract_top_user(data_root: str) -> pd.DataFrame:
    """
    Extract top user rankings.
    Includes level ('country' / 'state') and entity_type ('state', 'district', 'pincode').
    """
    pattern = os.path.join(data_root, 'top', 'user', '**', '[0-9].json')
    rows = []
    for file_path in glob.glob(pattern, recursive=True):
        parts = os.path.normpath(file_path).split(os.sep)
        year = int(parts[-2])
        quarter = int(parts[-1].replace('.json', ''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception:
            continue
            
        data = content.get('data', {}) or {}
        
        if 'state' in parts:
            level = 'state'
            state_idx = parts.index('state') + 1
            state = format_state(parts[state_idx])
        else:
            level = 'country'
            state = 'India'
            for item in data.get('states') or []:
                name = format_state(item.get('name'))
                rows.append((level, state, 'state', name, year, quarter, item.get('registeredUsers')))
                
        for item in data.get('districts') or []:
            name = clean_district(item.get('name'))
            rows.append((level, state, 'district', name, year, quarter, item.get('registeredUsers')))
            
        for item in data.get('pincodes') or []:
            name = clean_entity_name(item.get('name'))
            rows.append((level, state, 'pincode', name, year, quarter, item.get('registeredUsers')))
            
    df = pd.DataFrame(rows, columns=['level', 'state', 'entity_type', 'entity_name', 'year', 'quarter', 'registered_users'])
    df = df.drop_duplicates(subset=['level', 'state', 'entity_type', 'entity_name', 'year', 'quarter'])
    return df


def extract_top_insurance(data_root: str) -> pd.DataFrame:
    """Extract top insurance rankings."""
    pattern = os.path.join(data_root, 'top', 'insurance', '**', '[0-9].json')
    rows = []
    for file_path in glob.glob(pattern, recursive=True):
        parts = os.path.normpath(file_path).split(os.sep)
        year = int(parts[-2])
        quarter = int(parts[-1].replace('.json', ''))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception:
            continue
            
        data = content.get('data', {}) or {}
        
        if 'state' in parts:
            level = 'state'
            state_idx = parts.index('state') + 1
            state = format_state(parts[state_idx])
        else:
            level = 'country'
            state = 'India'
            for item in data.get('states') or []:
                name = format_state(item.get('entityName'))
                m = item.get('metric') or {}
                rows.append((level, state, 'state', name, year, quarter, m.get('count'), m.get('amount')))
                
        for item in data.get('districts') or []:
            name = clean_district(item.get('entityName'))
            m = item.get('metric') or {}
            rows.append((level, state, 'district', name, year, quarter, m.get('count'), m.get('amount')))
            
        for item in data.get('pincodes') or []:
            name = clean_entity_name(item.get('entityName'))
            m = item.get('metric') or {}
            rows.append((level, state, 'pincode', name, year, quarter, m.get('count'), m.get('amount')))
            
    df = pd.DataFrame(rows, columns=['level', 'state', 'entity_type', 'entity_name', 'year', 'quarter', 'count', 'amount'])
    df = df.drop_duplicates(subset=['level', 'state', 'entity_type', 'entity_name', 'year', 'quarter'])
    return df


def extract_all(data_root: str = "pulse/data") -> Dict[str, pd.DataFrame]:
    """Run all extractors and return dictionary of DataFrames."""
    print("=" * 60)
    print("Starting PhonePe Pulse Data Extraction...")
    print("=" * 60)
    start_total = time.time()
    
    tables = {}
    
    # 1. Aggregated Transaction
    t0 = time.time()
    print("Extracting agg_transaction...")
    tables['agg_transaction'] = extract_agg_transaction(data_root)
    print(f" -> agg_transaction extracted: {len(tables['agg_transaction'])} rows ({time.time()-t0:.2f}s)")
    
    # 2. Aggregated User & Device
    t0 = time.time()
    print("Extracting agg_user and agg_user_device...")
    df_u, df_dev = extract_agg_user(data_root)
    tables['agg_user'] = df_u
    tables['agg_user_device'] = df_dev
    print(f" -> agg_user extracted: {len(df_u)} rows")
    print(f" -> agg_user_device extracted: {len(df_dev)} rows ({time.time()-t0:.2f}s)")
    
    # 3. Aggregated Insurance
    t0 = time.time()
    print("Extracting agg_insurance...")
    tables['agg_insurance'] = extract_agg_insurance(data_root)
    print(f" -> agg_insurance extracted: {len(tables['agg_insurance'])} rows ({time.time()-t0:.2f}s)")
    
    # 4. Map Transaction
    t0 = time.time()
    print("Extracting map_transaction...")
    tables['map_transaction'] = extract_map_transaction(data_root)
    print(f" -> map_transaction extracted: {len(tables['map_transaction'])} rows ({time.time()-t0:.2f}s)")
    
    # 5. Map User
    t0 = time.time()
    print("Extracting map_user...")
    tables['map_user'] = extract_map_user(data_root)
    print(f" -> map_user extracted: {len(tables['map_user'])} rows ({time.time()-t0:.2f}s)")
    
    # 6. Map Insurance
    t0 = time.time()
    print("Extracting map_insurance...")
    tables['map_insurance'] = extract_map_insurance(data_root)
    print(f" -> map_insurance extracted: {len(tables['map_insurance'])} rows ({time.time()-t0:.2f}s)")
    
    # 7. Top Transaction
    t0 = time.time()
    print("Extracting top_transaction...")
    tables['top_transaction'] = extract_top_transaction(data_root)
    print(f" -> top_transaction extracted: {len(tables['top_transaction'])} rows ({time.time()-t0:.2f}s)")
    
    # 8. Top User
    t0 = time.time()
    print("Extracting top_user...")
    tables['top_user'] = extract_top_user(data_root)
    print(f" -> top_user extracted: {len(tables['top_user'])} rows ({time.time()-t0:.2f}s)")
    
    # 9. Top Insurance
    t0 = time.time()
    print("Extracting top_insurance...")
    tables['top_insurance'] = extract_top_insurance(data_root)
    print(f" -> top_insurance extracted: {len(tables['top_insurance'])} rows ({time.time()-t0:.2f}s)")
    
    print("-" * 60)
    print(f"Extraction completed in {time.time()-start_total:.2f} seconds.")
    print("-" * 60)
    return tables


def print_summary(tables: Dict[str, pd.DataFrame]):
    """Print validation summary for all extracted tables."""
    print("\n" + "=" * 90)
    print(f"{'TABLE NAME':<20} | {'ROWS':<8} | {'MIN (YEAR-Q)':<14} | {'MAX (YEAR-Q)':<14} | {'DISTINCT STATES':<15}")
    print("-" * 90)
    
    pk_info = {
        'agg_transaction': '(state, year, quarter, category)',
        'agg_user': '(state, year, quarter)',
        'agg_user_device': '(state, year, quarter, brand)',
        'agg_insurance': '(state, year, quarter, category)',
        'map_transaction': '(state, district, year, quarter)',
        'map_user': '(state, district, year, quarter)',
        'map_insurance': '(state, district, year, quarter)',
        'top_transaction': '(level, state, entity_type, entity_name, year, quarter)',
        'top_user': '(level, state, entity_type, entity_name, year, quarter)',
        'top_insurance': '(level, state, entity_type, entity_name, year, quarter)'
    }
    
    for name, df in tables.items():
        row_count = len(df)
        if row_count > 0:
            min_row = df.sort_values(by=['year', 'quarter']).iloc[0]
            max_row = df.sort_values(by=['year', 'quarter']).iloc[-1]
            min_period = f"{min_row['year']}-Q{min_row['quarter']}"
            max_period = f"{max_row['year']}-Q{max_row['quarter']}"
            distinct_states = df['state'].nunique()
        else:
            min_period, max_period, distinct_states = 'N/A', 'N/A', 0
            
        print(f"{name:<20} | {row_count:<8} | {min_period:<14} | {max_period:<14} | {distinct_states:<15}")
    print("=" * 90)
    print("\nComposite Primary Keys Enforced:")
    for name, pk in pk_info.items():
        print(f"  * {name:<18} -> PK {pk}")
    print("=" * 90)


if __name__ == '__main__':
    extracted_tables = extract_all()
    
    # Save extracted tables to data_clean directory as CSV for fast subsequent usage
    out_dir = "data_clean"
    os.makedirs(out_dir, exist_ok=True)
    for name, df in extracted_tables.items():
        out_path = os.path.join(out_dir, f"{name}.csv")
        df.to_csv(out_path, index=False)
        
    print_summary(extracted_tables)
