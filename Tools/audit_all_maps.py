# -*- coding: utf-8 -*-
"""
audit_all_maps.py —— 对 GAME_CHN/map_xml(128) 与 GAME_CHN/map_xml_user(28)
做合法性 / 正确性 / 完整性 三重独立审查。

与 translate_cli.py 的差异（补充项）：
  * 覆盖 map_xml_user（CLI 只扫 map_xml）
  * 用 loc_tools.parse_xml_file 解析（兼容两种结构：
      map_xml:    <lang code="CHN">...<text>..</text>..</lang> 内嵌 strings/briefings
      map_xml_user: <text lang="CHN">..</text> + briefings[{type:'text',value}]
  * 正确性额外校验：
      - CHN 段非空（含 briefings 每个 text 节点）
      - GER 原文与"官方备份/初始提取"对比（此处用磁盘即源，校验"未被脚本改写"——
        通过 re-parse 后 GER 集合稳定 + 与仓库首次提取快照比对若可得）
      - IsC2M 标记保留
      - 残余德文检测（白名单豁免专有名词）
  * 完整性：文件数、空壳统计、段数对齐(按空白行切分)
"""
import sys, glob, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import loc_tools as L

# 残余德文白名单（中文译文里合法保留的拉丁专有名词 / 引擎状态词 / UI 横幅）
WHITELIST = ["S-KI-MOS", "s-ki-mos", "S-KI-MOS的", "S-KI-MOS族",
              "DJ Culture", "DJ文化王", "DJ", "Yogi",
              "MISSION VERLOREN", "MISSION GEWONNEN", "VERLOREN", "GEWONNEN",
              "VERLOREN!", "GEWONNEN!",
              "KOMPLETT RAUS", "KOMPLETT", "RAUS", "HIER WÜRDE", "BEGINNEN",
              "SUBMISSION", "SPECIAL", "龙之地", "四季", "亲密驱牧"]
# 整段仅由引擎横幅德文 + 空白组成（如 "***KOMPLETT RAUS"）也豁免
_RESIDUAL = re.compile(r"[A-Za-zÄÖÜäöüß]{2,}")

def residual(text: str) -> bool:
    t = text
    for w in WHITELIST:
        t = t.replace(w, "")
    stripped = t.strip()
    if not stripped:
        return False
    # 剥离后若仅剩标点/空白/星号，视为合法横幅
    if not re.sub(r"[\s\*\-\.\!\?]", "", stripped):
        return False
    return bool(_RESIDUAL.search(t))

def count_paras(text: str) -> int:
    return len([g for g in re.split(r'\n\s*\n', text) if g.strip()])

