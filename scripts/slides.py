"""インスタ用カルーセル画像(1080x1350)を作る部品。

使い方(例):
    from slides import cover, page, rows_card, render
    htmls = [cover(tag="GⅠ高松宮記念 住之江|2日目", no="AI", title="モーター<br>格付け", sub="出場52人の機歴をAIが判定"),
             page(2, 6, tag="...", title='展示が<span class="hl">速い</span>モーター', lead="...", body=rows_card([...]), src="出典...")]
    render(htmls, "images/posts/2026-11-06-xxx")
タイトルは1行13文字程度まで。長いときは <br> で改行する。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;font-family:"Noto Sans CJK JP",sans-serif;background:#071a33;color:#fff;position:relative;overflow:hidden}
.glow{position:absolute;inset:0;background:radial-gradient(circle at 85% 10%,rgba(255,196,0,.22),transparent 40%),radial-gradient(circle at 0% 100%,rgba(0,140,255,.28),transparent 50%)}
.tag{position:absolute;top:70px;left:80px;font-size:30px;letter-spacing:.12em;color:#ffc400;font-weight:700}
.page{position:absolute;top:70px;right:80px;font-size:30px;color:#6f8bb0;font-weight:700}
h2{position:absolute;top:150px;left:80px;right:80px;font-size:66px;font-weight:900;line-height:1.25}
.lead{position:absolute;top:330px;left:80px;right:80px;font-size:34px;color:#cfe3ff;line-height:1.55}
.src{position:absolute;bottom:52px;left:80px;right:80px;font-size:23px;color:#6f8bb0;line-height:1.5}
.hl{color:#ffc400}.bad{color:#ff8a8a}
.card{position:absolute;left:80px;right:80px;border-radius:20px;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.12)}
.k{font-size:30px;color:#9bb6d9;font-weight:700}.v{font-size:76px;font-weight:900;line-height:1.1}"""
DISCLAIMER = "※舟券の購入は20歳から。余裕資金で楽しみましょう。データは過去の傾向で、結果を保証するものではありません。"


def cover(tag, no, title, sub, title_px=122):
    c = (ROOT / "templates/cover.html").read_text(encoding="utf-8")
    c = c.replace('<div class="tag">近畿4場をデータで読む</div>', f'<div class="tag">{tag}</div>')
    c = c.replace('<div class="no">01</div>', f'<div class="no">{no}</div>')
    c = c.replace('<h1>住之江<br>攻略の基本</h1>', f'<h1 style="font-size:{title_px}px">{title}</h1>')
    c = c.replace('ナイター水面のクセを数字で', sub)
    if len(sub) > 14:
        c = c.replace('h2{position:absolute;top:720px;left:84px;font-size:56px', 'h2{position:absolute;top:720px;left:84px;font-size:46px')
    return c


def page(n, total, tag, title, lead, body, src):
    lead_html = f'<div class="lead">{lead}</div>' if lead else ""
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="glow"></div>'
            f'<div class="tag">{tag}</div><div class="page">{n}/{total}</div><h2>{title}</h2>{lead_html}{body}'
            f'<div class="src">{src}</div></body></html>')


def rows_card(items, top=480, step=138, col="#ffc400"):
    """items: [(大きい名前, 小見出し1, 値1, 小見出し2, 値2), ...] を横長カードで縦に並べる(最大5件)。"""
    b = ""
    for i, (name, k1, v1, k2, v2) in enumerate(items):
        y = top + i * step
        b += f'<div class="card" style="top:{y}px;height:{step-20}px"></div>'
        b += f'<div style="position:absolute;top:{y+30}px;left:120px;font-size:50px;font-weight:900">{name}</div>'
        b += f'<div style="position:absolute;top:{y+20}px;left:520px;font-size:28px;color:#9bb6d9">{k1}</div>'
        b += f'<div style="position:absolute;top:{y+58}px;left:520px;font-size:38px;font-weight:900;color:{col}">{v1}</div>'
        b += f'<div style="position:absolute;top:{y+20}px;left:800px;font-size:28px;color:#9bb6d9">{k2}</div>'
        b += f'<div style="position:absolute;top:{y+58}px;left:800px;font-size:38px;font-weight:900">{v2}</div>'
    return b


def bullets(lines, top=470, size=42):
    inner = "".join(f"<div>{l}</div>" for l in lines)
    return f'<div style="position:absolute;top:{top}px;left:80px;right:80px;font-size:{size}px;line-height:1.85">{inner}</div>'


def note(text, top=960):
    return (f'<div style="position:absolute;top:{top}px;left:80px;right:80px;padding:30px 34px;border-radius:20px;'
            f'background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.12);font-size:30px;line-height:1.6;color:#cfe3ff">{text}</div>')


def render(htmls, outdir, contact=True):
    """HTMLのリストを s1.png, s2.png ... に書き出す。contact=True なら一覧画像 contact.png も作る(確認用、投稿しない)。"""
    from playwright.sync_api import sync_playwright
    out = ROOT / outdir
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path("/tmp/slides_html")
    tmp.mkdir(exist_ok=True)
    paths = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, h in enumerate(htmls, 1):
            f = tmp / f"s{i}.html"
            f.write_text(h, encoding="utf-8")
            pg.goto(f"file://{f}")
            png = out / f"s{i}.png"
            pg.screenshot(path=str(png))
            paths.append(png)
        b.close()
    if contact:
        from PIL import Image
        ims = [Image.open(x).resize((360, 450)) for x in paths]
        cols = 3
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (360 * cols, 450 * rows))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 360, (i // cols) * 450))
        sheet.save("/tmp/contact.png")
    return paths
