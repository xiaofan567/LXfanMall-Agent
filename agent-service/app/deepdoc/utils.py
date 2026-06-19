"""
deepdoc/utils.py - 通用工具函数

编码检测、文本清洗、表格提取等辅助功能。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_encoding(file_path: str | Path) -> str:
    """检测文件编码，返回编码名称。默认回退 utf-8。"""
    try:
        import chardet
        with open(file_path, "rb") as f:
            raw = f.read(100_000)  # 读取前 100KB 用于检测
        result = chardet.detect(raw)
        encoding = result.get("encoding") or "utf-8"
        logger.debug("检测到编码: %s (置信度: %.2f)", encoding, result.get("confidence", 0))
        return encoding
    except ImportError:
        logger.warning("chardet 未安装，使用默认编码 utf-8")
        return "utf-8"
    except Exception as e:
        logger.warning("编码检测失败: %s，使用 utf-8", e)
        return "utf-8"


def clean_text(text: str) -> str:
    """清洗文本：去除多余空白、控制字符等。"""
    if not text:
        return ""
    # 替换常见控制字符（保留换行和制表符）
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # 将多个连续空格压缩为单个空格（但保留换行）
    text = re.sub(r"[^\S\n]+", " ", text)
    # 去除每行首尾空格
    lines = [line.strip() for line in text.splitlines()]
    # 压缩连续空行
    result: list[str] = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                result.append("")
            prev_empty = True
        else:
            result.append(line)
            prev_empty = False
    return "\n".join(result).strip()


def extract_tables_from_text(text: str) -> list[dict]:
    """
    从纯文本中检测表格结构（基于分隔符模式）。

    返回: [{"rows": [[cell, ...], ...], "start_line": int, "end_line": int}, ...]
    """
    tables: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        # 检测表格起始：包含 | 或多个 \t 或连续多个空格分隔的行
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # 模式1: Markdown 风格表格 (| 分隔)
        if "|" in line and re.search(r"\|.*\|", line):
            table_rows: list[list[str]] = []
            start = i
            while i < len(lines):
                row = lines[i].strip()
                if not row or not ("|" in row and re.search(r"\|.*\|", row)):
                    break
                # 跳过分隔行 (|---|---|)
                if re.match(r"^[\s|:\-]+$", row):
                    i += 1
                    continue
                cells = [c.strip() for c in row.split("|")]
                # 去除首尾空元素
                if cells and not cells[0]:
                    cells = cells[1:]
                if cells and not cells[-1]:
                    cells = cells[:-1]
                if cells:
                    table_rows.append(cells)
                i += 1
            if len(table_rows) >= 2:
                tables.append({
                    "rows": table_rows,
                    "start_line": start,
                    "end_line": i - 1,
                })
            continue

        # 模式2: Tab 分隔
        if "\t" in line and line.count("\t") >= 2:
            table_rows = []
            start = i
            while i < len(lines):
                row = lines[i].strip()
                if not row or "\t" not in row:
                    break
                cells = [c.strip() for c in row.split("\t")]
                if cells:
                    table_rows.append(cells)
                i += 1
            if len(table_rows) >= 2:
                tables.append({
                    "rows": table_rows,
                    "start_line": start,
                    "end_line": i - 1,
                })
            continue

        i += 1

    return tables
