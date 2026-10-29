"""Local Streamlit monitor: overview → trend → exact MQTT observation."""
from pathlib import Path
from html import escape
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import streamlit as st
import pandas as pd
from dashboard.collector import Collector
from dashboard.store import device_view,freshness
from dashboard.presentation import METRICS,STATES,thresholds,bands,reading_status,reasons,since_for,selected_ids
from dashboard.charts import chart_frame,trend_chart
from dashboard.gauges import gauge_markdown
from tools.runtime_config import MQTT_HOST,MQTT_PORT,TOPIC_PREFIX,setting

st.set_page_config(page_title='PCCC · Nhóm 07',page_icon='🚨',layout='wide')
st.markdown('''<style>
.block-container{max-width:1480px;padding-top:2rem;padding-bottom:2rem}
h1{font-size:2rem!important;letter-spacing:-.035em}h2{font-size:1.35rem!important}
h3{font-size:1.1rem!important} [data-testid="stMetricValue"]{font-size:2rem}
[data-testid="stCaptionContainer"]{font-size:.87rem}
.st-key-sensor_cards button{height:160px;padding:8px 12px;justify-content:flex-start;border-radius:8px}
.st-key-sensor_cards button [data-testid="stMarkdownContainer"]{width:100%}
.st-key-sensor_cards button p{text-align:left;line-height:1.45;white-space:normal;font-size:.8rem;margin:0}
.st-key-sensor_cards button p strong:first-child{font-size:.95rem}
.st-key-sensor_cards button img{display:block!important;height:84px!important;max-height:84px!important;width:176px!important;max-width:100%!important;object-fit:contain;margin:2px auto}
.st-key-sensor_cards button p{text-align:center;line-height:1.2}
.st-key-sensor_cards button[kind="primary"]{background:#EFF6FF;color:#172554;border:2px solid #2563EB}
.st-key-sensor_cards [data-testid="stVerticalBlock"]{gap:.4rem}
.command-strip{display:flex;flex-wrap:wrap;gap:6px;padding:7px 0 2px}
.command-badge{border:1px solid #CBD5E1;background:#F8FAFC;color:#334155;border-radius:5px;padding:4px 9px;font-size:.83rem;line-height:1.3}
.st-key-overview_compact [data-testid="stVerticalBlock"]{gap:.5rem}
.status-pill{display:inline-block;padding:.25rem .6rem;border-radius:6px;font-size:.8rem;font-weight:600;margin:.25rem 0}
.danger{background:#FEE2E2;color:#991B1B}.warn{background:#FEF3C7;color:#92400E}
.info{background:#E0F2FE;color:#075985}.muted{background:#E2E8F0;color:#334155}
@media(max-width:640px){.block-container{padding:1.2rem 1rem}h1{font-size:1.65rem!important}}
</style>''',unsafe_allow_html=True)
st.title('PCCC · Giám sát hệ thống')
st.caption('Nhóm 07 · Mô hình ESP32 / Wokwi · Dashboard chỉ theo dõi, không gửi lệnh điều khiển')

@st.cache_resource
def resource(host,port,prefix,path):return Collector(host,port,prefix,path)

expected=setting('PCCC_EXPECTED_FIRMWARE_ID')
config=(MQTT_HOST,MQTT_PORT,TOPIC_PREFIX,setting('PCCC_DASHBOARD_DB',str(ROOT/'runs/dashboard.sqlite3')))
previous=st.session_state.get('monitor_config')
if previous and previous!=config:resource(*previous).stop()
st.session_state.monitor_config=config
try:
    collector=resource(*config)
    if setting('PCCC_DASHBOARD_OFFLINE')!='1':collector.start()
except (ValueError,OSError) as error:
    st.error(str(error));st.stop()


