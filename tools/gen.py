# -*- coding: utf-8 -*-
"""Generate TENSON caption page from works.json (extracted from worklist xlsx)."""
# TODO(2026-07-29): このスクリプトは現状そのままでは動かない。
#   1) 入力パス SP は使い捨てのスクラッチ領域で、既に消滅している。works.json /
#      template.html / site/ をリポジトリ内に移すか、パスを引数化する必要がある。
#   2) 下の SECTIONS は 260722 より前の番号体系（1–116）をハードコードしており、
#      公開中の index.html（260722版 1–118）とは一致しない。番号は data_works.json
#      の num フィールドに 260722 版を入れてあるので、そちらを正とすること。
#   3) index.html には AR帯・年表帯・会場ギャラリー・相互リンクなど手作業で足した
#      資産があり、このスクリプトで再生成するとそれらが消える。修正は index.html を
#      直接触るのが現状の運用（ルートB）。
import json, html, re

SP = '/private/tmp/claude-501/-Users-yoichiochiai/fc782a78-cb18-4783-a0d9-8bc5dcf9e565/scratchpad'
works = json.load(open(f'{SP}/works.json'))
by = {w['row']: w for w in works}
rows_sorted = sorted(by.keys())

def resolve_desc(row, key):
    """Walk up rows while desc == 上と同じ."""
    i = rows_sorted.index(row)
    while i >= 0:
        d = by[rows_sorted[i]][key].strip()
        if d and d != '上と同じ' and d != 'まだ思いついていない':
            return d
        i -= 1
    return ''

def clean_year(y):
    y = str(y).strip()
    if y.endswith('.0'): y = y[:-2]
    if y == '新作': y = '2026'
    return y

def clean_mat(m):
    return re.sub(r'\s*\n\s*', ', ', m.strip())

