"""tools/extract_mondou.py の選定基準とプライバシー条件を検証する。

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import extract_mondou as m  # noqa: E402

# 40〜140字の帯に入る、素性の違う応答をいくつか用意する。
LONG_FACT_REPLY = (
    "霧島の森はね、火山の上に育った若い森だよ。噴火のたびに一度こわれて、"
    "そのあとで木がまた立ち上がる。作品もそうやって作り直してきた。"
)
LONG_PLAIN_REPLY = (
    "そうだね、答えはひとつじゃないと思うよ。展示室をぐるっと歩いてみて、"
    "気になったところで足を止めてくれたら、それでいい。"
)
SHORT_REPLY = "うん、そうだね。"
OVERLONG_REPLY = "波が木になる話をしようか。" * 12


def turn(user="展示について教えて", assistant=LONG_FACT_REPLY, facts=("鰻ドラゴンはこの会場に展示してある。",), **extra):
    record = {
        "ts": "2026-07-29T17:00:00.000",
        "turn_id": "t1",
        "user_text": user,
        "assistant_text": assistant,
        "spoken_text": assistant,
        "metrics": {"knowledge_facts": list(facts), "fallback_phrase": False},
    }
    record.update(extra)
    return record


def write_log(logdir: Path, date: str, turns, sub=None):
    target = logdir / sub if sub else logdir
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"turns-{date}.jsonl"
    path.write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in turns), encoding="utf-8")
    return path


class SelectionTests(unittest.TestCase):
    def test_picks_a_reply_in_the_length_band(self):
        picked = m.select([turn()])
        self.assertIsNotNone(picked)
        self.assertEqual(picked["text"], LONG_FACT_REPLY)
        self.assertTrue(picked["facts_used"])

    def test_rejects_too_short_and_too_long(self):
        self.assertIsNone(m.select([turn(assistant=SHORT_REPLY), turn(assistant=OVERLONG_REPLY)]))

    def test_prefers_a_reply_that_used_knowledge_facts(self):
        picked = m.select([
            turn(user="この森はどんな森なの", assistant=LONG_PLAIN_REPLY, facts=()),
            turn(user="作品の作り方を知りたい", assistant=LONG_FACT_REPLY),
        ])
        self.assertEqual(picked["text"], LONG_FACT_REPLY)
        self.assertTrue(picked["facts_used"])

    def test_falls_back_to_a_factless_reply_when_nothing_else_qualifies(self):
        picked = m.select([turn(assistant=LONG_PLAIN_REPLY, facts=())])
        self.assertEqual(picked["text"], LONG_PLAIN_REPLY)
        self.assertFalse(picked["facts_used"])

    def test_excludes_canned_safety_replies(self):
        canned = "うまく聞き取れなかったよ。ゆっくり話してみて。もう一回、ゆっくりお願いできるかな。"
        self.assertGreaterEqual(len(canned), m.MIN_CHARS)
        self.assertIsNone(m.select([turn(assistant=canned, facts=())]))
        self.assertTrue(m.is_boilerplate("どういたしまして"))

    def test_excludes_turns_flagged_as_fallback_phrases(self):
        self.assertIsNone(m.select([turn(**{"metrics": {"knowledge_facts": [], "fallback_phrase": True}})]))

    def test_excludes_turns_whose_question_is_a_stuck_repetition(self):
        self.assertTrue(m.has_repetition("もしもしもしもし"))
        self.assertTrue(m.has_repetition("ああああ"))
        self.assertFalse(m.has_repetition("この作品はどうやって作ったんですか"))
        self.assertIsNone(m.select([turn(user="もしもしもしもし")]))

    def test_excludes_replies_containing_urls(self):
        self.assertIsNone(m.select([turn(assistant=LONG_FACT_REPLY + " https://example.com/abc")]))

    def test_reads_both_the_mac_log_and_the_pi_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            logdir = Path(tmp)
            write_log(logdir, "20260729", [turn(assistant=LONG_PLAIN_REPLY, facts=())])
            write_log(logdir, "20260729", [turn()], sub="pi2")
            turns = m.load_turns(m.turn_files(logdir, "20260729"))
            self.assertEqual(len(turns), 2)
            self.assertEqual(m.select(turns)["text"], LONG_FACT_REPLY)


class PrivacyTests(unittest.TestCase):
    SECRET = "私の名前は山田花子で今日は妻の誕生日なんです"

    def test_reply_that_calls_the_visitor_by_name_is_rejected(self):
        # 名前は echoes_user の一致長より短いので、呼びかけの形で落とす。
        parrot = "山田花子さん、誕生日おめでとう。今日この森で聞いた話は、僕の中にだけ置いておくよ。よい一日を。"
        self.assertTrue(m.ADDRESS_PATTERN.search(parrot))
        self.assertIsNone(m.select([turn(user=self.SECRET, assistant=parrot)]))

    def test_reply_that_repeats_a_long_stretch_of_the_question_is_rejected(self):
        parrot = (
            "私の名前は山田花子で今日は妻の誕生日なんです、という話だったね。"
            "そういう日にここへ来てくれたのが、いちばん面白いと思うよ。"
        )
        self.assertTrue(m.echoes_user(parrot, [self.SECRET]))
        self.assertIsNone(m.select([turn(user=self.SECRET, assistant=parrot)]))

    def test_no_output_file_contains_the_visitor_utterance(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            logdir = Path(tmp) / "logs"
            repo.mkdir()
            write_log(logdir, "20260729", [turn(user=self.SECRET)])
            rc = m.main(["--date", "20260729", "--logdir", str(logdir), "--repo", str(repo)])
            self.assertEqual(rc, 0)

            written = [repo / "mondou.json", repo / "mondou_archive.jsonl",
                       repo / "logs" / "mondou_sns_draft.txt"]
            for path in written:
                self.assertTrue(path.is_file(), path)
                body = path.read_text(encoding="utf-8")
                self.assertNotIn(self.SECRET, body)
                # 断片も残さない
                for i in range(len(self.SECRET) - m.ECHO_NGRAM + 1):
                    self.assertNotIn(self.SECRET[i:i + m.ECHO_NGRAM], body)
                self.assertNotIn("user_text", body)

    def test_published_json_has_only_the_three_public_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            m.write_outputs(repo, "2026-07-29", {"text": LONG_FACT_REPLY, "facts_used": True})
            data = json.loads((repo / "mondou.json").read_text(encoding="utf-8"))
            self.assertEqual(set(data), {"date", "text", "facts_used"})
            self.assertEqual(data["date"], "2026-07-29")


class OutputTests(unittest.TestCase):
    def test_archive_appends_and_replaces_the_same_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            m.write_outputs(repo, "2026-07-28", {"text": LONG_PLAIN_REPLY, "facts_used": False})
            m.write_outputs(repo, "2026-07-29", {"text": LONG_FACT_REPLY, "facts_used": True})
            m.write_outputs(repo, "2026-07-29", {"text": LONG_PLAIN_REPLY, "facts_used": False})
            lines = [json.loads(l) for l in
                     (repo / "mondou_archive.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([l["date"] for l in lines], ["2026-07-28", "2026-07-29"])
            self.assertEqual(lines[-1]["text"], LONG_PLAIN_REPLY)

    def test_sns_draft_quotes_the_reply_and_says_it_is_a_draft(self):
        draft = m.sns_draft("2026-07-29", LONG_FACT_REPLY)
        self.assertTrue(draft.startswith("黒電話は今日、こう答えた。「"))
        self.assertIn("#天孫帰るってよ", draft)
        self.assertIn("投稿はしていません", draft)

    def test_missing_log_leaves_existing_files_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "mondou.json").write_text('{"date":"2026-07-28"}', encoding="utf-8")
            rc = m.main(["--date", "20260729", "--logdir", str(Path(tmp) / "nope"), "--repo", str(repo)])
            self.assertEqual(rc, 0)
            self.assertEqual((repo / "mondou.json").read_text(encoding="utf-8"), '{"date":"2026-07-28"}')

    def test_a_day_with_no_usable_reply_leaves_existing_files_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            logdir = Path(tmp) / "logs"
            repo.mkdir()
            (repo / "mondou.json").write_text('{"date":"2026-07-28"}', encoding="utf-8")
            write_log(logdir, "20260729", [turn(assistant=SHORT_REPLY, facts=())])
            rc = m.main(["--date", "20260729", "--logdir", str(logdir), "--repo", str(repo)])
            self.assertEqual(rc, 0)
            self.assertEqual((repo / "mondou.json").read_text(encoding="utf-8"), '{"date":"2026-07-28"}')

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            logdir = Path(tmp) / "logs"
            repo.mkdir()
            write_log(logdir, "20260729", [turn()])
            rc = m.main(["--date", "20260729", "--logdir", str(logdir),
                         "--repo", str(repo), "--dry-run"])
            self.assertEqual(rc, 0)
            self.assertFalse((repo / "mondou.json").exists())


if __name__ == "__main__":
    unittest.main()
