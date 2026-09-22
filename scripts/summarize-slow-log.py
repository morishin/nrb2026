#!/usr/bin/env python3
"""MySQL slow query log (long_query_time=0 で全クエリを記録した前提) を
mysqldumpslow 風にクエリ正規化して集計する。

compose.yaml の mysql サービスは --long-query-time=0 で常時ログを吐くので、
このスクリプトは「遅いクエリ検出」ではなく「クエリ種別ごとの呼び出し回数 x 時間」の
集計に使う (N+1 検出向け)。詳細: docs/bench-log-analysis.md

使い方:
    docker compose exec mysql cat /var/lib/mysql/slow.log \
        | scripts/summarize-slow-log.py [--top N]
"""
import argparse
import re
import sys
from collections import defaultdict

QUERY_TIME_RE = re.compile(r"^# Query_time: ([\d.]+)\s")
TIME_MARKER_RE = re.compile(r"^# Time: ")
USER_HOST_RE = re.compile(r"^# User@Host: ")
SET_TIMESTAMP_RE = re.compile(r"^SET timestamp=\d+;$")


def normalize(sql: str) -> str:
    sql = re.sub(r"'[^']*'", "?", sql)
    sql = re.sub(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", "?", sql)
    sql = re.sub(r"\b\d+\b", "?", sql)
    sql = re.sub(r"\s+", " ", sql).strip()
    return sql


def parse(lines):
    stats = defaultdict(lambda: {"count": 0, "total": 0.0, "max": 0.0})
    pending_time = None
    query_lines: list[str] = []

    def flush():
        nonlocal pending_time, query_lines
        if pending_time is not None and query_lines:
            sql = normalize(" ".join(query_lines))
            if sql:
                s = stats[sql]
                s["count"] += 1
                s["total"] += pending_time
                s["max"] = max(s["max"], pending_time)
        pending_time = None
        query_lines = []

    for line in lines:
        line = line.rstrip("\n")
        if TIME_MARKER_RE.match(line):
            flush()
            continue
        m = QUERY_TIME_RE.match(line)
        if m:
            pending_time = float(m.group(1))
            query_lines = []
            continue
        if USER_HOST_RE.match(line) or SET_TIMESTAMP_RE.match(line):
            continue
        if line.startswith("/usr/sbin/mysqld") or line.startswith("Tcp port:") or line.startswith("Time "):
            continue
        if pending_time is not None:
            query_lines.append(line)
    flush()
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("file", nargs="?", help="slow.log ファイルパス (省略時は stdin)")
    args = ap.parse_args()

    # 画像バイナリを bind した INSERT 等、非 UTF-8 バイト列がクエリ文に混ざりうるので
    # 置換して読み飛ばす (集計目的なので厳密なデコードは不要)。
    if args.file:
        src = open(args.file, encoding="utf-8", errors="replace")
    else:
        src = sys.stdin.buffer.read().decode("utf-8", errors="replace").splitlines(keepends=True)
    stats = parse(src)

    rows = sorted(stats.items(), key=lambda kv: kv[1]["total"], reverse=True)
    print(f"{'COUNT':>8} {'TOTAL(ms)':>12} {'AVG(ms)':>10} {'MAX(ms)':>10}  QUERY")
    for sql, s in rows[: args.top]:
        print(
            f"{s['count']:>8} {s['total'] * 1000:>12.1f} "
            f"{(s['total'] / s['count']) * 1000:>10.2f} {s['max'] * 1000:>10.2f}  {sql[:120]}"
        )


if __name__ == "__main__":
    main()
