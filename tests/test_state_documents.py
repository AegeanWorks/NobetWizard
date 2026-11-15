import unittest

from state_documents import LANGUAGES, is_users_document, normalize_personnel_document


def person(**overrides):
    record = {
        "name": "Ann", "gender": "F", "role": "Senior", "fixed_duties_total": 0,
        "fixed_duties_weekend": 0, "max_duties": 20, "max_weekends": 10,
        "mixed_gender_allowed": True, "busy_days": "", "off_dates": "", "leave_dates": "",
        "fixed_dates": "", "duty_count": 0, "weekend_duty_count": 0,
    }
    record.update(overrides)
    return record


class NormalizePersonnelDocumentTest(unittest.TestCase):
    def test_a_saved_document_passes_through_unchanged(self):
        document = {
            "personnel": [person()], "conditional_rules": [], "forbidden_pairs": [],
            "holidays_multiselect": [], "cfg_year": 2026, "cfg_month": 11, "cfg_ppl": 2,
            "cfg_min_seniors": 0, "cfg_gender": "Any", "cfg_consecutive": False,
            "cfg_two_rest": False, "cfg_max_weekly": 3, "cfg_language": "English",
        }
        self.assertEqual(normalize_personnel_document(document), (document, 0))

    def test_a_bare_list_is_the_legacy_personnel_format(self):
        self.assertEqual(normalize_personnel_document([person()]), ({"personnel": [person()]}, 0))

    def test_unusable_top_level_shapes_return_none(self):
        for data in (5, None, "x", {"personnel": 5}, {"personnel": None}, {"personnel": "x"}):
            self.assertEqual(normalize_personnel_document(data), (None, 0), data)

    def test_an_empty_object_or_list_is_an_empty_roster(self):
        self.assertEqual(normalize_personnel_document({}), ({"personnel": []}, 0))
        self.assertEqual(normalize_personnel_document([]), ({"personnel": []}, 0))

    def test_entries_that_are_not_usable_people_are_dropped_and_counted(self):
        bad = [1, "x", None, person(name=""), person(name=5), person(gender="X"), {"name": "NoGender"}]
        document, dropped = normalize_personnel_document({"personnel": [person(name="Keep")] + bad})
        self.assertEqual([p["name"] for p in document["personnel"]], ["Keep"])
        self.assertEqual(dropped, len(bad))

    def test_missing_limits_get_the_add_form_defaults(self):
        record = person()
        del record["max_duties"], record["max_weekends"]
        document, dropped = normalize_personnel_document({"personnel": [record]})
        self.assertEqual((document["personnel"][0]["max_duties"], document["personnel"][0]["max_weekends"]), (5, 2))
        self.assertEqual(dropped, 0)

    def test_limits_of_the_wrong_type_get_the_defaults(self):
        document, _ = normalize_personnel_document(
            {"personnel": [person(max_duties="many", max_weekends=None), person(name="B", max_duties=True)]}
        )
        self.assertEqual([(p["max_duties"], p["max_weekends"]) for p in document["personnel"]], [(5, 2), (5, 10)])

    def test_settings_of_the_wrong_type_or_range_are_dropped(self):
        bad = {
            "personnel": [], "conditional_rules": 5, "forbidden_pairs": 5, "holidays_multiselect": 5,
            "cfg_year": "x", "cfg_month": 99, "cfg_ppl": 0, "cfg_min_seniors": -1, "cfg_max_weekly": "3",
            "cfg_consecutive": "yes", "cfg_two_rest": 1, "cfg_gender": 3, "cfg_language": None,
        }
        self.assertEqual(normalize_personnel_document(bad), ({"personnel": []}, 0))

    def test_unknown_keys_are_kept(self):
        document, _ = normalize_personnel_document({"personnel": [], "generated_schedule": {"a": 1}})
        self.assertEqual(document["generated_schedule"], {"a": 1})

    def test_fixed_duty_targets_of_the_wrong_type_become_zero(self):
        people = [
            person(name="A", fixed_duties_total="x", fixed_duties_weekend=None),
            person(name="B", fixed_duties_total=True, fixed_duties_weekend=-1),
            person(name="C", fixed_duties_total=3, fixed_duties_weekend=2),
        ]
        document, dropped = normalize_personnel_document({"personnel": people})
        self.assertEqual(dropped, 0)
        self.assertEqual(
            [(p["fixed_duties_total"], p["fixed_duties_weekend"]) for p in document["personnel"]],
            [(0, 0), (0, 0), (3, 2)],
        )

    def test_a_missing_fixed_duty_target_is_left_for_the_app_to_default(self):
        record = person()
        del record["fixed_duties_total"], record["fixed_duties_weekend"]
        document, _ = normalize_personnel_document({"personnel": [record]})
        self.assertNotIn("fixed_duties_total", document["personnel"][0])

    def test_only_known_languages_are_kept(self):
        for language in LANGUAGES:
            document, _ = normalize_personnel_document({"personnel": [], "cfg_language": language})
            self.assertEqual(document["cfg_language"], language)
        for language in ("French", "", None, 3):
            document, _ = normalize_personnel_document({"personnel": [], "cfg_language": language})
            self.assertNotIn("cfg_language", document)

    def test_the_input_is_not_modified(self):
        original = {"personnel": [person(), 1], "cfg_month": 99}
        snapshot = {"personnel": [person(), 1], "cfg_month": 99}
        normalize_personnel_document(original)
        self.assertEqual(original, snapshot)


class IsUsersDocumentTest(unittest.TestCase):
    def test_only_an_object_is_a_users_document(self):
        self.assertTrue(is_users_document({}))
        self.assertTrue(is_users_document({"ann": "hash"}))
        for data in (5, None, "x", [], ["ann"]):
            self.assertFalse(is_users_document(data), data)


if __name__ == "__main__":
    unittest.main()
