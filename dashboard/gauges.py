"""Small SVG readout gauges. Display scales are not safety classifications."""
import base64
from html import escape
import math


def gauge_svg(metric,value,live=True):
    lower,upper=(0,4095) if metric.unit=='ADC' else (0,100)
    if value is not None and metric.unit=='°C':
        # Expand the visual scale only. Never clip or alter the printed reading.
        lower=min(0,math.floor(value/10)*10)
        upper=max(100,math.ceil(value/10)*10)
    fraction=0 if value is None else max(0,min(1,(value-lower)/(upper-lower)))
    color=metric.color
    opacity=1 if live else .55
    text='—' if value is None else f'{value:,.0f}' if metric.unit=='ADC' else f'{value:.1f}'
    label=f'{text} {metric.unit}'
    # pathLength makes the stroke fraction independent of SVG rendering size.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 130" role="img" aria-label="{escape(metric.name)}: {escape(label)}">
<path d="M 28 100 A 82 82 0 0 1 192 100" pathLength="100" fill="none" stroke="#E2E8F0" stroke-width="13" stroke-linecap="round"/>
<path d="M 28 100 A 82 82 0 0 1 192 100" pathLength="100" fill="none" stroke="{color}" opacity="{opacity}" stroke-width="13" stroke-linecap="{'round' if fraction else 'butt'}" stroke-dasharray="{fraction*100:.3f} 100"/>
<text x="110" y="77" text-anchor="middle" font-family="Arial,sans-serif" font-size="32" font-weight="600" fill="#0F172A">{escape(text)}</text>
<text x="110" y="98" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#475569">{escape(metric.unit)}</text>
<text x="22" y="123" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#64748B">{lower:g}</text>
<text x="198" y="123" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#64748B">{upper:g}</text>
</svg>'''


def gauge_markdown(metric,value,live=True):
    svg=gauge_svg(metric,value,live)
    encoded=base64.b64encode(svg.encode()).decode()
    text='—' if value is None else f'{value:,.0f}' if metric.unit=='ADC' else f'{value:.1f}'
    return f'![{text} {metric.unit}](data:image/svg+xml;base64,{encoded})'
