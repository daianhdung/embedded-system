"""SQLite observations. Read-only monitoring never writes a device command."""
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import threading
import time
from datetime import datetime, timezone

STATES={'NORMAL','WARNING','FIRE_SUPPRESSION','RECOVERY'}


def decode(topic, body, prefix):
    if len(body)>8192:
        raise ValueError('payload too large')
    suffix=topic.removeprefix(prefix+'/')
    if suffix==topic:
        raise ValueError('unexpected topic')
    if suffix=='device/esp32-01/availability':
        value=body.decode('utf-8')
        if value not in ('online','offline'):raise ValueError('bad availability')
        return 'availability',{'status':value}
    value=json.loads(body,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    if not isinstance(value,dict):raise ValueError('object expected')
    if suffix in ('device/esp32-01/telemetry','device/esp32-01/event'):
        expected='EVENT' if suffix.endswith('/event') else 'TELEMETRY'
        if (type(value.get('v')) is not int or value.get('v')!=1 or value.get('record_type')!=expected or value.get('state') not in STATES
                or not all(isinstance(value.get(k),str) and 0<len(value[k])<=128 for k in ('firmware_id','boot_id'))
                or type(value.get('uptime_ms')) is not int or value['uptime_ms']<0):
            raise ValueError('invalid device identity/state')
        for key in ('local_level','ai_level','merged_level'):
            if type(value.get(key)) is not int or value[key] not in (0,1,2):raise ValueError('invalid level')
        for key in ('pump_cmd','valve_cmd','door_open_cmd','buzzer_cmd'):
            if type(value.get(key)) is not bool:raise ValueError('invalid command state')
        if value['merged_level']!=max(value['local_level'],value['ai_level']):raise ValueError('inconsistent fused level')
        if value['state']!='FIRE_SUPPRESSION' and (value['pump_cmd'] or value['valve_cmd']):raise ValueError('loads outside FIRE')
        if value['state']=='NORMAL' and value['door_open_cmd']:raise ValueError('open door in NORMAL')
        for key in ('temperature_c','humidity_pct','smoke_adc','ldr_adc','temp_rate_c_s','ai_confidence'):
            number=value.get(key)
            if number is not None and (type(number) not in (int,float) or not math.isfinite(number)):
                raise ValueError('invalid sensor number')
        return 'event' if expected=='EVENT' else 'telemetry',value
    if suffix=='ai/result':
        if (set(value)!={'v','nhan','do_tin_cay','ts_ms'} or type(value['v']) is not int or value['v']!=1
                or value['nhan'] not in ('lua','khoi','binh_thuong')
                or type(value['do_tin_cay']) not in (int,float) or not 0<=value['do_tin_cay']<=1
                or type(value['ts_ms']) is not int):raise ValueError('invalid AI contract')
        return 'ai',value
    if suffix=='ai/status':
        if not isinstance(value.get('event'),str) or len(value['event'])>64:raise ValueError('invalid AI status')
        return 'ai_status',value
    raise ValueError('unsupported topic')


class Store:
    def __init__(self,path,prefix,max_rows=50000):
        self.path=Path(path).resolve();self.path.parent.mkdir(parents=True,exist_ok=True)
        self.prefix=prefix;self.max_rows=max_rows;self.lock=threading.RLock();self.writes=0
        self.db=sqlite3.connect(self.path,check_same_thread=False,timeout=3)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY, namespace TEXT, kind TEXT, topic TEXT, received_utc TEXT, monotonic REAL, session TEXT, retained INTEGER, payload TEXT, fingerprint TEXT, UNIQUE(namespace,fingerprint))')
        self.db.execute('CREATE INDEX IF NOT EXISTS obs_latest ON observations(namespace,kind,id)')
        self.db.commit()

    def add(self,topic,body,retained=False,session='IMPORT',monotonic=None,received_utc=None):
        kind,payload=decode(topic,body,self.prefix)
        canonical=json.dumps(payload,sort_keys=True,allow_nan=False,separators=(',',':'))
        fingerprint=hashlib.sha256((topic+'\0'+canonical).encode()).hexdigest()
        with self.lock,self.db:
            row=self.db.execute('INSERT OR IGNORE INTO observations(namespace,kind,topic,received_utc,monotonic,session,retained,payload,fingerprint) VALUES(?,?,?,?,?,?,?,?,?)',
                (self.prefix,kind,topic,received_utc or datetime.now(timezone.utc).isoformat(),monotonic,session,int(retained),canonical,fingerprint))
            self.writes+=1
            if self.writes%100==0:
                self.db.execute('DELETE FROM observations WHERE namespace=? AND id NOT IN (SELECT id FROM observations WHERE namespace=? ORDER BY id DESC LIMIT ?)',(self.prefix,self.prefix,self.max_rows))
            return bool(row.rowcount)

    def rows(self,kind=None,limit=300):
        where='namespace=?';params=[self.prefix]
        if kind is not None:where+=' AND kind=?';params.append(kind)
        params.append(min(max(int(limit),1),50000))
        with self.lock:
            rows=self.db.execute(f'SELECT * FROM observations WHERE {where} ORDER BY id DESC LIMIT ?',params).fetchall()
        return [dict(row,payload=json.loads(row['payload'])) for row in rows]

    def window(self,kind,since=None,boot_id=None,limit=2000):
        """Exact bounded observations; filters apply before the limit, no aggregation."""
        where='namespace=? AND kind=?';params=[self.prefix,kind]
        if since:
            where+=' AND received_utc>=?';params.append(since)
        if boot_id:
            where+=" AND json_extract(payload,'$.boot_id')=?";params.append(boot_id)
        params.append(min(max(int(limit),1),50000))
        with self.lock:
            rows=self.db.execute(f'SELECT * FROM observations WHERE {where} ORDER BY id DESC LIMIT ?',params).fetchall()
        return [dict(row,payload=json.loads(row['payload'])) for row in rows]

    def latest(self,kind):
        rows=self.rows(kind,1)
        return rows[0] if rows else None

    def close(self):
        with self.lock:self.db.close()


def freshness(row,session,connected,now=None,limit=15):
    if row is None:return False,None
    mono=row.get('monotonic')
    age=None if mono is None else (time.monotonic() if now is None else now)-mono
    fresh=(connected and row['session']==session and not row['retained'] and age is not None and 0<=age<=limit)
    return bool(fresh),age


def device_view(store,session,connected,expected_firmware='',now=None):
    row=store.latest('telemetry');live,age=freshness(row,session,connected,now)
    data=row['payload'] if row else {}
    wrong=bool(expected_firmware and data and data.get('firmware_id')!=expected_firmware)
    fixture=bool(data.get('fixture_not_mcu') or str(data.get('firmware_id','')).upper().startswith(('HOST','FAKE','MOCK')))
    availability=store.latest('availability')
    offline=bool(availability and row and availability['id']>row['id'] and availability['payload']['status']=='offline')
    return dict(row=row,data=data,live=live and not wrong and not fixture and not offline,age=age,
                wrong_firmware=wrong,fixture=fixture,offline=offline)
