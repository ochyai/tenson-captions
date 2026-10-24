# 天孫帰るってよ？ 作品解説 / TENSOИ Captions

落合陽一 TENSON「天孫帰るってよ？」(2026.7.11–9.23) の全作品キャプション（日英）。
番号・掲載順は会場配布マップに準拠。

- Page: https://ochyai.github.io/tenson-captions/
- `index.html` — 静的ページ（generated from the exhibition work list xlsx）。現在は index.html を直接編集する運用（AR帯・年表帯・会場ギャラリー・相互リンクなど手作業の資産を含む）
- `data_works.json` — 抽出元データ。作品番号は 2026-07-22 版（1–118）の `num` が正
- `mondou.json` / `mondou_archive.jsonl` — 「今日の問答」の最新1本と蓄積（下記）
- `tools/gen.py` — 初期のページ生成スクリプト。**そのままでは動かない**（入力の作業領域が消滅、番号体系が旧版、再生成すると手作業分が消える。冒頭の TODO 参照）。使わない
- `photos/`・`g_*.jpg`・`kv*.jpg`・`keyvisual.webp`・`og_keyvisual.jpg` — 会場写真・キービジュアル
- `tests/test_extract_mondou.py` — 問答抽出のテスト

## 状態（2026-10-24 時点の確認）
- 会期（2026-07-11〜09-23）は終了。最後の commit は 2026-09-24 の「今日の問答」（mondou_archive.jsonl は55行）。以後の更新は無い。
- 毎晩の問答の自動実行（mac mini の launchd）が今も動いているかはリポからは分からない（未確認）。
- 公開（GitHub Pages）：リポは public。

## 今日の問答

会場の黒電話（#54）の当日ベスト応答を毎晩1本、#54カードの直後に掲載する。

- `tools/extract_mondou.py` — 当日ログから1本選び `mondou.json` を上書き、`mondou_archive.jsonl` に追記、
  SNS下書きを `logs/mondou_sns_draft.txt`（gitignore）に書く。標準ライブラリのみ。
  来場者の発話（`user_text`）は選定に使うだけで出力には一切書かない。
- `tools/mondou_nightly.sh` — 抽出 → 変化があれば commit → pull --rebase → push。
- `tools/com.ochyai.tenson-mondou.plist` — mac mini 用 launchd（毎日17:00）。設置手順はファイル冒頭のコメント。
- ページ側は `mondou.json` を fetch し、無い・壊れているときはセクションごと出さない。

```bash
python3 tools/extract_mondou.py --date 20260728 --logdir ~/Projects/kurodenwa/logs --dry-run
python3 -m unittest discover -s tests
```

2026-10-24 に `python3 -m unittest discover -s tests` を実行し通過を確認。`tools/*.py` は構文確認済み。ログ（`~/Projects/kurodenwa/logs`）はリポの外。

## 一行の物語（見落とし44点）

範囲カード（木化する波・借景するガラス・銀口魚・十三支）の中で個体を展開し、一行ずつ添えている。
文言の正本は `~/kirishima-graph/zukan-lines.json`。推敲前の行には `<!-- 物語:要推敲 -->` を付けてある。

## 決まり
- public リポ。来場者の発話・個人情報・鍵を入れない（問答は選んだ応答側の1本だけを載せる設計。`user_text` は出力しない）。
- `logs/`（SNS 下書き）と `.gstack/` は gitignore。
- 関連：`ochyai/kirishima-panels`（霧島側のパネル）、文言の正本は `~/kirishima-graph/zukan-lines.json`（リポの外）。
