"""Consistent chart presentation with exact record-id selection and PC timestamps."""
import altair as alt
import pandas as pd
from .presentation import bands

def chart_frame(rows,metric):
    data=[]
    for row in rows:
        stamp=pd.Timestamp(row['received_utc']).tz_convert('Asia/Ho_Chi_Minh')
        mask={'smoke_adc':(1<<0)|(1<<1)|(1<<6),'ldr_adc':(1<<2)|(1<<7),'temperature_c':(1<<3)|(1<<4)|(1<<5),'humidity_pct':1<<5}[metric.key]
        flagged=bool(row['payload'].get('active_mask',0)&mask)
        data.append(dict(flag='ESP gắn cờ' if flagged else 'Không có cờ tương ứng',record_id=row['id'],received=stamp.tz_localize(None),
            time_label=stamp.strftime('%d/%m/%Y %H:%M:%S.%f')[:-3],value=row['payload'].get(metric.key),
            state=row['payload'].get('state'),boot=row['payload'].get('boot_id')))
    return pd.DataFrame(data,columns=['flag','record_id','received','time_label','value','state','boot']).sort_values(['received','record_id'])

def trend_chart(data,metric,thresholds):
    select=alt.selection_point(name='record',fields=['record_id'],on='click',clear='dblclick',toggle=False)
    base=alt.Chart(data).encode(
        x=alt.X('received:T',title='Thời điểm PC nhận · giờ Việt Nam',axis=alt.Axis(format='%H:%M:%S',labelAngle=0,tickCount=6)),
        y=alt.Y('value:Q',title=f'{metric.name} ({metric.unit})',scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip('time_label:N',title='PC nhận (VN)'),alt.Tooltip('value:Q',title=f'{metric.name} · {metric.unit}',format='.3f'),alt.Tooltip('record_id:Q',title='Mã bản ghi',format='d'),alt.Tooltip('state:N',title='Trạng thái ESP')])
    line=base.mark_line(color=metric.color,strokeWidth=2.5).encode(detail='boot:N')
    points=base.mark_point(size=65,color=metric.color,filled=True).encode(shape=alt.Shape('flag:N',title='Trạng thái trong snapshot',scale=alt.Scale(domain=['Không có cờ tương ứng','ESP gắn cờ'],range=['circle','triangle-up']),legend=alt.Legend(orient='bottom')),opacity=alt.condition(select,alt.value(1),alt.value(.4))).add_params(select)
    layers=[line,points]
    limits=bands(metric.key,thresholds)
    if limits:
        values=pd.DataFrame(limits)
        limits_base=alt.Chart(values).encode(y='value:Q',tooltip=[alt.Tooltip('label:N',title='Ngưỡng tham chiếu'),alt.Tooltip('value:Q',title=metric.unit)])
        layers.append(limits_base.mark_rule(color='#64748B',strokeDash=[6,5],opacity=.8))
        layers.append(limits_base.mark_text(align='left',dx=6,dy=-8,fontSize=12,color='#475569').encode(x=alt.value(0),text='label:N'))
    return alt.layer(*layers).properties(height=330).configure_axis(labelFontSize=12,titleFontSize=13,titlePadding=14,gridColor='#E2E8F0').configure_view(stroke=None)
