"""Optional Streamlit AppTest; no broker/camera connection."""
import os
from pathlib import Path
import tempfile
os.environ['PCCC_DASHBOARD_OFFLINE']='1'
from streamlit.testing.v1 import AppTest
temporary=tempfile.TemporaryDirectory()
os.environ['PCCC_DASHBOARD_DB']=str(Path(temporary.name)/'empty.sqlite3')
app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'dashboard/app.py'),default_timeout=30).run()
assert not app.exception,[x.message for x in app.exception]
assert any('PCCC' in x.value for x in app.title)
assert any('OFFLINE' in x.value for x in app.warning)
assert len(app.sidebar.text_input)==0
assert any('Cài đặt nâng cao' in e.label for e in app.expander)
assert not any(button.label in ('ACK','Bật bơm','Mở cửa') for button in app.button)
temporary.cleanup()
print('PASS dashboard UI renders offline/history, sensors/charts/AI/events/acceptance; no control buttons or network connection.')

# Isolated fixture in a temporary DB; never publish it to the user's dashboard.
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard.store import Store
from dashboard.charts import chart_frame,trend_chart
from dashboard.presentation import METRICS,thresholds
with tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'fixture.sqlite3'
    os.environ['PCCC_DASHBOARD_DB']=str(path)
    store=Store(path,os.getenv('PCCC_TOPIC_PREFIX','ptit/nhom07/lab-7c49e2'))
    for i in range(3):
        p=dict(v=1,record_type='TELEMETRY',firmware_id='FAKE_UI',boot_id='ui-test',uptime_ms=i*1000,state='NORMAL',local_level=0,ai_level=0,merged_level=0,pump_cmd=False,valve_cmd=False,door_open_cmd=False,buzzer_cmd=False,smoke_adc=1200+i,ldr_adc=2045,temperature_c=28.1,humidity_pct=45.2,active_mask=0)
        store.add(store.prefix+'/device/esp32-01/telemetry',json.dumps(p).encode(),received_utc=f'2000-01-01T03:00:0{i}+00:00')
    latest=store.latest('telemetry')
    rows=store.window('telemetry',boot_id='ui-test')
    for key,metric in METRICS.items():
        frame=chart_frame(rows,metric)
        assert frame.iloc[-1]['value']==latest['payload'][key]
        assert int(frame.iloc[-1]['record_id'])==latest['id']
        spec=trend_chart(frame,metric,thresholds()).to_dict()
        assert any(x['name']=='record' for x in spec['params'])
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'dashboard/app.py'),default_timeout=30).run()
    assert not app.exception,[x.message for x in app.exception]
    assert '![1,202 ADC]' in app.button(key='focus_smoke_adc').label
    app.selectbox(key='history_range').select('Tất cả đã lưu').run()
    for key,metric in METRICS.items():
        app.button(key='focus_'+key).click().run()
        assert app.selectbox(key='focus_metric').value==key
        assert app.selectbox(key='history_range').value=='Tất cả đã lưu'
        assert app.session_state['monitor_tab']=='Xu hướng & tra cứu'
        assert not app.exception,[x.message for x in app.exception]
        tables=[x.value for x in app.dataframe if metric.name in x.value.columns]
        assert len(tables)==1
        assert tables[0][metric.name].iloc[0]==latest['payload'][key]
        assert app.button(key='focus_'+key).proto.type=='primary'
    app.selectbox(key='focus_metric').select('temperature_c').run()
    assert app.button(key='focus_temperature_c').proto.type=='primary'
    assert not app.exception,[x.message for x in app.exception]
    app.selectbox(key='history_range').select('15 phút qua').run()
    assert any('Không có bản ghi' in x.value for x in app.info)
    assert '![1,202 ADC]' in app.button(key='focus_smoke_adc').label
    app.selectbox(key='history_range').select('Lần chạy cuối').run()
    app.selectbox(key='detail_temperature_c_Lần chạy cuối_False').select(latest['id']).run()
    assert any('snapshot ESP32' in x.value for x in app.markdown)
    assert not app.exception,[x.message for x in app.exception]
    store.close()
print('PASS KPI = chart endpoint = original record; all 4 chart schemas, metric navigation, time filtering, exact-ID details.')
