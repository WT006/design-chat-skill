"""Render captured replies as a standalone, dialogue-only comparison."""
from html import escape
import re


STYLE = """
*{box-sizing:border-box}body{margin:0;background:#f4f5f7;color:#202734;
font:16px/1.8 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:1480px;margin:auto;padding:28px 32px 80px}
section{margin-bottom:64px}h1{font-size:19px;font-weight:600;margin:12px 0 20px}
.pair{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px}
.heads{position:sticky;top:0;z-index:1;background:#f4f5f7;padding:12px 0;
border-bottom:1px solid #dce1e8;margin-bottom:20px;font-weight:600;text-align:center}
.conversation{min-width:0;display:flex;flex-direction:column;padding:0 0 24px;gap:16px}
.bubble{max-width:96%;padding:16px 20px;border-radius:18px;
overflow-wrap:anywhere}.user{align-self:flex-end;background:#e0ebff;color:#173b70;
border-bottom-right-radius:5px}.assistant{align-self:flex-start;background:white;
border:1px solid #e4e8ef;border-bottom-left-radius:5px}
.role{display:block;font-size:12px;line-height:1.4;margin-bottom:8px;color:#62748c}
.missing{color:#697586;font-style:italic}
.bubble p{margin:0 0 .8em}.bubble p:last-child{margin-bottom:0}
.bubble pre{white-space:pre-wrap;background:#f2f4f7;padding:12px;border-radius:8px;
font:13px/1.7 ui-monospace,monospace}.bubble code{font-size:.9em}
.table-wrap{overflow:auto;margin:12px 0}.bubble table{border-collapse:collapse;
width:100%;font-size:14px}.bubble th,.bubble td{padding:7px 9px;border:1px solid #dce1e8;
text-align:left;vertical-align:top}.bubble th{background:#f4f6f9}
@media(max-width:700px){main{padding:12px 12px 40px}.pair{gap:12px}
.bubble{max-width:100%;padding:12px;font-size:14px}h1{font-size:17px}}
"""


def inline(text):
    # Escape first; support a small safe subset without scripts, raw HTML, or active links.
    tokens = re.split(r'(`[^`]+`|\*\*[^*]+\*\*)', text)
    rendered = []
    for token in tokens:
        if token.startswith('`') and token.endswith('`') and len(token) > 2:
            rendered.append('<code>' + escape(token[1:-1]) + '</code>')
        elif token.startswith('**') and token.endswith('**') and len(token) > 4:
            rendered.append('<strong>' + escape(token[2:-2]) + '</strong>')
        else:
            rendered.append(escape(token))
    return ''.join(rendered)


def message_html(text):
    lines, parts, paragraph = text.splitlines(), [], []

    def flush():
        if paragraph:
            parts.append('<p>' + '<br>'.join(inline(line) for line in paragraph) + '</p>')
            paragraph.clear()

    def cells(line):
        return [cell.strip() for cell in line.strip().strip('|').split('|')]

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('```'):
            flush()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i])
                i += 1
            parts.append('<pre><code>' + escape('\n'.join(code)) + '</code></pre>')
        elif ('|' in line and i + 1 < len(lines) and '|' in lines[i + 1]
              and all(re.fullmatch(r':?-{3,}:?', c) for c in cells(lines[i + 1]))):
            flush()
            parts.append('<div class="table-wrap"><table><thead><tr>' +
                         ''.join('<th>' + inline(c) + '</th>' for c in cells(line)) +
                         '</tr></thead><tbody>')
            i += 2
            while i < len(lines) and '|' in lines[i] and lines[i].strip():
                parts.append('<tr>' + ''.join('<td>' + inline(c) + '</td>'
                                            for c in cells(lines[i])) + '</tr>')
                i += 1
            parts.append('</tbody></table></div>')
            continue
        elif not line.strip():
            flush()
        elif re.match(r'^#{1,6} ', line):
            flush()
            parts.append('<p><strong>' + inline(line.lstrip('#').strip()) + '</strong></p>')
        else:
            paragraph.append(line)
        i += 1
    flush()
    return ''.join(parts)


def bubble(role, content):
    label = '你' if role == 'user' else 'AI'
    return (f'<div class="bubble {role}"><span class="role">{label}</span>'
            f'{message_html(content)}</div>')


def render(out, cases, results, filename='comparison.html'):
    lookup = {(r['variant'], r['case']): r for r in results}
    parts = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>Talk to Plan · 对话对比</title>', f'<style>{STYLE}</style>',
             '</head><body><main>']
    for case in cases:
        parts.append(f'<section><h1>{escape(case["title"])}</h1>'
                     '<div class="pair heads"><div>上次</div><div>这次</div></div>'
                     '<div class="pair">')
        for variant in ('baseline', 'candidate'):
            result = lookup.get((variant, case['id']), {})
            parts.append('<div class="conversation">')
            for row in result.get('rows', []):
                parts.append(bubble('user', row['user']))
                if row.get('reply', '').strip():
                    parts.append(bubble('assistant', row['reply']))
                else:
                    parts.append('<div class="bubble missing">本轮未取得完整回复</div>')
            if not result.get('rows') or result.get('completed') is False:
                parts.append('<div class="bubble missing">对话未完整运行，已有回复保留如上。</div>')
            parts.append('</div>')
        parts.append('</div></section>')
    parts.append('</main></body></html>')
    target = out / filename
    target.write_text('\n'.join(parts), encoding='utf-8')
    return target
