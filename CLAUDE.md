# CLAUDE.md

このリポジトリは ISUNARABE 合同演習2026 の問題を解く側 (コンテスト参加者) として
チューニング作業を行うための fork。問題の作問自体はこのリポジトリの管轄ではない。

## ローカル開発

- ローカル起動手順: [README.md](README.md) の「ローカルで起動する」
- ベンチを回してログからボトルネックを分析する手順: [docs/bench-log-analysis.md](docs/bench-log-analysis.md)

## ベンチの回し方

GitHub Actions (push トリガー) のベンチは1回あたり約10分かかるため、基本はローカルの
`scripts/dev-bench.sh` で素早く反復する。remote (GitHub Actions) のベンチはたまに回し、
その完了を待っている間もローカルでの改善作業を並行して進めてよい。

## スコア改善の記録ルール

ベンチマーカー (ローカルの `scripts/dev-bench.sh`、または push 後の GitHub Actions) で
スコア改善を確認できた変更は [CHANGELOG.md](CHANGELOG.md) に記録すること。基本はローカル
bench のスコアを記録して構わない。

- 記録するタイミング: 変更をコミットし、ベンチでスコア改善を確認できた後
  (スコアが変わらない/悪化した試行錯誤は記録しなくてよい)
- 記録する内容:
  - その変更のコミットハッシュ (short hash) と一言説明
  - 変更前後のスコア、どちらの計測か (ローカル bench / GitHub Actions) を必ず明記
- 新しいエントリは CHANGELOG.md の先頭に追記する (降順)
- コミットハッシュは変更をコミットした後でないと分からないため、CHANGELOG.md への
  追記は「変更のコミット」とは別の、それに続く小さなコミットとして行う
