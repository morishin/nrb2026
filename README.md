# nrb2026 — ISUNARABE 合同演習2026

ISUNARABE 合同演習2026を対象としてGitHub Actions で継続的にベンチマークを実行するためのリポジトリです。

## クイックスタート

1. `gh repo fork matsuu/nrb2026 --clone`
2. KAIZEN
3. git commit
4. git push
5. GitHub Actions ベンチマーク結果を確認
6. 2-5 を繰り返す

## ローカルで起動する

ブラウザで動作を確認しながら開発する場合の最短手順。

前提: Docker (Rancher Desktop 等) / Rust ([rust-toolchain.toml](rust-toolchain.toml) で pin 済み) / Node.js + pnpm。

```sh
# 1. MySQL を起動 (Docker Desktop 等が起動していること)
docker compose up -d mysql

# 2. webapp を起動 (別ターミナル、初回はビルドで数分かかる)
DATABASE_URL=mysql://isucon:isucon@127.0.0.1:3307/nrb2026 \
  cargo run --manifest-path webapp/Cargo.toml
# -> http://127.0.0.1:8080 で待受

# 3. DB を初期化 (webapp 起動後に 1 回。フロントに initialize UI は無いので curl で叩く)
curl -X POST http://127.0.0.1:8080/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"notification_webhook_url":"http://127.0.0.1:8090/webhook"}'
# notification_webhook_url は動かなくても initialize 自体は通る。
# 実際にプッシュ通知の受信まで見たい場合は docs/manual.md § 5.4 の簡易 receiver を先に立てる。

# 4. frontend を起動 (別ターミナル)
cd frontend
pnpm install
pnpm dev
# -> http://localhost:5173 (vite dev server が /api/* を :8080 へ proxy)
```

`http://localhost:5173` をブラウザで開くとログイン画面が表示される。ベンチマーカーを
ローカルで回す場合は [docs/authoring/dev-loop.md](docs/authoring/dev-loop.md) を参照。

## 注意事項

* スコアのランキング機能はありません
* ISUNARABE 合同演習2026 と環境スペックが異なるため、ベンチマークスコアはあくまで参考値として扱ってください

## GitHub Actions

| 項目 | 内容 |
|---|---|
| ワークフロー | `.github/workflows/bench.yml` |
| トリガー | `push` または手動 (`workflow_dispatch`) |
| 実行内容 | fixtures 準備 → イメージビルド → サービス起動 → bench 実行 → スコア表示 |

## 詳細

- 作問ドキュメント: [docs/README.md](docs/README.md)
- ローカル開発ループ (Docker 不使用): [docs/authoring/dev-loop.md](docs/authoring/dev-loop.md)
- Docker Compose 定義: [compose.yaml](compose.yaml)
