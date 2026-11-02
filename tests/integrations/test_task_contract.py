import json
import unittest

from pydantic import ValidationError

from src.integrations.task_contract import TaskEnvelope, from_runescript_task


def example(**changes):
    data = {
        "contract_version": "0.1.0",
        "task_id": "hypenosys:4",
        "source": "hypenosys",
        "external_id": "4",
        "title": "Example task",
        "status": "todo",
        "priority": "high",
    }
    data.update(changes)
    return data


class TaskEnvelopeTests(unittest.TestCase):
    def test_contract_example_round_trips_as_json(self):
        data = example(description="Work", repository="owner/repository", branch=None,
                       acceptance_criteria=[], metadata={})
        envelope = TaskEnvelope.model_validate(data)
        self.assertEqual(json.loads(envelope.model_dump_json(exclude_unset=True)), data)

    def test_required_fields_cannot_be_missing_null_or_wrong_type(self):
        for field in example():
            with self.subTest(field=field, value="missing"):
                data = example()
                del data[field]
                with self.assertRaises(ValidationError):
                    TaskEnvelope.model_validate(data)
            for invalid in (None, 42, ""):
                with self.subTest(field=field, value=invalid):
                    with self.assertRaises(ValidationError):
                        TaskEnvelope.model_validate(example(**{field: invalid}))

    def test_identity_version_and_blank_fields_are_checked(self):
        for changes in ({"contract_version": "0.2.0"}, {"task_id": "other:4"},
                        {"title": "  "}, {"source": " ", "task_id": " :4"},
                        {"external_id": " ", "task_id": "hypenosys: "}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                TaskEnvelope.model_validate(example(**changes))

    def test_each_normalized_status_and_priority_and_unknown_values(self):
        for status in ("todo", "in_progress", "testing", "review", "done", "blocked", "cancelled"):
            self.assertEqual(TaskEnvelope.model_validate(example(status=status)).status, status)
        for priority in ("low", "medium", "high", "critical"):
            self.assertEqual(TaskEnvelope.model_validate(example(priority=priority)).priority, priority)
        for changes in ({"status": "completed"}, {"status": "unknown"}, {"priority": "urgent"}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                TaskEnvelope.model_validate(example(**changes))

    def test_omitted_null_and_empty_optional_fields_remain_distinct(self):
        omitted = TaskEnvelope.model_validate(example()).model_dump(exclude_unset=True)
        null = TaskEnvelope.model_validate(example(branch=None)).model_dump(exclude_unset=True)
        empty = TaskEnvelope.model_validate(example(branch="", acceptance_criteria=[], metadata={})).model_dump(exclude_unset=True)
        self.assertNotIn("branch", omitted)
        self.assertIsNone(null["branch"])
        self.assertEqual(empty["branch"], "")
        self.assertNotIn("acceptance_criteria", omitted)
        self.assertEqual(empty["acceptance_criteria"], [])
        self.assertEqual(empty["metadata"], {})

    def test_optional_field_types_and_json_metadata(self):
        for changes in ({"description": 1}, {"branch": []}, {"repository": 1},
                        {"acceptance_criteria": None}, {"acceptance_criteria": ["ok", 1]},
                        {"metadata": None}, {"metadata": {"x": object()}},
                        {"metadata": {"x": float("nan")}}, {"metadata": {1: "x"}},
                        {"other": "not in contract"}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                TaskEnvelope.model_validate(example(**changes))
        metadata = {"original": {"count": 2, "values": [True, None, ""]}}
        self.assertEqual(TaskEnvelope.model_validate(example(metadata=metadata)).metadata, metadata)

    def test_common_credential_keys_are_rejected_recursively(self):
        for key in ("access_token", "apiKey", "password", "client_secret", "Authorization"):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                TaskEnvelope.model_validate(example(metadata={"nested": [{key: "sensitive"}]}))

    def test_runescript_task_normalization_preserves_source_fields(self):
        task = {"status": "pending", "description": "Implement parser", "phase": "1", "line_number": 12, "note": "context"}
        before = dict(task)
        envelope = from_runescript_task(task, external_id="stable-123", priority="medium")
        self.assertEqual(envelope.task_id, "runescript:stable-123")
        self.assertEqual(envelope.title, "Implement parser")
        self.assertEqual(envelope.status, "todo")
        self.assertEqual(envelope.metadata, {"runescript": {"phase": "1", "line_number": 12, "note": "context"}})
        self.assertEqual(task, before)
        self.assertEqual(TaskEnvelope.model_validate_json(envelope.model_dump_json(exclude_unset=True)), envelope)

    def test_runescript_status_mapping_and_rejection(self):
        for source, expected in (("pending", "todo"), ("completed", "done"), ("blocked", "blocked")):
            task = {"status": source, "description": "Task"}
            self.assertEqual(from_runescript_task(task, external_id="id", priority="high").status, expected)
        for task in ({"status": "mystery", "description": "Task"}, {"status": "pending"},
                     {"status": "pending", "description": "Task", "token": "secret"}):
            with self.subTest(task=task), self.assertRaises(ValueError):
                from_runescript_task(task, external_id="id", priority="high")
        with self.assertRaises(ValidationError):
            from_runescript_task({"status": "pending", "description": "Task"}, external_id="", priority="high")


if __name__ == "__main__":
    unittest.main()
