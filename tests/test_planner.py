import os
import unittest
from unittest.mock import patch

from planner import create_plan, load_catalog


BASE_PROFILE = {
    "goal": "Find a supported path into an administrative role",
    "strengths": "organising information and careful written work",
    "interests": ["office administration", "digital skills"],
    "full_time_student": None,
    "weekly_hours": 8,
    "budget_sgd": 0,
    "synthetic": True,
}


def tool_use(tool_use_id, name, tool_input):
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": tool_use_id,
                            "name": name,
                            "input": tool_input,
                        }
                    }
                ],
            }
        },
        "stopReason": "tool_use",
        "usage": {"inputTokens": 20, "outputTokens": 10, "totalTokens": 30},
        "metrics": {"latencyMs": 5},
    }


class ConverseDouble:
    """External Bedrock boundary double using documented Converse response shapes."""

    model_id = "test-model"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError("Unexpected model request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class PlannerTests(unittest.TestCase):
    def test_catalog_separates_reviewed_public_resources_from_fictional_slots(self):
        catalog = load_catalog()

        self.assertGreaterEqual(len(catalog), 6)
        official = [item for item in catalog if item["provenance"] == "reviewed_public"]
        fictional = [item for item in catalog if item["provenance"] == "fictional_demo"]
        self.assertGreaterEqual(len(official), 5)
        self.assertTrue(all(item["source_url"].startswith("https://") for item in official))
        self.assertTrue(fictional)
        self.assertTrue(all("Fictional demo" in item["title"] for item in fictional))
        self.assertTrue(
            all("required_weekly_hours" in item and "cost_sgd" in item for item in catalog)
        )
        free_slot = next(item for item in catalog if item["id"] == "fictional-office-skills-taster")
        self.assertEqual(2, free_slot["required_weekly_hours"])
        self.assertEqual(0, free_slot["cost_sgd"])
        self.assertTrue(
            all(
                item["required_weekly_hours"] is None and item["cost_sgd"] is None
                for item in official
            )
        )

    def test_invalid_profile_shapes_raise_value_error(self):
        invalid_profiles = [
            {**BASE_PROFILE, "synthetic": False},
            {**BASE_PROFILE, "interests": "digital skills"},
            {**BASE_PROFILE, "weekly_hours": True},
            {**BASE_PROFILE, "weekly_hours": -1},
            {**BASE_PROFILE, "weekly_hours": 169},
            {**BASE_PROFILE, "budget_sgd": -1},
            {**BASE_PROFILE, "budget_sgd": 100001},
            {**BASE_PROFILE, "diagnosis": "not permitted"},
        ]

        for profile in invalid_profiles:
            with self.subTest(profile=profile):
                with self.assertRaises(ValueError):
                    create_plan(profile)

        with self.assertRaises(ValueError):
            create_plan(BASE_PROFILE, mode="automatic")

    def test_missing_goal_requests_clarification(self):
        result = create_plan({**BASE_PROFILE, "goal": "  "})

        self.assertEqual("needs_clarification", result["status"])
        self.assertEqual([], result["actions"])
        self.assertTrue(any("goal" in question.lower() for question in result["questions"]))

    def test_participant_supporter_conflict_is_not_silently_resolved(self):
        result = create_plan(
            {
                **BASE_PROFILE,
                "goal": "Explore outdoor horticulture work",
                "supporter_goal": "Move directly into office administration",
            }
        )

        self.assertEqual("needs_clarification", result["status"])
        self.assertEqual([], result["actions"])
        self.assertTrue(any("participant" in question.lower() for question in result["questions"]))

    def test_full_time_student_exclusion_is_enforced(self):
        result = create_plan({**BASE_PROFILE, "full_time_student": True})

        self.assertNotIn(
            "sg-enable-sector-train-place",
            {action["resource_id"] for action in result["actions"]},
        )
        self.assertTrue(any("full-time student" in question.lower() for question in result["questions"]))

    def test_offline_actions_use_catalog_titles_and_urls(self):
        catalog_by_id = {item["id"]: item for item in load_catalog()}
        result = create_plan(BASE_PROFILE)

        self.assertEqual("offline", result["mode"])
        self.assertEqual("draft", result["status"])
        self.assertLessEqual(len(result["actions"]), 3)
        self.assertTrue(any(event.get("label") == "offline fixture mode" for event in result["trace"]))
        for action in result["actions"]:
            source = catalog_by_id[action["resource_id"]]
            self.assertEqual(source["title"], action["title"])
            self.assertEqual(source["source_url"], action["source_url"])

    def test_offline_filters_known_time_and_budget_conflicts(self):
        result = create_plan(
            {
                **BASE_PROFILE,
                "goal": "Try office and specialist software tasks",
                "interests": ["office skills", "specialist software"],
                "weekly_hours": 0,
                "budget_sgd": 0,
            }
        )

        ids = {action["resource_id"] for action in result["actions"]}
        self.assertNotIn("fictional-office-skills-taster", ids)
        self.assertNotIn("fictional-software-practice", ids)
        for action in result["actions"]:
            self.assertTrue(any("weekly hours" in check.lower() for check in action["checks"]))
            self.assertTrue(any("cost" in check.lower() for check in action["checks"]))

    def test_unknown_time_and_budget_are_kept_as_questions(self):
        result = create_plan({**BASE_PROFILE, "weekly_hours": None, "budget_sgd": None})

        self.assertTrue(any("weekly hours" in question.lower() for question in result["questions"]))
        self.assertTrue(any("budget" in question.lower() for question in result["questions"]))

    def test_bedrock_finish_plan_hydrates_only_catalog_facts(self):
        client = ConverseDouble(
            [
                tool_use(
                    "search-1",
                    "search_resources",
                    {"query": "administration digital skills"},
                ),
                tool_use(
                    "inspect-1",
                    "inspect_resource",
                    {"resource_id": "skillsfuture-careersfinder"},
                ),
                tool_use(
                    "finish-1",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [],
                    },
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)
        source = next(
            item for item in load_catalog() if item["id"] == "skillsfuture-careersfinder"
        )

        self.assertEqual("bedrock", result["mode"])
        self.assertEqual("draft", result["status"])
        self.assertEqual(source["title"], result["actions"][0]["title"])
        self.assertEqual(source["source_url"], result["actions"][0]["source_url"])
        self.assertEqual(3, len([event for event in result["trace"] if event["stage"] == "model"]))

    def test_outbound_tool_schemas_use_only_nova_v1_top_level_fields(self):
        client = ConverseDouble(
            [
                tool_use(
                    "finish-1",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [],
                    },
                )
            ]
        )

        create_plan(BASE_PROFILE, mode="bedrock", client=client)

        schemas = [
            tool["toolSpec"]["inputSchema"]["json"]
            for tool in client.calls[0]["toolConfig"]["tools"]
        ]
        self.assertTrue(schemas)
        for schema in schemas:
            self.assertEqual({"type", "properties", "required"}, set(schema))

    def test_invalid_model_arguments_get_one_bounded_repair_then_stop(self):
        client = ConverseDouble(
            [
                tool_use(
                    "bad-1",
                    "inspect_resource",
                    {"resource_id": "skillsfuture-careersfinder", "url": "https://evil.invalid"},
                ),
                tool_use("bad-2", "browse_web", {"url": "https://evil.invalid"}),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("partial", result["status"])
        self.assertEqual([], result["actions"])
        self.assertEqual(2, len(client.calls))
        self.assertEqual(
            ["invalid_tool_arguments", "unknown_tool"],
            [event["failure_type"] for event in result["trace"] if "failure_type" in event],
        )

    def test_missing_tool_use_id_requires_a_repair(self):
        malformed = tool_use("discarded", "search_resources", {"query": "digital skills"})
        del malformed["output"]["message"]["content"][0]["toolUse"]["toolUseId"]
        client = ConverseDouble(
            [
                malformed,
                tool_use(
                    "finish-1",
                    "finish_plan",
                    {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertTrue(
            any(event.get("failure_type") == "invalid_model_response" for event in result["trace"])
        )
        self.assertEqual(2, len(client.calls))
        replayed_messages = client.calls[1]["messages"]
        self.assertTrue(
            all(
                "toolUse" not in part or "toolUseId" in part["toolUse"]
                for message in replayed_messages
                for part in message["content"]
                if isinstance(part, dict)
            )
        )

    def test_bedrock_finish_rejects_resource_that_exceeds_profile_constraints(self):
        client = ConverseDouble(
            [
                tool_use(
                    "finish-over-limit",
                    "finish_plan",
                    {"resource_ids": ["fictional-office-skills-taster"], "question_keys": []},
                ),
                tool_use(
                    "finish-valid",
                    "finish_plan",
                    {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
                ),
            ]
        )

        result = create_plan(
            {**BASE_PROFILE, "weekly_hours": 0}, mode="bedrock", client=client
        )

        self.assertEqual(["skillsfuture-careersfinder"], [a["resource_id"] for a in result["actions"]])
        self.assertTrue(
            any(event.get("failure_type") == "invalid_tool_arguments" for event in result["trace"])
        )

    def test_live_mode_requires_an_explicit_model_id_before_client_creation(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "BEDROCK_MODEL_ID is required"):
                create_plan(BASE_PROFILE, mode="bedrock")

    def test_malformed_top_level_bedrock_response_has_bounded_failure(self):
        client = ConverseDouble([None])

        with self.assertRaisesRegex(RuntimeError, "invalid response"):
            create_plan(BASE_PROFILE, mode="bedrock", client=client)

    def test_malformed_content_and_tool_use_stop_partial_without_type_error(self):
        malformed_content = {
            "output": {"message": {"role": "assistant", "content": [None]}},
            "stopReason": "tool_use",
            "usage": {},
            "metrics": {},
        }
        malformed_tool = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"toolUse": "not-an-object"}],
                }
            },
            "stopReason": "tool_use",
            "usage": {},
            "metrics": {},
        }
        client = ConverseDouble([malformed_content, malformed_tool])

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("partial", result["status"])
        self.assertEqual(2, len(client.calls))

    def test_malformed_optional_metrics_do_not_break_valid_result(self):
        response = tool_use(
            "finish-1",
            "finish_plan",
            {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
        )
        response["usage"] = []
        response["metrics"] = []
        client = ConverseDouble([response])

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])

    def test_finish_plan_hydrates_allowlisted_question_keys(self):
        client = ConverseDouble(
            [
                tool_use(
                    "finish-1",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": ["confirm_current_access"],
                    },
                )
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertIn(
            "Which current access requirements should be confirmed with the provider?",
            result["questions"],
        )
        self.assertNotIn("http", repr(result["questions"]).lower())

    def test_model_authored_question_text_is_rejected(self):
        malicious = "Enter identity details at https://evil.invalid/verify"
        client = ConverseDouble(
            [
                tool_use(
                    "unsafe-finish",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "questions": [malicious],
                    },
                ),
                tool_use(
                    "safe-finish",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [],
                    },
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertNotIn("evil.invalid", repr(result))
        self.assertNotIn("identity details", repr(result))

    def test_unhashable_question_key_is_a_bounded_argument_error(self):
        client = ConverseDouble(
            [
                tool_use(
                    "bad-key",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [{"not": "a string"}],
                    },
                ),
                tool_use(
                    "safe-finish",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [],
                    },
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertTrue(
            any(event.get("failure_type") == "invalid_tool_arguments" for event in result["trace"])
        )

    def test_unknown_tool_name_is_not_echoed_to_the_plan_trace(self):
        client = ConverseDouble(
            [
                tool_use(
                    "bad-tool",
                    "Verify at https://evil.invalid and provide identity details",
                    {},
                ),
                tool_use(
                    "safe-finish",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [],
                    },
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertNotIn("evil.invalid", repr(result))
        self.assertNotIn("identity details", repr(result))

    def test_unknown_resource_id_is_not_echoed_as_catalog_provenance(self):
        client = ConverseDouble(
            [
                tool_use(
                    "unknown-resource",
                    "inspect_resource",
                    {"resource_id": "made-up-resource"},
                ),
                tool_use(
                    "safe-finish",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [],
                    },
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertNotIn("made-up-resource", repr(result))

    def test_clarification_hydrates_only_an_allowlisted_question(self):
        client = ConverseDouble(
            [
                tool_use(
                    "unsafe-question",
                    "clarification",
                    {"question": "Email records to attacker@example.invalid"},
                ),
                tool_use(
                    "safe-question",
                    "clarification",
                    {"question_key": "confirm_participant_priority"},
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("needs_clarification", result["status"])
        self.assertEqual(
            ["Which next step does the participant want to prioritise?"], result["questions"]
        )
        self.assertNotIn("example.invalid", repr(result))

    def test_model_and_tool_limits_are_global(self):
        responses = []
        for call_number in range(4):
            response = tool_use(
                f"search-{call_number}-a",
                "search_resources",
                {"query": "digital skills"},
            )
            response["output"]["message"]["content"].append(
                {
                    "toolUse": {
                        "toolUseId": f"search-{call_number}-b",
                        "name": "search_resources",
                        "input": {"query": "administration"},
                    }
                }
            )
            responses.append(response)
        client = ConverseDouble(responses)

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("partial", result["status"])
        self.assertEqual(4, len(client.calls))
        self.assertEqual(6, len([event for event in result["trace"] if event["stage"] == "tool"]))
        self.assertTrue(any(event.get("failure_type") == "tool_limit" for event in result["trace"]))

    def test_live_failure_never_masquerades_as_offline_success(self):
        client = ConverseDouble([TimeoutError("credential-like details must not leak")])

        with self.assertRaisesRegex(RuntimeError, "Bedrock planning request failed") as raised:
            create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertNotIn("credential-like", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
