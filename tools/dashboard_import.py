#!/usr/bin/env python3
"""Import a capture as historical observations; never marks it as live."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard.store import Store
from mqtt_mock import DEFAULT_PREFIX

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,required=True);p.add_argument('--db',type=Path,default=Path('runs/dashboard.sqlite3'))
    p.add_argument('--prefix',default=DEFAULT_PREFIX);a=p.parse_args()
    store=Store(a.db,a.prefix);count=0;invalid=0
    try:
        for line in a.capture.read_text().splitlines():
            row=json.loads(line)
            if row.get('kind')!='device':continue
            try:
                count+=store.add(row['topic'],json.dumps(row['payload']).encode(),retained=row.get('retained',False),received_utc=row['received_utc'])
            except (ValueError,KeyError,TypeError):invalid+=1
    finally:store.close()
    print(f'Imported {count} historical records; invalid {invalid}; not live, not acceptance PASS.')
if __name__=='__main__':main()
