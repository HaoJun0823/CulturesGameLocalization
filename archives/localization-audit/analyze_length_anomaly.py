# -*- coding: utf-8 -*-
"""
增强分析: 重新解析全部 XML, 对长度比异常项输出完整 CHN/GER 对照,
并做跨文件/跨 block 的 CHN 文本查重(内容错位的强证据)。
"""
import os, re, json, difflib
import xml.etree.ElementTree as ET

ROOT = r"G:/Projects/CulturesGameLocalization/Localization"
DIRS = ["map_xml", "map_xml_user"]
GER_UMLAUT = re.compile(r"[äöüÄÖÜß]")

def parse_file(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "cp1252", "latin-1"):
        try:
            return ET.fromstring(raw.decode(enc)), None
        except UnicodeDecodeError:
            continue
        except ET.ParseError as e:
            return None, str(e)
    return None, "decode fail"

def norm(s):
    return re.sub(r"\s+", "", s or "")

def collect_all():
    """返回 {sub: {relpath: {'strings': {...}, 'blocks': {...}, 'issues_len': [...]}}}"""
    all_data = {}
    all_texts = []  # (norm_text, sub, file, kind, id, idx)
    for sub in DIRS:
        base = os.path.join(ROOT, sub)
        all_data[sub] = {}
        for cur, _s, files in os.walk(base):
            for fn in sorted(files):
                if not fn.lower().endswith(".xml"):
                    continue
                path = os.path.join(cur, fn)
                rel = os.path.relpath(path, base).replace("\\", "/")
                root, err = parse_file(path)
                if err:
                    all_data[sub][rel] = {"error": err}
                    continue
                strings, blocks = {}, {}
                for s_el in root.findall("./strings/string"):
                    sid = s_el.get("id", "")
                    strings[sid] = {t.get("lang", ""): (t.text or "") for t in s_el.findall("text")}
                for b_el in root.findall("./briefings/block"):
                    bid = b_el.get("id", "")
                    langs = {}
                    for l_el in b_el.findall("lang"):
                        code = l_el.get("code", "")
                        seq = [(c.tag, c.text or "") for c in l_el]
                        langs[code] = seq
                    blocks[bid] = langs
                all_data[sub][rel] = {"strings": strings, "blocks": blocks}
                # 索引 CHN 文本
                for sid, t in strings.items():
                    cn = norm(t.get("CHN", ""))
                    if len(cn) >= 8:
                        all_texts.append((cn, sub, rel, "string", sid, None))
                for bid, langs in blocks.items():
                    if "CHN" not in langs:
                        continue
                    for k, (tp, tx) in enumerate(langs["CHN"]):
                        if tp == "text":
                            cn = norm(tx)
                            if len(cn) >= 8:
                                all_texts.append((cn, sub, rel, "block", bid, k))
    return all_data, all_texts

def find_dup(cn, all_texts, self_key):
    """在索引中找与 cn 高度相似的 CHN 文本(排除自身位置), 返回最相似的候选列表。"""
    cands = []
    for (t, sub, rel, kind, id_, idx) in all_texts:
        if (sub, rel, kind, id_, idx) == self_key:
            continue
        if t == cn:
            ratio = 1.0
        else:
            if len(t) < 8 or len(cn) < 8:
                continue
            s = difflib.SequenceMatcher(None, cn, t, autojunk=False)
            ratio = s.ratio()
        if ratio >= 0.80:
            cands.append((ratio, sub, rel, kind, id_, idx))
    cands.sort(key=lambda x: -x[0])
    return cands[:3]

def main():
    all_data, all_texts = collect_all()
    out = []
    dup_stats = {"A_dup_found": 0, "no_dup": 0}
    for sub in DIRS:
        out.append("\n" + "#" * 100)
        out.append("# 目录: %s" % sub)
        out.append("#" * 100)
        for rel in sorted(all_data[sub]):
            data = all_data[sub][rel]
            if "error" in data:
                out.append("\n### [PARSE_ERROR] %s : %s" % (rel, data["error"]))
                continue
            strings, blocks = data["strings"], data["blocks"]
            issues = []
            # 长度比异常(完整收集,含短文本豁免调整)
            for sid, t in strings.items():
                if "CHN" in t and "ger" in t:
                    cn, ge = norm(t["CHN"]), norm(t["ger"])
                    if cn and ge and not (len(cn) <= 6 and len(ge) <= 40):
                        r = len(cn) / len(ge)
                        if r < 0.20 or r > 1.10:
                            issues.append(("string", sid, None, t["CHN"], t["ger"], r))
            for bid, langs in blocks.items():
                if "CHN" not in langs or "ger" not in langs:
                    continue
                cn_seq = [t for tp, t in langs["CHN"] if tp == "text"]
                ge_seq = [t for tp, t in langs["ger"] if tp == "text"]
                n = min(len(cn_seq), len(ge_seq))
                for k in range(n):
                    cn, ge = norm(cn_seq[k]), norm(ge_seq[k])
                    if cn and ge and not (len(cn) <= 6 and len(ge) <= 40):
                        r = len(cn) / len(ge)
                        if r < 0.20 or r > 1.10:
                            issues.append(("block", bid, k, cn_seq[k], ge_seq[k], r))
            if not issues:
                continue
            out.append("\n### %s" % rel)
            for kind, id_, idx, cn_txt, ge_txt, r in issues:
                # 查重
                key = (sub, rel, kind, id_, idx)
                dup = find_dup(norm(cn_txt), all_texts, key)
                loc = "%s %s" % (kind, id_)
                if idx is not None:
                    loc += " text[%d]" % idx
                cn1 = re.sub(r"\s+", " ", cn_txt).strip()
                ge1 = re.sub(r"\s+", " ", ge_txt).strip()
                out.append("  --- %s ratio=%.2f" % (loc, r))
                out.append("      CHN: %s" % cn1)
                out.append("      GER: %s" % ge1)
                if dup:
                    dup_stats["A_dup_found"] += 1
                    d0 = dup[0]
                    out.append("      >>> 相似CHN文本: %s/%s %s %s (sim=%.2f)" %
                               (d0[1], d0[2], d0[3], d0[4], d0[0]))
                else:
                    dup_stats["no_dup"] += 1
    text = "\n".join(out)
    with open("length_anomaly_full.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("输出: length_anomaly_full.txt, 共 %d 行" % len(out))
    print("查重统计:", dup_stats)

if __name__ == "__main__":
    main()
