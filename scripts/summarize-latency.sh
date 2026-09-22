#!/usr/bin/env bash
# webapp の tracing ログ (tower_http::trace, webapp/src/main.rs 参照) からエンドポイント別に
# リクエスト数・平均レイテンシ・最大レイテンシを集計する。
#
# 使い方:
#   cargo run --manifest-path webapp/Cargo.toml 2>&1 | tee /tmp/webapp.log
#   (別ターミナルで bench を走らせたあと)
#   scripts/summarize-latency.sh /tmp/webapp.log
#
# 詳細: docs/bench-log-analysis.md
set -euo pipefail

LOG="${1:?usage: summarize-latency.sh <webapp-log-file>}"

# ANSI カラーコードを除去し、method/uri/latency を取り出して集計する。
# uri 中の UUID は :id に正規化してエンドポイント単位でまとめる。
sed -E 's/\x1b\[[0-9]*m//g' "$LOG" \
    | grep "finished processing request" \
    | grep -oE "method=[A-Z]+ uri=[^ ]+.*latency=[0-9]+ ms" \
    | sed -E 's#method=([A-Z]+) uri=([^ ]+).*latency=([0-9]+) ms#\1 \2 \3#' \
    | sed -E 's#/api/campaigns/[0-9a-fA-F-]{36}#/api/campaigns/:id#' \
    | awk '{
        key = $1"\t"$2
        sum[key] += $3
        n[key]++
        if ($3 > max[key]) max[key] = $3
      }
      END {
        for (k in n) printf "%s\t%d\t%.1f\t%d\n", k, n[k], sum[k] / n[k], max[k]
      }' \
    | sort -t $'\t' -k3 -rn \
    | (printf "METHOD\tPATH\tCOUNT\tAVG_MS\tMAX_MS\n"; cat) \
    | column -t -s $'\t'
