#!/usr/bin/env python3
"""黒電話（作品 #54）の当日ログから「今日の問答」を一本選び、公開用ファイルを書き出す。

    python3 tools/extract_mondou.py [--date YYYYMMDD] [--logdir PATH] [--repo PATH]

入力は kurodenwa の会話ログ `turns-YYYYMMDD.jsonl`（1行1ターン）で、
mac mini 側の `<logdir>/turns-*.jsonl` と Pi 側の `<logdir>/pi2/turns-*.jsonl` を併せて読む。

プライバシー: 来場者の発話（user_text）は出力に一切書かない。選定の材料に使うだけで、
応答が来場者の言い回しをそのまま含んでいる（オウム返し）候補も落とす。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

MIN_CHARS = 40
MAX_CHARS = 140
IDEAL_CHARS = 90

# 来場者の発話が応答に紛れ込んでいないかを見るときの一致長（文字）。
ECHO_NGRAM = 6

# runtime.py が返す定型句（回線ノイズ・生成失敗時のバックストップ）。
# 40字未満なので長さだけでも落ちるが、文言が変わっても効くよう明示しておく。
CANNED_PHRASES = {
    "うーん、うまく言えないな。もう一回聞いてくれる？",
    "ちょっと言葉に詰まったな。別の聞き方をしてみてよ。",
    "なんだろうね。その話、もう少し詳しく聞かせてよ。",
    "ん？　よく聞こえなかった。もう一回言ってくれる？",
    "回線がざらついたかな。もう一度どうぞ。",
    "うまく聞き取れなかったよ。ゆっくり話してみて。",
}

# 中身のない社交辞令・聞き返しで終わっている応答。
STOCK_PATTERNS = (
    re.compile(r"^(どういたしまして|こちらこそ|ありがとう)"),
    re.compile(r"(もう一回|もう一度)(聞かせて|言って|どうぞ|話して)"),
    re.compile(r"(聞き取れ|聞こえ)(なかった|ません)"),
    re.compile(r"^(はい|うん|ええ)[、。]?$"),
)

# 読み上げには乗らない残骸（URL・メンション）が混ざった応答は掲載しない。
JUNK_PATTERN = re.compile(r"https?://|[@＠]\w")

# 名前で呼びかけている応答。来場者が名乗った名前は 4 文字程度で、
# echoes_user の一致長より短くすり抜けるので、呼びかけの形そのものを弾く。
ADDRESS_PATTERN = re.compile(r"[一-龥ァ-ヶー]{2,6}(さん|ちゃん|くん|君|様)")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="黒電話ログから今日の問答を一本選ぶ")
    parser.add_argument("--date", default=datetime.now().strftime("%Y%m%d"),
                        help="対象日 YYYYMMDD（既定: 今日）")
    parser.add_argument("--logdir", default=str(Path.home() / "Projects" / "kurodenwa" / "logs"),
                        help="turns-*.jsonl のあるディレクトリ")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]),
                        help="出力先リポジトリのルート")
    parser.add_argument("--dry-run", action="store_true", help="選定結果を表示するだけで書き出さない")
    return parser.parse_args(argv)


def turn_files(logdir: Path, date: str):
    """当日分のログを mini 側・Pi 側の順に返す（無いものは黙って飛ばす）。"""
    name = f"turns-{date}.jsonl"
    return [p for p in (logdir / name, logdir / "pi2" / name) if p.is_file()]


def load_turns(paths):
    turns = []
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                turns.append(record)
    return turns


def fact_count(turn) -> int:
    metrics = turn.get("metrics")
    if not isinstance(metrics, dict):
        return 0
    facts = metrics.get("knowledge_facts")
    if isinstance(facts, list):
        return len(facts)
    if isinstance(facts, bool):
        return int(facts)
    if isinstance(facts, int):
        return max(facts, 0)
    return 0


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def has_repetition(text: str) -> bool:
    """来場者の発話が同語反復（ASRのループ・連呼）かどうか。"""
    t = normalize(text)
    if not t:
        return False
    if re.search(r"(.)\1{2,}", t):
        return True
    for n in range(2, 7):
        threshold = 4 if n == 2 else 3
        if len(t) < n * threshold:
            break
        unit, count = Counter(t[i:i + n] for i in range(len(t) - n + 1)).most_common(1)[0]
        if count >= threshold and not re.fullmatch(r"[、。！？…ー・,.!?]+", unit):
            return True
    return False


def is_boilerplate(text: str) -> bool:
    t = normalize(text)
    if t in {normalize(p) for p in CANNED_PHRASES}:
        return True
    return any(p.search(t) for p in STOCK_PATTERNS)


def echoes_user(assistant_text: str, user_texts, n: int = ECHO_NGRAM) -> bool:
    """応答が来場者の言い回しを n 文字以上そのまま含んでいたら掲載しない。"""
    reply = normalize(assistant_text)
    for user_text in user_texts:
        u = normalize(user_text)
        if len(u) < n:
            continue
        for i in range(len(u) - n + 1):
            if u[i:i + n] in reply:
                return True
    return False


def candidates(turns):
    """掲載してよいターンを (順序, ファクト数, 応答) で返す。"""
    user_texts = [t.get("user_text", "") for t in turns if t.get("user_text")]
    out = []
    for index, turn in enumerate(turns):
        if turn.get("error"):
            continue
        metrics = turn.get("metrics") if isinstance(turn.get("metrics"), dict) else {}
        if metrics.get("fallback_phrase"):
            continue
        text = (turn.get("assistant_text") or "").strip()
        if not text or JUNK_PATTERN.search(text):
            continue
        if not MIN_CHARS <= len(normalize(text)) <= MAX_CHARS:
            continue
        if is_boilerplate(text) or ADDRESS_PATTERN.search(text):
            continue
        if has_repetition(turn.get("user_text", "")):
            continue
        if echoes_user(text, user_texts):
            continue
        out.append((index, fact_count(turn), text))
    return out


def select(turns):
    """ファクトを使った応答を優先し、長さが真ん中に近いものを一本選ぶ。"""
    found = candidates(turns)
    if not found:
        return None
    index, facts, text = min(
        found,
        key=lambda c: (0 if c[1] else 1, -c[1], abs(len(normalize(c[2])) - IDEAL_CHARS), c[0]),
    )
    return {"text": text, "facts_used": facts > 0}


def sns_draft(date_iso: str, text: str) -> str:
    return (
        f"黒電話は今日、こう答えた。「{text}」 #天孫帰るってよ\n"
        "\n"
        "----\n"
        f"{date_iso} 自動生成の下書き。投稿はしていません。\n"
        "来場者の発話は含みません（応答のみ）。\n"
    )


def write_outputs(repo: Path, date_iso: str, picked: dict) -> dict:
    payload = {"date": date_iso, "text": picked["text"], "facts_used": picked["facts_used"]}

    (repo / "mondou.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive = repo / "mondou_archive.jsonl"
    kept = []
    if archive.is_file():
        for line in archive.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                if json.loads(line).get("date") == date_iso:
                    continue  # 同じ日を二度走らせても増やさない
            except json.JSONDecodeError:
                pass
            kept.append(line)
    entry = dict(payload, generated_at=datetime.now().isoformat(timespec="seconds"))
    kept.append(json.dumps(entry, ensure_ascii=False))
    archive.write_text("\n".join(kept) + "\n", encoding="utf-8")

    draft = repo / "logs" / "mondou_sns_draft.txt"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(sns_draft(date_iso, picked["text"]), encoding="utf-8")
    return payload


def main(argv=None) -> int:
    args = parse_args(argv)
    date_iso = f"{args.date[:4]}-{args.date[4:6]}-{args.date[6:8]}"
    paths = turn_files(Path(args.logdir), args.date)
    if not paths:
        print(f"[mondou] {args.date} のログが {args.logdir} に見つかりません。何も書きません。")
        return 0

    picked = select(load_turns(paths))
    if picked is None:
        print(f"[mondou] {args.date} は掲載できる応答がありませんでした。既存のファイルは触りません。")
        return 0

    if args.dry_run:
        print(f"[mondou] {date_iso} facts={picked['facts_used']}\n{picked['text']}")
        return 0

    write_outputs(Path(args.repo), date_iso, picked)
    print(f"[mondou] {date_iso} を書き出しました（facts_used={picked['facts_used']}）。")
    print(picked["text"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
