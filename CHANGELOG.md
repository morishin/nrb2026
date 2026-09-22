# CHANGELOG

ベンチマーカーでスコア改善を確認できたチューニング変更を記録する。新しいエントリを
先頭に追記する。記録ルール: [CLAUDE.md](CLAUDE.md) 参照。

## 2026-09-22 4249908 Add secondary indexes on campaign_participants and charges

`campaign_participants(campaign_id)` / `campaign_participants(user_id)` /
`charges(campaign_participant_id)` にインデックスを追加した (schema.sql は元々
性能目的の二次 index を付けない設計になっていた)。

- Before (commit 549f425): GitHub Actions score=505000
- After (commit 4249908): GitHub Actions score=528000 (+23000, 約+4.6%)

## 2026-09-22 549f425 Fix N+1 in GET /api/campaigns

`list_campaigns` が campaign 1件ごとに `hydrate_campaign` (3クエリ) を呼んでいた
N+1 を、campaign 全件をまとめて取得する3クエリ (`hydrate_all_campaigns`) に置き換えた。

- Before (baseline, commit 3ea872a): GitHub Actions score=378000
- After (commit 549f425): GitHub Actions score=505000 (+127000, 約+33.6%)