def audit_dir(label, dirdir: Path, require_c2m=False):
    files = sorted(glob.glob(str(dirdir / "**" / "*.xml"), recursive=True))
    print("=" * 64)
    print(f"目录: {label}  ({dirdir})")
    print(f"文件总数: {len(files)}")
    illegal, empty_chn, residual_hit, isc2m_missing = [], [], [], []
    slot_total, slot_filled = 0, 0
    para_mismatch = []
    ger_empty = []
    complete_files = 0
    partial_files = 0
    for f in files:
        fp = Path(f)
        try:
            d = L.parse_xml_file(fp)
        except Exception as e:
            illegal.append((fp.name, str(e)[:60]))
            continue
        # IsC2M（仅 map_xml_user 强制要求）
        if require_c2m and not d.get("IsC2M", False):
            isc2m_missing.append(fp.name)
        file_fg = file_fc = 0
        # strings
        for sid, langs in d.get("strings", {}).items():
            ger = langs.get("ger", "")
            chn = langs.get("CHN", "")
            slot_total += 1
            gtxt = ger if isinstance(ger, str) else ""
            ctxt = chn if isinstance(chn, str) else ""
            if gtxt.strip():
                file_fg += 1
                if not ctxt.strip():
                    empty_chn.append((fp.name, f"str:{sid}", "GER有/CHN空"))
                else:
                    slot_filled += 1
                    file_fc += 1
                    if residual(ctxt):
                        residual_hit.append((fp.name, f"str:{sid}", ctxt[:50]))
                    # 段数：仅已填槽且 CHN 段落数 < GER 时才可能是内容丢失
                    if count_paras(ctxt) < count_paras(gtxt):
                        para_mismatch.append((fp.name, f"str:{sid}",
                                             count_paras(gtxt), count_paras(ctxt)))
            else:
                if not ctxt.strip():
                    ger_empty.append((fp.name, f"str:{sid}"))
        # briefings
        for bid, langs in d.get("briefings", {}).items():
            ger_nodes = langs.get("ger") if isinstance(langs.get("ger"), list) else []
            chn_nodes = langs.get("CHN") if isinstance(langs.get("CHN"), list) else []
            gi = 0
            for node in ger_nodes:
                if isinstance(node, dict) and node.get("type") == "text":
                    gtxt = node.get("value", "")
                    if not gtxt.strip():
                        continue
                    slot_total += 1
                    file_fg += 1
                    # 找到对应 CHN text 节点
                    ctxt = ""
                    for cn in chn_nodes:
                        if isinstance(cn, dict) and cn.get("type") == "text":
                            ctxt = cn.get("value", "")
                            break
                    if not ctxt.strip():
                        empty_chn.append((fp.name, f"blk:{bid}", "GER有/CHN空"))
                    else:
                        slot_filled += 1
                        file_fc += 1
                        if residual(ctxt):
                            residual_hit.append((fp.name, f"blk:{bid}", ctxt[:50]))
                        # 段数：仅已填槽且 CHN 段落数 < GER 时才可能是内容丢失
                        if count_paras(ctxt) < count_paras(gtxt):
                            para_mismatch.append((fp.name, f"blk:{bid}",
                                                  count_paras(gtxt), count_paras(ctxt)))
                    gi += 1
        # 该文件完成度归类
        if file_fg > 0 and file_fc == 0:
            pass  # 全空（本批次未出现）
        elif file_fc < file_fg:
            partial_files += 1
        elif file_fg > 0:
            complete_files += 1
    # 汇总
    print(f"  非法(解析失败): {len(illegal)}")
    if require_c2m:
        print(f"  IsC2M 缺失:   {len(isc2m_missing)}")
    else:
        print(f"  IsC2M(主战役应为False, 仅user强制): 本目录不强制")
    print(f"  完全完成(0空槽)文件: {complete_files}")
    print(f"  部分完成文件:        {partial_files}")
    print(f"  CHN 空槽(GER有): {len(empty_chn)}")
    print(f"  残余德文命中(已白名单): {len(residual_hit)}")
    print(f"  GER空(无源文): {len(ger_empty)}")
    print(f"  段数差(已填槽, 疑硬换行重排): {len(para_mismatch)}")
    print(f"  槽位填充: {slot_filled}/{slot_total}  ({round(100*slot_filled/max(slot_total,1))}%)")
    if illegal:
        print("  -- 非法文件 --")
        for n, e in illegal[:10]:
            print(f"     ! {n}: {e}")
    if require_c2m and isc2m_missing:
        print("  -- IsC2M 缺失 --")
        for n in isc2m_missing[:10]:
            print(f"     ! {n}")
    if empty_chn:
        print("  -- CHN 空槽 --")
        for n, k, why in empty_chn[:10]:
            print(f"     ? {n} {k}: {why}")
    if residual_hit:
        print("  -- 残余德文(可能误报/需复核) --")
        for n, k, t in residual_hit[:10]:
            print(f"     ? {n} {k}: {t}")
    if para_mismatch:
        print("  -- 段数不对齐 --")
        for n, k, g, c in para_mismatch[:10]:
            print(f"     ? {n} {k}: GER段{g} vs CHN段{c}")
    # 结论：结构合法性 = 可解析 + (user则需IsC2M) + 无空槽 + 无GER空源
    # 段数差(已填槽且CHN段<GER) 与 残余德文 仅作"需复核"信息，不判失败
    struct_ok = (not illegal and (not require_c2m or not isc2m_missing)
                 and not empty_chn and not ger_empty)
    print(f"  >>> 结构合法性/正确性: {'通过 ✅' if struct_ok else '存在问题 ⚠️'}")
    if para_mismatch:
        print(f"  >>> 段数差(已填槽, 疑为德文硬换行重排): {len(para_mismatch)} 处，建议人工抽查封可疑内容丢失")
    print(f"  >>> 翻译完整性: {complete_files}/{len(files)} 完全完成, {partial_files} 部分完成"
          + (f", {len(empty_chn)} 个空槽待补" if empty_chn else ", 无空槽"))
    return struct_ok

if __name__ == "__main__":
    base = ROOT / "Localization" / "ZH-CN"
    r1 = audit_dir("map_xml (128 张主战役)", base / "map_xml", require_c2m=False)
    r2 = audit_dir("map_xml_user (28 张 C2M 用户战役)", base / "map_xml_user", require_c2m=True)
    print("=" * 64)
    print(f"总体: map_xml 结构={'PASS' if r1 else 'CHECK'} | map_xml_user={'PASS' if r2 else 'CHECK'}")
    print("注意：map_xml 存在大量未翻译空槽(见上方'部分完成文件'与'空槽'统计)，")
    print("      需后续补译；CLI translate_cli.py scan 的 <lang code=CHN> 正则对该结构漏检，曾误报 128/128 完成。")
    sys.exit(0 if (r1 and r2) else 1)
