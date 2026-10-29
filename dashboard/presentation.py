"""Read-only view models: exact observation values, no inferred FSM or safe label."""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
STATES={
    'NORMAL':('Bình thường','ESP32 đang ở trạng thái theo dõi.'),
    'WARNING':('Cần chú ý','ESP32 đang cảnh báo; kiểm tra nguyên nhân bên dưới.'),
    'FIRE_SUPPRESSION':('Đang xử lý nguy hiểm','ESP32 đã kích hoạt chế độ ứng phó.'),
    'RECOVERY':('Chờ xác nhận sau sự cố','Kiểm tra điều kiện an toàn và nhấn ACK trên mô hình khi được phép.'),
}
@dataclass(frozen=True)
class Metric:
    key:str
    name:str
    unit:str
    source:str
    color:str
    note:str

METRICS={m.key:m for m in [
    Metric('smoke_adc','Khói / gas','ADC','MQ-2 · GPIO35','#B45309','ADC thô 0–4095, chưa quy đổi sang ppm.'),
    Metric('ldr_adc','Ánh sáng giả lập lửa','ADC','LDR · GPIO32','#7C3AED','Càng sáng, ADC càng giảm. Đây là demo ánh sáng, không phải cảm biến lửa IR.'),
    Metric('temperature_c','Nhiệt độ','°C','DHT22 · GPIO4','#DC2626','Giá trị nhiệt độ trong snapshot ESP32; không phải số trung bình.'),
    Metric('humidity_pct','Độ ẩm','%','DHT22 · GPIO4','#0369A1','Chỉ theo dõi; firmware không đặt ngưỡng báo cháy theo độ ẩm.'),
]}

def thresholds():
    """Read numeric constants from the actual repository config, not duplicate them."""
    source=(ROOT/'include/config.h').read_text()
    names=['kSmokeWarningAdc','kSmokeDangerAdc','kSmokeHysteresisAdc','kLdrFireAdc','kLdrClearAdc','kTemperatureDangerC','kTemperatureClearC','kTemperatureRateDangerCps']
    found={}
    for name in names:
        match=re.search(r'\b'+name+r'\s*=\s*([0-9.]+)f?\s*;',source)
        if match:found[name]=float(match[1])
    return found

def bands(key,t):
    specs={
        'smoke_adc':[('kSmokeWarningAdc','Cảnh báo'),('kSmokeDangerAdc','Nguy hiểm')],
        'ldr_adc':[('kLdrFireAdc','Bật cờ lửa giả'),('kLdrClearAdc','Xóa cờ lửa giả')],
        'temperature_c':[('kTemperatureDangerC','Nguy hiểm'),('kTemperatureClearC','Xóa cờ nhiệt')],
        'humidity_pct':[],
    }
    return [dict(value=t[name],label=label) for name,label in specs[key] if name in t]

def reading_status(key,payload,live,t):
    if payload.get(key) is None:return 'Chưa có giá trị','muted'
    if not live:return 'Đã lưu · không phải trực tiếp','muted'
    fault={'smoke_adc':1<<6,'ldr_adc':1<<7,'temperature_c':1<<5,'humidity_pct':1<<5}[key]
    if (payload.get('active_mask') or 0)&fault:return 'ESP báo lỗi cảm biến','warn'
    active=payload.get('active_mask') or 0
    if key=='smoke_adc' and active&((1<<0)|(1<<1)):
        return ('ESP báo khói nguy hiểm','danger') if active&(1<<1) else ('ESP cảnh báo khói','warn')
    if key=='ldr_adc' and payload.get('flame_simulated') is True:return 'ESP báo lửa giả lập','danger'
    if key=='temperature_c' and active&((1<<3)|(1<<4)):return 'ESP báo nguy cơ nhiệt','danger'
    if key=='humidity_pct':return 'Theo dõi · không có ngưỡng báo cháy','info'
    # Numerical comparison is deliberately distinct from the firmware's stateful rule.
    v=payload[key]
    if key=='smoke_adc':
        if v>=t.get('kSmokeDangerAdc',float('inf')):return 'Vượt ngưỡng tham chiếu nguy hiểm','danger'
        if v>=t.get('kSmokeWarningAdc',float('inf')):return 'Vượt ngưỡng tham chiếu cảnh báo','warn'
    if key=='ldr_adc' and v<=t.get('kLdrFireAdc',-1):return 'Đạt ngưỡng tham chiếu lửa giả','danger'
    if key=='temperature_c' and v>=t.get('kTemperatureDangerC',float('inf')):return 'Vượt ngưỡng tham chiếu nhiệt','danger'
    return 'Chưa chạm ngưỡng tăng mức','info'

REASONS=[(1<<0,'Khói đạt cảnh báo'),(1<<1,'Khói đạt nguy hiểm'),(1<<2,'LDR kích hoạt lửa giả'),(1<<3,'Nhiệt độ cao'),(1<<4,'Nhiệt tăng nhanh'),(1<<5,'Lỗi DHT22'),(1<<6,'Lỗi mẫu khói'),(1<<7,'Lỗi LDR'),(1<<8,'AI báo khói'),(1<<9,'AI báo lửa')]
def reasons(mask):return [text for bit,text in REASONS if isinstance(mask,int) and mask&bit]

def since_for(label,now=None):
    minutes={'15 phút qua':15,'1 giờ qua':60,'24 giờ qua':1440}.get(label)
    return ((now or datetime.now(timezone.utc))-timedelta(minutes=minutes)).isoformat() if minutes else None

def selected_ids(event):
    selection=event.get('selection',{}).get('record',[]) if event else []
    return [int(item['record_id']) for item in selection if isinstance(item,dict) and type(item.get('record_id')) in (int,float)]
