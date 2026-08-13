import shutil
from pathlib import Path

SRC = Path(r"G:\Projects\Cultures_Saga_Remix\Gates of Asgard\data\maps")
DST = Path(r"G:\Projects\CulturesGameLocalization\OfficalMaps")

total = 0
for map_dir in SRC.iterdir():
    if not map_dir.is_dir():
        continue
    eng_dir = map_dir / "sfx" / "eng"
    if not eng_dir.is_dir():
        continue
    wavs = sorted(eng_dir.glob("*.wav"))
    if not wavs:
        continue
    tdir = DST / map_dir.name / "sfx" / "eng"
    if not DST.joinpath(map_dir.name).is_dir():
        print(f"[MISS] target map dir missing for {map_dir.name}; skip")
        continue
    tdir.mkdir(parents=True, exist_ok=True)
    for w in wavs:
        shutil.copy2(w, tdir / w.name)
        total += 1
    print(f"[OK] {map_dir.name}: {len(wavs)} wav -> {tdir}")

print(f"\nTOTAL_COPIED={total}")
