import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from scheduled_sync import canonical, normalized, collect

def sample(name="First title", url="https://www.rappler.com/philippines/story/?utm_source=foo"):
    return {"originalUrl":url,"sourceName":"Rappler","title":name,
            "dateISO":"2026-10-13T03:00:00Z","summary":"A linked news summary",
            "officials":["Sara Duterte"],"tags":["Investigations and claims"]}

class ScheduledSyncTests(unittest.TestCase):
    def test_canonical_remove_tracking(self):
        self.assertEqual(canonical(sample()["originalUrl"]),"https://rappler.com/philippines/story")
    def test_reject_nonpublisher(self):
        self.assertIsNone(normalized(sample(url="https://example.net/news")))
    def test_publisher_claim_must_match_host(self):
        row=sample();row["sourceName"]="GMA News"
        self.assertIsNone(normalized(row))
    def test_idempotent_import_same_day(self):
        with TemporaryDirectory() as d:
            payload={"entries":[sample(),sample()]}
            first=collect(payload,d,"2026-10-13")
            second=collect(payload,d,"2026-10-13")
            self.assertEqual(first["new"],1)
            self.assertEqual(second["new"],0)
            self.assertEqual(second["total"],1)
            self.assertEqual(len(list(Path(d).glob("snapshots/*.json"))),1)
    def test_change_captured_and_sent_for_review(self):
        with TemporaryDirectory() as d:
            collect({"entries":[sample()]},d,"2026-10-13")
            result=collect({"entries":[sample(name="Corrected publisher title")]},d,"2026-10-14")
            self.assertEqual(result["changed"],1)
            data=json.loads((Path(d)/"index.json").read_text())
            rec=next(iter(data["byUrl"].values()))
            self.assertEqual(rec["editorialStatus"],"pending")
            self.assertEqual(rec["firstCapturedAt"],"2026-10-13")
            self.assertEqual(len(list(Path(d).glob("snapshots/*.json"))),2)
    def test_zero_entries_does_not_erase_index(self):
        with TemporaryDirectory() as d:
            collect({"entries":[sample()]},d,"2026-10-13")
            collect({"entries":[]},d,"2026-10-14")
            data=json.loads((Path(d)/"index.json").read_text())
            self.assertEqual(len(data["byUrl"]),1)
    def test_reject_non_rss_payload(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                collect({"records":[]},d,"2026-10-13")

    def test_untagged_local_crime_report_not_in_government_index(self):
        row=sample()
        row["title"]="Unrelated local crime"
        row["officials"]=[]
        row["tags"]=[]
        self.assertIsNone(normalized(row))

    def test_same_day_updates_preserve_multiple_captures(self):
        with TemporaryDirectory() as d:
            collect({"entries":[sample()]},d,"2026-10-13")
            collect({"entries":[sample(name="Publisher corrected the title")]},d,"2026-10-13")
            snapshots=list(Path(d).glob("snapshots/*.json"))
            self.assertEqual(len(snapshots),2)
            names=[json.loads(p.read_text())["records"][0]["title"] for p in snapshots]
            self.assertEqual(set(names),{"First title","Publisher corrected the title"})

    def test_inquirer_original_source_and_subdomains(self):
        row=sample(url="https://globalnation.inquirer.net/341758/icc-holds-4th-status-conference?utm_medium=rss")
        row["sourceName"]="INQUIRER.net"
        normalized_record=normalized(row)
        self.assertIsNotNone(normalized_record)
        self.assertEqual(normalized_record["originalUrl"],"https://globalnation.inquirer.net/341758/icc-holds-4th-status-conference")
        self.assertEqual(normalized_record["sourceName"],"INQUIRER.net")

    def test_reject_inquirer_impostor(self):
        row=sample(url="https://inquirer.net.evil.org/fake")
        row["sourceName"]="INQUIRER.net"
        self.assertIsNone(normalized(row))

if __name__=="__main__":
    unittest.main()
