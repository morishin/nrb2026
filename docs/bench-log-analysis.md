# ローカルでベンチを回してボトルネックを見る

ISUCON の定番の流れ (ベンチ走行 → アプリログ / スロークエリログ分析 → ボトルネック特定) を
ローカルでも再現するための手順。前提: [README.md](../README.md) の「ローカルで起動する」を
先に済ませておくこと。

## 1. webapp をログ付きで起動する

webapp には `tower_http::trace::TraceLayer` が仕込んであり、リクエストごとに
`method` / `uri` / `status` / `latency` を INFO レベルでログ出力する
(`webapp/src/main.rs`)。ログを後で集計できるようファイルにも保存しておく:

```sh
DATABASE_URL=mysql://isucon:isucon@127.0.0.1:3307/nrb2026 \
  cargo run --manifest-path webapp/Cargo.toml 2>&1 | tee /tmp/webapp.log
```

`RUST_LOG` 環境変数でログレベルを変更できる (デフォルト `info,tower_http=info`)。

## 2. MySQL のスロークエリログ

`compose.yaml` の mysql サービスは `--long-query-time=0` で常時ログを吐く設定にしてある
(= 実質的に全クエリログ。閾値を上げて本当に遅いものだけ見たい場合は compose.yaml を編集して
コンテナを再作成する)。

```sh
# 設定変更を反映させたい場合のみ (通常は起動したままでよい)
docker compose up -d --force-recreate mysql
```

## 3. bench を回す

```sh
scripts/dev-bench.sh
```

`build/dev-report.json` にスコアが出力される。webapp のログファイル (`/tmp/webapp.log` 等)
にはこの走行中のリクエストログが溜まっている。

## 4. 集計する

### アプリ側 (エンドポイント別レイテンシ)

```sh
scripts/summarize-latency.sh /tmp/webapp.log
```

`METHOD PATH COUNT AVG_MS MAX_MS` を平均レイテンシ降順で表示する。呼び出し回数 × 平均
レイテンシが大きいエンドポイントが総処理時間への寄与が大きい。

### DB 側 (クエリ種別ごとの呼び出し回数 / 合計時間)

`mysqldumpslow` / `pt-query-digest` は今回の Docker イメージには同梱されていないため、代わりに
`scripts/summarize-slow-log.py` を使う (クエリのリテラルを正規化してクエリ種別ごとに
count/total/avg/max を集計する、mysqldumpslow 風のツール):

```sh
docker compose exec mysql cat /var/lib/mysql/slow.log \
  | scripts/summarize-slow-log.py --top 20
```

count が異常に多いクエリ (例: 60 秒の走行で 10 万回超) は N+1 の強いシグナル。

## 実例 (初期実装、N+1 修正前)

`GET /api/campaigns` が呼び出し回数・平均レイテンシともに突出して大きく (avg 約 70ms,
呼び出し全体の 3 割超)、DB 側では `hydrate_campaign` 内の 3 クエリ
(`campaigns` / `campaign_tags` / `campaign_participants` の SELECT) がそれぞれ
13 万回以上実行されていた。`list_campaigns` (`webapp/src/main.rs`) が
`SELECT id FROM campaigns` で全件 ID を取得したあと 1 件ずつ `hydrate_campaign` を呼ぶ
構造になっており、典型的な N+1 だった。
