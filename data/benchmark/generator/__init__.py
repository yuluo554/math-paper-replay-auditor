"""生成器入口。"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from .truth_builder import generate_all


def main(output_dir: str = "data/benchmark", min_per_type: int = 3, clean_count: int = 3) -> None:
    """生成全部合成论文样本与真值台账。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    result = generate_all(out, min_per_type=min_per_type, clean_count=clean_count)

    # 落盘真值台账
    (out / "truth.json").write_text(
        json.dumps(result["truth"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 落盘 manifest
    (out / "manifest.json").write_text(
        json.dumps(result["manifest"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Generated {result['manifest']['total_samples']} samples")


if __name__ == "__main__":
    import json
    main(*sys.argv[1:])
