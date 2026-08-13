# -*- coding: utf-8 -*-
"""
生成「map_xml 汉化一致性检查报告」(HTML)。
数据源:
  1. check_result.json  —— 脚本结构检查(序列不一致等)
  2. 人工语义核对结论    —— 内容错位清单(嵌入下方 MISMATCH)
"""
import os, re, json, html
import xml.etree.ElementTree as ET

ROOT = r"G:/Projects/CulturesGameLocalization/Localization"
MAP_XML = os.path.join(ROOT, "map_xml")

# ================= 人工语义核对结论 =================
# 内容错位(含整体平移)文件的错位 block 清单
# 说明: _campaign_04 系列错位文件均为「CHN 丢失 GER 00_start 首段 → 后续整体错位一格」
MISMATCH = {
    "demo_singleplayer_02.xml": {
        "note": "CHN 的教程/通用文本块(00,01,04~08,10,15)与 GER 的剧情块(山谷、山贼、谈判者)错位;block 55/70 内 text[1] 与 GER text[1] 不对应(平移)。",
        "blocks": ["00", "01", "04", "05", "06", "07", "08", "10", "15", "55", "70"],
    },
    "demo_mainmenu_10.xml": {
        "note": "CHN 的教程指令块(01~07,09,10)与 GER 的剧情块(灯塔建设、流浪汉)错位;block 08 起恢复正常。",
        "blocks": ["01", "02", "03", "04", "05", "06", "07", "09", "10"],
    },
    "_campaign_04_01_sub2.xml": {
        "note": "CHN 丢失 GER 00_start 首段文本(玛尼与诺伯特进入水神庙), 之后 CHN 相对 GER 整体向前错位 2 个 block。",
        "blocks": ["00_start", "00_start1", "01", "02", "03", "500"],
    },
    "_campaign_04_01_sub3.xml": {
        "note": "CHN 丢失 GER 00_start 首段, 之后 CHN 相对 GER 整体错位 1 个 block(00_start~08), block 500 混入 50_end 内容。",
        "blocks": ["00_start", "00_start1", "01", "02", "03", "04", "05", "06", "07", "08", "500"],
    },
    "_campaign_04_02_sub2.xml": {
        "note": "CHN 丢失 GER 00_start 首段(洞中仍漆黑), 之后整体错位;block 50_end 的 CHN「干得漂亮!」与 GER「找到水晶须带给博肯扎恩」不对应。",
        "blocks": ["00_start", "00_start1", "01", "02", "03", "04", "05", "06", "50_end"],
    },
    "_campaign_04_03.xml": {
        "note": "CHN 丢失 GER 00_start 首段, 全文件 CHN 相对 GER 错位 1 个 block(00_start1~24 全部错位, 含失败块 20/24)。",
        "blocks": ["00_start1", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"],
    },
    "_campaign_04_03_sub1.xml": {
        "note": "CHN 丢失 GER 00_start 首段, 00_start~05 错位;失败块 100/200 的正文也错位(200 的正文是传送装置内容)。",
        "blocks": ["00_start", "00_start1", "01", "02", "03", "04", "05", "100", "200"],
    },
    "_campaign_04_04.xml": {
        "note": "CHN 丢失 GER 00_start 首段, 全文件错位 1 个 block(00_start~29);50_end/50_end1 亦错位(50_end=GER 50_end1 内容)。",
        "blocks": ["00_start", "00_start1", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "50_end", "50_end1"],
    },
    "_campaign_04_04_sub1.xml": {
        "note": "CHN 丢失 GER 00_start 首段, 00_start~04 错位;50_end/50_end1 错位。",
        "blocks": ["00_start", "00_start1", "01", "02", "03", "04", "50_end", "50_end1"],
    },
    "_campaign_04_04_sub2.xml": {
        "note": "CHN 丢失 GER 00_start 首段(卡巴利亚人的地牢), 00_start~09 全部错位 1 个 block。",
        "blocks": ["00_start", "00_start1", "01", "02", "03", "04", "05", "06", "07", "08", "09"],
    },
    "_campaign_04_05.xml": {
        "note": "CHN 丢失 GER 00_start 首段, 全文件错位 1 个 block(00_start~24);50_end/50_end1/50_endheader 亦错位。",
        "blocks": ["00_start", "00_start1", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "50_end", "50_end1", "50_endheader"],
    },
    "tutorial_002.xml": {
        "note": "CHN 与 GER 是两套不同内容的教程:CHN 讲职业/建筑/防御, GER 讲个体属性/婚姻/需求/英雄/狼。几乎全部 block 的 CHN 与 GER 对不上。",
        "blocks": ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"],
    },
    "tutorial_003.xml": {
        "note": "block 01(建采集站 vs 雇伐木工/采石工)、block 03 text[1](培训工人 vs 点建筑图标建农场) 内容错位;其余正常。",
        "blocks": ["01", "03"],
    },
    "tutorial_001.xml": {
        "note": "block 02(左键点蓝点弹菜单 vs 右键点建筑)、block 09(修路建桥 vs 建路标) 操作说明细节不一致;整体教学主题一致, 轻微。",
        "blocks": ["02", "09"],
    },
    "tutorial_005.xml": {
        "note": "block 10「必须先取得贸易许可证」vs GER「必须先停靠(ANDOCKEN)」翻译内容不一致;其余正常。",
        "blocks": ["10"],
    },
    "weinachten_2002.xml": {
        "note": "多数 block 的 text[1](CHN 任务目标短句) 与 GER text[1](角色对话) 不对应:02~07、10~13、17、18、100;block 00/01/08/09/14/15/16 正常。",
        "blocks": ["02", "03", "04", "05", "06", "07", "10", "11", "12", "13", "17", "18", "100"],
    },
}

# 结构问题(序列不一致)—— 从 check_result.json 读取, 生成时合并
# 内容健康但建议补 usericon/font/picture 的文件(序列不一致且不在 MISMATCH 中)

def parse(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "cp1252"):
        try:
            return ET.fromstring(raw.decode(enc))
        except Exception:
            pass
    return None


def get_block_texts(root, bid):
    """返回 (CHN文本列表, GER文本列表, CHN标签, GER标签)"""
    for b in root.findall("./briefings/block"):
        if b.get("id") != bid:
            continue
        langs = {l.get("code"): l for l in b.findall("lang")}
        cn = langs.get("CHN")
        ge = langs.get("ger")
        cn_txts = [re.sub(r"\s+", " ", t.text or "").strip()
                   for t in cn.findall("text")] if cn is not None else []
        ge_txts = [re.sub(r"\s+", " ", t.text or "").strip()
                   for t in ge.findall("text")] if ge is not None else []
        cn_tags = [c.tag for c in cn] if cn is not None else []
        ge_tags = [c.tag for c in ge] if ge is not None else []
        return cn_txts, ge_txts, cn_tags, ge_tags
    return [], [], [], []


def main():
    result = json.load(open(os.path.join(ROOT, "check_result.json"), encoding="utf-8"))
    seq_issues = {}   # fn -> {block: 缺什么}
    for fn, res in result["map_xml"].items():
        if "issues" not in res:
            continue
        seqs = {}
        for it in res["issues"]:
            if it["type"] == "子元素序列不一致":
                m = re.match(r"CHN=\[(.*?)\] ger=\[(.*?)\]", it["detail"])
                if m:
                    cn = m.group(1).replace("'", "").split(",")
                    ge = m.group(2).replace("'", "").split(",")
                    missing = sorted(set(ge) - set(cn))
                    seqs[it["id"]] = missing
        if seqs:
            seq_issues[fn] = seqs

    # ---------------- 组装 HTML ----------------
    cards = []
    # 1. 内容错位
    mismatch_files = sorted(MISMATCH.keys())
    total_mismatch_blocks = sum(len(v["blocks"]) for v in MISMATCH.values())
    for fn in mismatch_files:
        info = MISMATCH[fn]
        root = parse(os.path.join(MAP_XML, fn))
        rows = []
        for bid in info["blocks"]:
            cn_txts, ge_txts, cn_tags, ge_tags = get_block_texts(root, bid)
            cnh = "<br>".join(html.escape(t) if t else "<i>(空)</i>" for t in cn_txts) or "<i>(空)</i>"
            geh = "<br>".join(html.escape(t) if t else "<i>(空)</i>" for t in ge_txts) or "<i>(空)</i>"
            rows.append(
                '<tr><td class="bid">%s</td><td class="chn">%s</td><td class="ger">%s</td></tr>'
                % (html.escape(bid), cnh, geh)
            )
        cards.append(
            '<div class="file"><h3>%s <span class="badge">%d 个 block 错位</span></h3>'
            '<div class="note">%s</div>'
            '<table><thead><tr><th>block</th><th>CHN 中文(现)</th><th>GER 德语(基准)</th></tr></thead>'
            '<tbody>%s</tbody></table></div>'
            % (html.escape(fn), len(info["blocks"]), html.escape(info["note"]), "".join(rows))
        )
    # 2. 结构问题
    seq_cards = []
    for fn in sorted(seq_issues, key=lambda f: -len(seq_issues[f])):
        blocks = seq_issues[fn]
        bcnt = len(blocks)
        missing_cnt = sum(len(v) for v in blocks.values())
        block_list = ", ".join("%s(缺%s)" % (b, "/".join(v)) for b, v in sorted(blocks.items()))
        tag = '错位文件(需一并修复)' if fn in MISMATCH else '内容正常(仅结构)'
        seq_cards.append(
            '<div class="file"><h3>%s <span class="badge">%d block / %d 处元素缺失</span> '
            '<span class="tag">%s</span></h3><div class="note">%s</div></div>'
            % (html.escape(fn), bcnt, missing_cnt, tag, html.escape(block_list))
        )
    # 3. 健康文件
    all_files = sorted(os.listdir(MAP_XML))
    all_files = [f for f in all_files if f.endswith(".xml")]
    healthy = [f for f in all_files if f not in MISMATCH and f not in seq_issues]
    healthy_html = "<br>".join(html.escape(f) for f in healthy)

    # map_xml_user
    user_ok = "28 个文件全部通过检查(仅 5 处长度比标记, 经核对均为正常翻译的误报)。"

    page = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>map_xml 汉化一致性检查报告</title>
<style>
:root{--fg:#1f2933;--mut:#5b6572;--bg:#f7f8fa;--card:#fff;--line:#e3e8ee;
--red:#c0392b;--amber:#b7791f;--green:#1f7a4d;--blue:#1d5fa8;}
*{box-sizing:border-box}
body{font:14px/1.6 "Segoe UI","Microsoft YaHei",sans-serif;color:var(--fg);background:var(--bg);margin:0;padding:24px}
.wrap{max-width:1280px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}h2{font-size:18px;margin:36px 0 12px;border-bottom:2px solid var(--line);padding-bottom:6px}
h3{font-size:15px;margin:0 0 6px}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;min-width:150px}
.stat b{display:block;font-size:26px}.stat span{color:var(--mut);font-size:12px}
.file{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:10px 0}
.badge{display:inline-block;background:#fdecea;color:var(--red);border-radius:20px;padding:1px 10px;font-size:12px;margin-left:8px}
.badge.g{background:#e8f5ee;color:var(--green)}
.tag{font-size:11px;color:var(--amber);background:#fdf3e3;border-radius:20px;padding:1px 10px;margin-left:6px}
.note{color:var(--mut);font-size:13px;margin:4px 0 10px}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
th{background:#f0f3f7;text-align:left;padding:6px 10px;border:1px solid var(--line);position:sticky;top:0}
td{padding:6px 10px;border:1px solid var(--line);vertical-align:top}
td.bid{white-space:nowrap;font-weight:600;width:90px}
td.chn{color:var(--red);width:44%%}
td.ger{color:var(--blue);width:44%%}
.healthy{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;color:var(--mut);font-size:13px}
.sum{background:#fffbe9;border:1px solid #f0e3b8;border-radius:10px;padding:14px 16px;margin:14px 0}
code{background:#f0f3f7;padding:1px 5px;border-radius:4px;font-size:12px}
</style></head><body><div class="wrap">
<h1>🧭 map_xml / map_xml_user 汉化一致性检查报告</h1>
<div class="note">基准语言 = 德语(ger, 原版)。检查范围: 128 个 map_xml 文件 + 28 个 map_xml_user 文件(2026-08-12)。</div>

<div class="stats">
<div class="stat"><b>%d</b><span>文件存在内容错位</span></div>
<div class="stat"><b>%d</b><span>错位 block 总数</span></div>
<div class="stat"><b>%d</b><span>文件存在结构问题(缺元素)</span></div>
<div class="stat"><b>%d</b><span>结构缺失处(usericon/font/picture)</span></div>
<div class="stat"><b>%d</b><span>完全健康文件(map_xml)</span></div>
</div>

<div class="sum">✅ <b>map_xml_user(28 个)</b>: %s</div>

<h2>🔴 一、内容错位(CHN 与 GER 语义对不上)—— 必须修复</h2>
%s

<h2>🟡 二、结构问题(CHN 缺少 <code>&lt;usericon&gt;</code>/<code>&lt;font&gt;</code>/<code>&lt;picture&gt;</code> 元素)—— 游戏内头像/字体/图片不显示</h2>
%s

<h2>🟢 三、健康文件(map_xml 其余)</h2>
<div class="healthy">%s</div>

<h2>🛠 修复建议</h2>
<div class="file">
<p><b>① _campaign_04 系列整体平移错位(8 个文件)</b> —— 规律: CHN 丢失了 GER <code>00_start</code> 的首段文本(每图第一段叙述), 导致 CHN 从 <code>00_start</code> 起全部对应到 GER 的下一个 block。修复方法: 按 GER block 顺序, 将每个 block 的 CHN 文本整体<b>向后挪一个 block</b>(即 CHN[block N] ← 现 CHN[block N+1]), 并把丢失的首段重新翻译补回 <code>00_start</code>。</p>
<p><b>② demo_singleplayer_02 / demo_mainmenu_10</b> —— CHN 把「教程/通用文本」塞进了剧情 block(山谷、山贼、谈判者、灯塔、流浪汉)。需对照 GER 逐 block 重译。</p>
<p><b>③ tutorial_002</b> —— CHN 与 GER 是两套教学文案(CHN: 职业/建筑/防御; GER: 个体属性/婚姻/需求/英雄/狼), 需按 GER 重新组织 CHN 或整体重译。</p>
<p><b>④ weinachten_2002</b> —— 多数 block 的第二段(CHN 目标短句)与 GER 第二段(角色对话)对不上, 需逐 block 核对 text[1]。</p>
<p><b>⑤ 结构问题</b> —— 给 CHN 补上与 GER 一致的 <code>&lt;usericon&gt;</code>(头像)、<code>&lt;font&gt;</code>(字库)、<code>&lt;picture&gt;</code>(插图) 元素; 失败块标准结构为 <code>font,text,font,picture,text</code>。注意: 错位文件的元素缺失应随内容修复一并处理。</p>
</div>

</div></body></html>""" % (
        len(mismatch_files), total_mismatch_blocks,
        len(seq_issues), sum(len(v) for v in seq_issues.values()),
        len(healthy),
        user_ok,
        "".join(cards),
        "".join(seq_cards) or "<div class='file'>无</div>",
        healthy_html,
    )

    out_path = os.path.join(ROOT, "map_xml_汉化一致性检查报告.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print("HTML 报告已生成:", out_path)
    print("错位文件 %d 个, 错位 block %d 个; 结构问题文件 %d 个; 健康文件 %d 个"
          % (len(mismatch_files), total_mismatch_blocks, len(seq_issues), len(healthy)))


if __name__ == "__main__":
    main()
