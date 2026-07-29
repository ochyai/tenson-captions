#!/bin/zsh
# 毎晩17:00に mac mini で走る「今日の問答」更新。
# 当日ログから一本選び、変化があったときだけ mondou.json / mondou_archive.jsonl を
# コミットして push する。launchd から呼ばれる（tools/com.ochyai.tenson-mondou.plist）。
#
# 環境変数で上書きできるもの:
#   MONDOU_LOGDIR  黒電話のログディレクトリ（既定 ~/Projects/kurodenwa/logs）
#   MONDOU_PYTHON  python3 の場所（既定 /usr/bin/python3）
#   MONDOU_BRANCH  push 先ブランチ（既定はチェックアウト中のブランチ）

set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin

REPO="${0:A:h:h}"
PYTHON="${MONDOU_PYTHON:-/usr/bin/python3}"
LOGDIR="${MONDOU_LOGDIR:-$HOME/Projects/kurodenwa/logs}"
DATE="$(date +%Y%m%d)"

log() { print -r -- "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "start: repo=$REPO logdir=$LOGDIR date=$DATE"

"$PYTHON" "$REPO/tools/extract_mondou.py" --date "$DATE" --logdir "$LOGDIR" --repo "$REPO"

cd "$REPO"
git add mondou.json mondou_archive.jsonl 2>/dev/null || true

if git diff --cached --quiet -- mondou.json mondou_archive.jsonl; then
  log "no change today; nothing to commit"
  exit 0
fi

BRANCH="${MONDOU_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"
git commit -m "今日の問答: $DATE" -- mondou.json mondou_archive.jsonl
log "committed on $BRANCH"

# ページ側の更新が先に入っていることがあるので、push 前に取り込む。
if ! git pull --rebase --autostash origin "$BRANCH"; then
  log "ERROR: pull --rebase failed; commit is local only. 手で解決してください"
  exit 1
fi

git push origin "$BRANCH"
log "pushed to origin/$BRANCH"