# entry: (num_label, [rows], overrides dict)
E = lambda n, r, **kw: dict(num=n, rows=r, **kw)
SECTIONS = [
    ('A', '1階 — 入口 / 1st Floor — Entrance', [
        E('1', [7], subitems=list(range(8, 27))),
        E('2', [63]),
    ]),
    ('B', '1階 / 1st Floor', [
        E('3', [27]), E('4', [64]), E('5', [28]), E('6', [35]),
        E('7', [80], no_desc=False),
        E('8', [98]), E('9', [33]), E('10', [99]), E('11', [30]),
        E('12', [34]), E('13', [65]),
    ]),
    ('C', '1階 / 1st Floor', [
        E('14–17', [83,84,85,86], tj='木化する波 #1, 3, 7, 8 − 中性 −', te='Woodized Waves #1, 3, 7, 8 – neutral –'),
        E('18–20', [87,88,89], tj='木化する波 #2, 5, 7 − 黒 −', te='Woodized Waves #2, 5, 7 – noct –'),
        E('21–25', [90,91,92], tj='借景するガラス，結晶化する波 #5, 6, 7', te='Borrowed Landscape Glass, Crystallizing Waves #5, 6, 7'),
        E('26, 27', [81,82], tj='木化する波 #4, 6 − 鏡 −', te='Woodized Waves #4, 6 – mirror –'),
        E('28–30', [78,79,80], tj='銀口魚 再物化する波 Ⅰ, Ⅱ, Ⅲ', te='Re-Materialization Waves "Silver Mouse Fish Ⅰ, Ⅱ, Ⅲ"'),
        E('31–33', [75,76,77], tj='銀口魚の変換過程 Ⅰ, Ⅱ, Ⅲ', te='Transformation Process of Silver Mouse Fish Ⅰ, Ⅱ, Ⅲ'),
        E('34', [36]),
        E('35', [68], tj='帰郷するシンギュラリティ，饗宴するコンヴィヴィアリティ：神人共食，天孫送宴',
          te='The Singularity Heads Home, Conviviality Holds the Feast: Commensality of Gods and Humans, a Farewell Banquet for the Tenson',
          year='2026', mat='teenagesスピーカー, PC, 生成AI'),
        E('36', [69]), E('37', [70]),
        E('38', [71], year='2026'),  # desc is placeholder -> auto-dropped
        E('39, 40', [72,73,74], tj='円環に帰す炭素 / リミックス / DJ Carbon Ⅰ, Ⅱ, Ⅲ',
          te='Emotion: Returning to the Repeating Cycle / Remix / DJ Ⅰ, Ⅱ, Ⅲ'),
        E('41', [94]), E('42', [96]), E('43', [95]), E('44', [108]),
        E('45', [102]), E('46', [107]), E('47', [105]), E('48', [101]),
        E('49', [100]), E('50', [104]), E('51', [103]),
    ]),
    ('D', '1階 / 1st Floor', [
        E('52', [110], note_ja='＊受話器を上げてください', note_en='* Pick up the handset'),
        E('53', [93]), E('54', [113]), E('55', [111]), E('56', [112]),
        E('57–59', [132], tj='計算期自然の微睡み，潜在空間の夢 Ⅰ–Ⅲ', te='Slumber of Digital Nature, Dreams of Latent Spaces Ⅰ–Ⅲ'),
        E('60', [129]), E('61', [128], year='2026'),
        E('62–74', list(range(37,50)), tj='象徴と変転 − 十三支 / 子, 丑, とら, 卯, 辰, 未, へび, 午, さる, 酉, 戌, 亥, 貓',
          te='Symbols and Transmutations – Thirteen Branches: Rat, Ox, Tiger, Rabbit, Dragon, Sheep, Snake, Horse, Monkey, Bird, Dog, Boa, Cat'),
        E('75–87', list(range(50,63)), tj='ﾇﾙ即是十三支 / 子, 丑, とら, 卯, 辰, 未, へび, 午, さる, 酉, 戌, 亥, 貓，生命の版木，計算機は浮世の夢を見る',
          te='Null is the Thirteen Signs: Rat, Ox, Tiger, Rabbit, Dragon, Sheep, Snake, Horse, Monkey, Bird, Dog, Boa, Cat — Woodblock of Life, Computation Dreams of Ukiyo'),
        E('88', [130]), E('89', [131]),
        E('90', [117], credit='協力：鹿児島県立埋蔵文化財センター'),
        E('91', [115], credit='協力：日置島津家・吉冨山大乗寺跡管理人 西郷隆文'),
        E('92', [119], credit='協力：鹿児島県立埋蔵文化財センター'),
        E('93', [118], credit='協力：鹿児島県立埋蔵文化財センター'),
        E('94', [116], credit='協力：郡山八幡神社'),
        E('95', [114]),
        E('96', [123], credit='協力：鹿児島県立埋蔵文化財センター，小澤知夏'),
        E('97', [120], credit='協力：霧島神宮，小澤知夏'),
        E('98', [125], credit='協力：小澤知夏'),
        E('99', [127], credit='協力：小澤知夏'),
        E('100', [124], credit='協力：小澤知夏'),
        E('101', [122], credit='協力：小澤知夏'),
        E('102', [121], credit='協力：小澤知夏'),
        E('103', [126], credit='協力：日新育成会，小澤知夏'),
        E('104', [133]),
    ]),
    ('E', '2階 / 2nd Floor', [
        E('105', [109]), E('106', [134]), E('107', [135]), E('108', [97]),
        E('109', [137]), E('110', [136]), E('111', [138]), E('112', [139]),
    ]),
    ('D2', '1階 D（続き）/ 1st Floor D (cont.)', [
        E('113', [106]), E('114', [140]),
    ]),
    ('F', '1階 — 出口 / 1st Floor — Exit', [
        E('115', [32]),
        E('116', [141], tj='天孫帰るってよ？に至るまで', te='',
          note_ja='制作映像ドキュメント', note_en='Documentary of the making'),
    ]),
]