def local_time(value):
    return datetime.fromisoformat(value).astimezone(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%d/%m/%Y · %H:%M:%S')


def show_details(row):
    p=row['payload']
    st.markdown(f'**Bản ghi #{row["id"]} · snapshot ESP32**')
    st.caption(f'PC nhận: {local_time(row["received_utc"])} · {"bản tin retained" if row["retained"] else "bản tin không retained"} · {"import lịch sử" if row["session"]=="IMPORT" else "phiên thu MQTT"}')
    st.dataframe([{'Cảm biến':m.source,'Thông số':m.name,'Giá trị gốc':p.get(m.key),'Đơn vị':m.unit} for m in METRICS.values()],hide_index=True,width='stretch')
    st.caption(f'Firmware: {p.get("firmware_id","—")} · Lần khởi động: {p.get("boot_id","—")} · Uptime snapshot: {p.get("uptime_ms","—")} ms')
    st.code(row['topic'],language=None)
    st.caption('Đây là giá trị trong snapshot, không phải trung bình. MQTT chưa gửi thời điểm đo riêng và cờ chất lượng cho từng cảm biến. Thời điểm PC nhận không thay thế thời điểm đo.')
    with st.expander('Xem nguyên bản JSON của bản ghi này'):
        st.json(p)


@st.fragment(run_every='2s')
def monitor():
    view=device_view(collector.store,collector.session,collector.connected and collector.subscribed,expected)
    q=view['data'];live=view['live'];row=view['row'];limits=thresholds()
    st.subheader('01 · Tổng quan hệ thống')
    status_col,connection_col=st.columns([3,2],gap='large')
    with status_col:
        if live:
            title,description=STATES[q['state']]
            {'NORMAL':st.success,'WARNING':st.warning,'FIRE_SUPPRESSION':st.error,'RECOVERY':st.warning}[q['state']](f'**{title}** — {description}')
        else:
            st.warning('**Chưa có dữ liệu trực tiếp / OFFLINE** — không kết luận hệ thống an toàn.')
            if row:st.caption(f'Trạng thái cuối đã lưu: {STATES[q["state"]][0]}. Các số bên dưới là lịch sử.')
        if live:
            why=reasons(q.get('active_mask'))
            st.write('Nguyên nhân ESP đang báo: '+(' · '.join(why) if why else 'Không có cờ nguyên nhân đang kích hoạt.'))
            if q['state']=='RECOVERY':st.caption('ACK '+('đã sẵn sàng: thả rồi nhấn nút trên mô hình.' if q.get('ack_ready') else 'chưa sẵn sàng; chờ đủ điều kiện an toàn theo ESP.'))
            if q.get('suppression_locked'):st.warning('ESP đang khóa bơm do hết thời gian. Kiểm tra mô hình trước khi ACK.')
    with connection_col:
        st.write('**Máy chủ dữ liệu:** '+('Đã kết nối' if collector.subscribed else 'Đang kết nối lại…'))
        st.write('**ESP32:** '+('Đang cập nhật' if live else 'Chưa có cập nhật hợp lệ'))
        st.write('**AI trên ESP32:** '+(('Có kết quả còn hiệu lực' if q.get('ai_available') else 'Chưa có kết quả còn hiệu lực') if live else 'Chưa biết trạng thái hiện tại'))
        if not collector.subscribed and st.button('Kết nối lại',disabled=setting('PCCC_DASHBOARD_OFFLINE')=='1'):
            collector.stop();collector.start()
    if collector.error:st.error(collector.error)
    if view['wrong_firmware']:st.error('Firmware không khớp cấu hình mong đợi. Dữ liệu chỉ được xem như lịch sử.')
    if view['fixture']:st.warning('Dữ liệu kiểm thử FAKE/HOST/MOCK — không phải ESP32 trực tiếp.')

    if 'focus_metric' not in st.session_state:st.session_state.focus_metric='smoke_adc'
    def select_sensor(key):
        st.session_state.focus_metric=key
        st.session_state.monitor_tab='Xu hướng & tra cứu'

    with st.container(key='overview_compact'):
        stamp=f'Snapshot #{row["id"]} · PC nhận {local_time(row["received_utc"])}' if row else 'Chưa có snapshot'
        st.caption(stamp+' · '+('Trực tiếp' if live else 'Lịch sử / OFFLINE')+' · KPI luôn là snapshot cuối, không đổi theo bộ lọc lịch sử.')
        with st.container(key='sensor_cards'):
            for col,m in zip(st.columns(4,gap='small'),METRICS.values()):
                val=q.get(m.key)
                label,tone=reading_status(m.key,q,live,limits)
                # Snapshot freshness is shared above, not repeated on every card.
                if not live and val is not None:label=m.source
                with col:
                    st.button(f'**{m.name}**  \n{gauge_markdown(m,val,live)}  \n{label}',
                        key='focus_'+m.key,width='stretch',
                        type='primary' if st.session_state.focus_metric==m.key else 'secondary',
                        on_click=select_sensor,args=(m.key,))
        items={'Bơm':'pump_cmd','Van':'valve_cmd','Cửa thoát hiểm':'door_open_cmd','Còi':'buzzer_cmd','Đèn đỏ':'red_led_cmd','Đèn xanh':'green_led_cmd'}
        badges=[]
        for name,key in items.items():
            v=q.get(key)
            text='Chưa có lệnh' if v is None else ('MỞ' if v else 'ĐÓNG') if key=='door_open_cmd' else ('BẬT' if v else 'TẮT')
            badges.append(f'<span class="command-badge"><b>{escape(name)}</b> {text}</span>')
        st.markdown('<div class="command-strip">'+''.join(badges)+'</div>',unsafe_allow_html=True)
        st.caption('Lệnh cuối ghi nhận từ ESP32 · Chưa có phản hồi trạng thái vật lý.'+(' Dữ liệu lịch sử; chưa biết trạng thái hiện tại.' if not live else ''))
        with st.expander('Nguồn cảm biến & metadata snapshot'):
            st.caption('Chọn một thẻ để xem biểu đồ, ngưỡng và bảng dữ liệu của đúng cảm biến đó.')
            st.dataframe([{'Thông số':m.name,'Nguồn':m.source,'Ghi chú':m.note} for m in METRICS.values()],hide_index=True,width='stretch')
            if row:show_details(row)

    trend_tab,ai_tab,event_tab,accept_tab=st.tabs(['Xu hướng & tra cứu','AI & kết nối','Sự kiện hệ thống','Nghiệm thu'],key='monitor_tab',on_change='rerun')
    # One shared history filter controls charts, record tables and event history.
    st.session_state.setdefault('history_range','Lần chạy cuối')
    with trend_tab:
        st.subheader('02 · Theo dõi xu hướng')
        a,b=st.columns([2,3])
        with a:period=st.selectbox('Khoảng dữ liệu', ['Lần chạy cuối','15 phút qua','1 giờ qua','24 giờ qua','Tất cả đã lưu'],key='history_range')
        with b:focus=st.selectbox('Cảm biến cần tra cứu',list(METRICS),format_func=lambda k:METRICS[k].name,key='focus_metric')
        since=since_for(period)
        boot=q.get('boot_id') if period=='Lần chạy cuối' else None
        rows=collector.store.window('telemetry',since,boot,limit=2000)
        metric=METRICS[focus]
        st.caption(f'{metric.source} · {metric.note}')
        selected=[]
        if rows:
            frame=chart_frame(rows,metric)
            st.caption(f'{len(rows):,} snapshot · {local_time(rows[-1]["received_utc"])} → {local_time(rows[0]["received_utc"])} · giờ Việt Nam. Tối đa 2.000 bản ghi mới nhất trong bộ lọc; không lấy trung bình.')
            selection=st.altair_chart(trend_chart(frame,metric,limits),width='stretch',key=f'trend_{focus}_{period}',on_select='rerun',selection_mode='record')
            selected=selected_ids(selection)
            st.caption('Di chuột: xem số chính xác và mã bản ghi. Bấm một điểm: tra bản tin nguồn bên dưới. Bấm đúp: bỏ chọn.')
            refs=bands(focus,limits)
            if refs:st.caption('Ngưỡng tham chiếu: '+' · '.join(f'{x["label"]}: {x["value"]:g} {metric.unit}' for x in refs))
            else:st.caption('Độ ẩm không có ngưỡng cảnh báo trong firmware hiện tại.')
        else:st.info('Không có bản ghi trong khoảng này. Chọn “Lần chạy cuối” hoặc “Tất cả đã lưu” để xem lịch sử đã nhận.')
        with st.expander('Đọc ngưỡng và thời gian cho đúng'):
            st.write('Đường đứt lấy từ include/config.h hiện tại; firmware trong lịch sử có thể dùng cấu hình khác. Trạng thái hệ thống luôn lấy từ bản tin ESP, không suy ra lại từ biểu đồ.')
            st.write(f'Khói có hysteresis {limits.get("kSmokeHysteresisAdc","—"):g} ADC. LDR và nhiệt có ngưỡng bật/xóa riêng; vì vậy dưới đường cảnh báo chưa chắc ESP đã xóa cờ. Tốc độ tăng nhiệt cũng là một nguyên nhân độc lập.')
            st.caption('Trục X là thời điểm PC nhận (UTC+7). Giờ UTC mô phỏng Wokwi và uptime của ESP được giữ trong bản tin nguồn, không dùng làm độ trễ vật lý. Khoảng 15 phút/1 giờ/24 giờ tính từ giờ PC hiện tại; “Lần chạy cuối” theo boot_id của snapshot cuối.')

        st.subheader('03 · Tra cứu dữ liệu gốc')
        if rows:
            abnormal=st.checkbox('Chỉ bản ghi có cảnh báo / nguy hiểm / lỗi cảm biến',key='abnormal_only')
            investigation=[r for r in rows if not abnormal or r['payload'].get('merged_level',0)>0 or r['payload'].get('active_mask',0)>0]
            chosen=[r for r in rows if r['id'] in selected]
            if chosen:
                st.info(f'Đang tra điểm đã chọn trên biểu đồ: bản ghi #{chosen[0]["id"]}. Bộ lọc bảng không che mất điểm này.')
                show_details(chosen[0])
            table=[dict(ID=r['id'],**{'PC nhận (VN)':local_time(r['received_utc']),metric.name:r['payload'].get(focus),'Đơn vị':metric.unit,'Trạng thái ESP':STATES[r['payload']['state']][0],'Nguyên nhân ESP':' · '.join(reasons(r['payload'].get('active_mask'))) or 'Không có cờ / chưa có trường dữ liệu','Uptime (ms)':r['payload'].get('uptime_ms')}) for r in investigation]
            if table:
                df=pd.DataFrame(table)
                st.dataframe(df,hide_index=True,width='stretch',height=290)
                st.download_button('Tải CSV đúng bộ lọc',df.to_csv(index=False).encode('utf-8-sig'),'pccc-sensor-records.csv','text/csv')
                by_id={r['id']:r for r in investigation}
                detail_id=st.selectbox('Mở bản ghi theo mã ID',list(by_id),index=None,placeholder='Chọn mã từ bảng để xem bản tin gốc',key=f'detail_{focus}_{period}_{abnormal}',format_func=lambda rid:f'#{rid} · {local_time(by_id[rid]["received_utc"])}')
                if detail_id is not None:show_details(by_id[detail_id])
                elif not chosen:
                    st.caption('Hoặc mở snapshot đã tạo ra 4 thẻ tổng quan:')
                    with st.expander(f'Bản ghi #{row["id"]} · nguồn của 4 thẻ tổng quan'):
                        show_details(row)
            else:st.info('Không có snapshot cảnh báo trong bộ lọc. Điều này không chứng minh các khoảng mất dữ liệu là an toàn.')
        else:st.caption('Bảng và biểu đồ dùng cùng bộ lọc; chưa có dữ liệu để tra cứu.')

    with ai_tab:
        st.subheader('AI đang cung cấp thông tin gì?')
        status=collector.store.latest('ai_status');packet=collector.store.latest('ai')
        status_fresh,_=freshness(status,collector.session,collector.connected,limit=12)
        info=status['payload'] if status else {}
        event=info.get('event','')
        messages={'UNAVAILABLE':'Chưa có kết quả nhận diện hợp lệ','CONFIRMING':'Đang chờ đủ mẫu xác nhận','PUBACK':'Đã gửi kết quả tới MQTT','START':'Đang khởi động','STOP':'Nguồn AI đã dừng','ERROR':'Nguồn AI báo lỗi','OFFLINE':'Nguồn AI mất kết nối'}
        st.info(messages.get(event,'Chưa biết trạng thái nguồn AI') if status_fresh else 'Nguồn AI chưa có cập nhật mới — chỉ xem được lịch sử nếu có.')
        a,b=st.columns(2)
        with a:
            st.markdown('**1 · Kết quả gần nhất tại máy chủ MQTT**')
            if packet:
                p=packet['payload'];label={'lua':'Lửa','khoi':'Khói','binh_thuong':'Bình thường'}[p['nhan']]
                st.metric(label,f'{p["do_tin_cay"]:.3f}',help='Confidence của model, không phải xác suất cháy đã được hiệu chuẩn.')
                st.caption(f'PC nhận: {local_time(packet["received_utc"])}. Bản tin gần nhất đã lưu, không khẳng định đang còn hiệu lực.')
            else:st.write('Chưa có bản tin AI được lưu.')
        with b:
            st.markdown('**2 · ESP32 xử lý kết quả AI**')
            st.write('AI còn hiệu lực: '+('Có' if q.get('ai_available') else 'Không') if live else 'Chưa có trạng thái ESP32 trực tiếp.')
            st.write(f'Tổng nhận / từ chối trong lần boot: {q.get("ai_accepted","—")} / {q.get("ai_rejected","—")}')
            st.caption('Các bộ đếm lấy từ snapshot ESP32 cuối; không chứng minh bản tin bên trái là bản tin đã được chấp nhận.')
        st.caption('Không phát hiện ≠ bình thường. Mức AI 0 có thể do confidence thấp hoặc hết hạn. Model hiện chưa được nghiệm thu độc lập.')
        st.write(f'Nguồn: {info.get("backend","Chưa biết")} · Model: {info.get("model_id","—")}')
        if info.get('timestamp_domain')=='WOKWI_SIMULATED_UTC':st.warning('Đang dùng đồng hồ Wokwi. TTL trên ESP tính bằng giây mô phỏng.')
        with st.expander('Chi tiết nguồn AI'):
            if info:st.json(info)
            else:st.caption('Chưa có metadata nguồn AI.')
    with event_tab:
        st.subheader('Dòng sự kiện ESP32')
        st.caption(f'Cùng khoảng dữ liệu: {period}. Mỗi hàng là EVENT đã nhận, không tự dựng sự kiện từ đường biểu đồ. Tối đa 500 sự kiện mới nhất.')
        records=collector.store.window('event',since,boot,limit=500)
        if records:
            table=[{'ID':r['id'],'PC nhận (VN)':local_time(r['received_utc']),'Từ':STATES.get(r['payload'].get('previous_state'),('—',))[0],'Đến':STATES[r['payload']['state']][0],'Lý do chuyển':r['payload'].get('transition_reason'),'Nguyên nhân':' · '.join(reasons(r['payload'].get('active_mask'))),'Nguồn':r['payload'].get('source')} for r in records]
            df=pd.DataFrame(table);st.dataframe(df,hide_index=True,width='stretch')
            st.download_button('Tải CSV sự kiện',df.to_csv(index=False).encode('utf-8-sig'),'pccc-events.csv','text/csv')
            with st.expander('Mở bản tin sự kiện gốc'):
                chosen_event=st.selectbox('Mã EVENT',[r['id'] for r in records])
                show_details(next(r for r in records if r['id']==chosen_event))
        else:st.info('Chưa có EVENT trong bộ lọc; dashboard có thể bỏ lỡ sự kiện khi mất kết nối.')
    with accept_tab:
        st.subheader('Theo dõi nghiệm thu đồ án')
        st.caption('Tách biệt với giám sát trực tiếp. Chỉ đọc bảng nghiệm thu; dashboard không tự ghi PASS.')
        sys.path.insert(0,str(ROOT/'tools'))
        from s8_track import LEDGER,summary
        if LEDGER.exists():st.dataframe([dict(TC=tc,**values) for tc,values in summary(LEDGER).items()],hide_index=True,width='stretch')
        else:st.warning('Chưa tìm thấy bảng nghiệm thu gốc.')

    with st.expander('Cài đặt nâng cao · cấu hình từ .env'):
        st.write(f'Máy chủ MQTT: {MQTT_HOST}:{MQTT_PORT} · Nhóm topic: {TOPIC_PREFIX}')
        st.caption('Sửa .env rồi khởi động lại dịch vụ. Không hiển thị mật khẩu. SQLite giữ tối đa khoảng 50.000 bản ghi mỗi prefix.')
        st.write(f'Gói lỗi: {collector.invalid} · Firmware cuối: {q.get("firmware_id","—")} · Boot: {q.get("boot_id","—")}')
        st.caption(f'Local / AI / tổng: {q.get("local_level","—")} / {q.get("ai_level","—")} / {q.get("merged_level","—")} · Nguồn chốt: {q.get("latched_source","—")} · Max loop gap: {q.get("max_loop_gap_ms","—")} ms; không phải độ trễ cảm biến.')

monitor()
