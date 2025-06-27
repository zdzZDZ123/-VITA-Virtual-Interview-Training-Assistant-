#!/usr/bin/env python3
"""clean_api_keys.py

遍历整个项目，查找并清理常见的 API Key/Secret 字符串：
  1. OpenAI key  (sk- 开头，长度 48+)
  2. 通用 32-64 位十六进制 / base62 字符串
  3. .env 文件里的 KEY=sk-xxxxx 或 KEY=xxxxx 形式

所有匹配内容会被统一替换为占位符 `__REMOVED_API_KEY__`。

用法：
  python scripts/clean_api_keys.py  [项目根目录可选，默认为脚本所在父目录]
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable

# --- 配置 __REMOVED_API_KEY__
TEXT_FILE_EXTS: set[str] = {
    ".py", ".js", ".ts", ".tsx", ".json", ".md", ".env", ".html", ".css",
    ".yml", ".yaml", ".toml", ".ini", ".bat", ".ps1", ".sh",
}

# 正则表达式列表，匹配可能的 secret
PATTERNS: list[re.Pattern[str]] = [
    # OpenAI 风格 sk- 开头（长度 48 以上，字母数字或 "-" / "_"）
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    # 通用 token: 32-64 位 base62
    re.compile(r"[A-Za-z0-9_-]{32,64}"),
]

PLACEHOLDER = "__REMOVED_API_KEY__"

# __REMOVED_API_KEY__----

def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_FILE_EXTS


def find_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and is_text_file(p):
            yield p


def clean_file(path: Path) -> bool:
    """清理文件中的密钥，返回是否有改动"""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # 不是 utf-8 文本跳过
        return False

    original = text
    for pattern in PATTERNS:
        text = pattern.sub(PLACEHOLDER, text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"[CLEANED] {path}")
        return True
    return False


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    print(f">>> Scanning directory: {root}")

    changed = 0
    for file_path in find_files(root):
        if clean_file(file_path):
            changed += 1

    if changed:
        print(f"\n✅ 清理完成，共修改 {changed} 个文件。")
    else:
        print("\n🎉 未发现可疑 API Key，无需修改。")

    print("\n下一步： git add -A && git commit -m 'chore: clean secrets' && git push -f origin main")


if __name__ == "__main__":
    main() 