# -*- coding: utf-8 -*-
"""
一键复现脚本（Run All）
用法：python run_all.py            # 全流程
      python run_all.py s3 s5      # 只跑指定步骤
每步均可独立执行，中间结果全部落盘，便于检查与调试。
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = [
    ("s0", "s0_generate_corpus.py", "Step 0 语料与仿真数据生成（预演用）"),
    ("s1", "s1_clean.py", "Step 1 文本清洗"),
    ("s2", "s2_tokenize.py", "Step 2 中文分词与关键词计数"),
    ("s3", "s3_measure.py", "Step 3 测度构建与信效度检验"),
    ("s4", "s4_panel.py", "Step 4 面板构建与描述性统计"),
    ("s5", "s5_model.py", "Step 5 回归与异质性分析"),
]


def main():
    want = [a for a in sys.argv[1:]] or [k for k, _, _ in STEPS]
    t0 = time.time()
    for key, script, desc in STEPS:
        if key not in want:
            continue
        print("=" * 78)
        print(f"▶ {desc}  ({script})")
        print("=" * 78)
        r = subprocess.run([sys.executable, str(HERE / script)], cwd=str(HERE),
                           env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        if r.returncode != 0:
            print(f"✗ {script} 执行失败，流程终止")
            sys.exit(r.returncode)
    print("=" * 78)
    print(f"✔ 全流程完成，用时 {time.time() - t0:.1f} 秒。"
          f"\n  面板数据：data/panel_firm_year.csv (xlsx)"
          f"\n  结果表：  output/tables/")


if __name__ == "__main__":
    main()
