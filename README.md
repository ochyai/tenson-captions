# 天孫帰るってよ？ 作品解説 / TENSOИ Captions

落合陽一 TENSON「天孫帰るってよ？」(2026.7.11–9.23) の全作品キャプション（日英）。
番号・掲載順は会場配布マップに準拠。

- Page: https://ochyai.github.io/tenson-captions/
- `index.html` — 静的ページ（generated from the exhibition work list xlsx）
- `data_works.json` — 抽出元データ

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

## 一行の物語（見落とし44点）

範囲カード（木化する波・借景するガラス・銀口魚・十三支）の中で個体を展開し、一行ずつ添えている。
文言の正本は `~/kirishima-graph/zukan-lines.json`。推敲前の行には `<!-- 物語:要推敲 -->` を付けてある。