esc = lambda s: html.escape(s, quote=False)
def para(s):
    s = esc(s.strip())
    return ''.join(f'<p>{p.strip()}</p>' for p in re.split(r'\n\s*\n|\n', s) if p.strip())

cards = []
for sec_id, sec_label, entries in SECTIONS:
    anchor = 'sec' + sec_id
    label_ja, _, label_en = sec_label.partition(' / ')
    cards.append(f'<section class="zone" id="{anchor}"><div class="zone-head"><span class="zone-letter">{sec_id[0]}</span><span class="zone-name"><span class="ja">{esc(label_ja)}</span><span class="en">{esc(label_en)}</span></span></div>')
    for e in entries:
        r0 = e['rows'][0]
        w = by[r0]
        tj = e.get('tj', w['title_ja'])
        te = e.get('te', w['title_en'])
        if te == tj or te in ('-', ''): te = e.get('te', '') if 'te' in e else ''
        year = e.get('year', clean_year(w['year']))
        mat = e.get('mat', clean_mat(w['material']))
        credit = e.get('credit', w['credit'].strip())
        dj = resolve_desc(r0, 'desc_ja') if w['desc_ja'].strip() not in ('', 'まだ思いついていない') or w['desc_ja'].strip()=='上と同じ' else ''
        de = resolve_desc(r0, 'desc_en') if dj else ''
        if w['desc_ja'].strip() == 'まだ思いついていない': dj = de = ''
        if w['desc_ja'].strip() == '': dj = de = ''
        numid = 'n' + e['num'].split('–')[0].split(',')[0].strip()
        meta = ' ｜ '.join(x for x in [year, mat] if x)
        h = [f'<article class="work" id="{numid}">']
        h.append(f'<div class="wnum">{e["num"]}</div>')
        h.append('<div class="wbody">')
        h.append(f'<h3 class="tj">{esc(tj)}</h3>')
        if te: h.append(f'<div class="te">{esc(te)}</div>')
        if meta: h.append(f'<div class="meta">{esc(meta)}</div>')
        if credit:
            credit_disp = re.sub(r'\s*\n\s*', '<br>', esc(credit))
            h.append(f'<div class="credit">{credit_disp}</div>')
        if e.get('note_ja'):
            h.append(f'<div class="note"><span class="ja">{esc(e["note_ja"])}</span><span class="en">{esc(e["note_en"])}</span></div>')
        if dj: h.append(f'<div class="desc ja">{para(dj)}</div>')
        if de: h.append(f'<div class="desc en">{para(de)}</div>')
        # sub items (timeline vitrine under no.1)
        if e.get('subitems'):
            h.append('<div class="subs"><div class="subs-title"><span class="ja">年表をかたちづくる資料</span><span class="en">Objects Composing the Chronicle</span></div>')
            for sr in e['subitems']:
                sw = by.get(sr)
                if not sw or not sw['title_ja']: continue
                stj, ste = sw['title_ja'], sw['title_en']
                sdj, sde = sw['desc_ja'].strip(), sw['desc_en'].strip()
                h.append('<div class="sub">')
                h.append(f'<div class="sub-t"><span class="ja">{esc(stj)}</span>' + (f'<span class="en">{esc(ste)}</span>' if ste and ste != stj else '') + '</div>')
                if sdj: h.append(f'<div class="sub-d ja">{esc(sdj)}</div>')
                if sde and sde != sdj: h.append(f'<div class="sub-d en">{esc(sde)}</div>')
                h.append('</div>')
            h.append('</div>')
        h.append('</div></article>')
        cards.append('\n'.join(h))
    cards.append('</section>')

body_works = '\n'.join(cards)

page = open(f'{SP}/template.html', encoding='utf8').read()
page = page.replace('<!--WORKS-->', body_works)
open(f'{SP}/site/index.html', 'w', encoding='utf8').write(page)
print('written', len(body_works))
