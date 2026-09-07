from copy import deepcopy
import json
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
        self.calls.append(deepcopy(kwargs))
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
        careers = next(
            action for action in result["actions"]
            if action["resource_id"] == "skillsfuture-careersfinder"
        )
        self.assertEqual("https://www.myskillsfuture.gov.sg/csp", careers["source_url"])

    def test_singapore_job_support_draft_keeps_provider_checks_for_zero_budget_and_hours(self):
        result = create_plan(
            {
                **BASE_PROFILE,
                "goal": "Explore job coaching and workplace accessibility",
                "strengths": "",
                "interests": ["job support", "workplace support"],
                "full_time_student": False,
                "weekly_hours": 0,
                "budget_sgd": 0,
            }
        )

        actions = {action["resource_id"]: action for action in result["actions"]}
        self.assertEqual("draft", result["status"])
        self.assertIn("sg-enable-job-placement-support", actions)
        action = actions["sg-enable-job-placement-support"]
        self.assertEqual(
            "https://www.enablingguide.sg/im-looking-for-disability-support/"
            "training-employment/job-placement-and-job-support",
            action["source_url"],
        )
        for unresolved in ("eligibility", "weekly hours", "cost"):
            self.assertTrue(any(unresolved in check.lower() for check in action["checks"]))

    def test_student_can_explore_singapore_course_directory_with_unconfirmed_access(self):
        result = create_plan(
            {
                **BASE_PROFILE,
                "goal": "Explore vocational courses and independent living skills",
                "strengths": "",
                "interests": ["work readiness"],
                "full_time_student": True,
                "weekly_hours": 0,
                "budget_sgd": 0,
            }
        )

        actions = {action["resource_id"]: action for action in result["actions"]}
        self.assertEqual("draft", result["status"])
        self.assertIn("enabling-academy-courses", actions)
        self.assertNotIn("sg-enable-sector-train-place", actions)
        action = actions["enabling-academy-courses"]
        self.assertEqual(
            "https://www.sgenable.sg/your-first-stop/training-consultancy/"
            "enabling-academy/training/persons-with-disabilities/programmes",
            action["source_url"],
        )
        for unresolved in ("eligibility", "student", "weekly hours", "cost", "intake"):
            self.assertTrue(any(unresolved in check.lower() for check in action["checks"]))

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
        self.assertEqual(1, len([event for event in result["trace"] if event["stage"] == "model"]))

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

        specs = {
            tool["toolSpec"]["name"]: tool["toolSpec"]["inputSchema"]["json"]
            for tool in client.calls[0]["toolConfig"]["tools"]
        }
        self.assertEqual(
            {"confirm_student_status"},
            set(specs["clarification"]["properties"]["question_key"]["enum"]),
        )
        self.assertTrue(
            {
                "confirm_current_access",
                "confirm_participant_priority",
                "confirm_support_preference",
            }.issubset(
                set(specs["finish_plan"]["properties"]["question_keys"]["items"]["enum"])
            )
        )

    def test_complete_profile_omits_clarification_from_outbound_tools(self):
        complete = {
            **BASE_PROFILE,
            "full_time_student": False,
            "weekly_hours": 3,
            "budget_sgd": 0,
        }
        client = ConverseDouble(
            [
                tool_use(
                    "finish-1",
                    "finish_plan",
                    {
                        "resource_ids": ["fictional-office-skills-taster"],
                        "question_keys": [],
                    },
                )
            ]
        )

        result = create_plan(complete, mode="bedrock", client=client)

        tool_config = client.calls[0]["toolConfig"]
        names = {tool["toolSpec"]["name"] for tool in tool_config["tools"]}
        self.assertEqual({"finish_plan"}, names)
        self.assertEqual({"tool": {"name": "finish_plan"}}, tool_config["toolChoice"])
        self.assertEqual("draft", result["status"])

    def test_complete_broad_profile_receives_detailed_constrained_shortlist(self):
        profile = {
            **BASE_PROFILE,
            "goal": "Explore office skills at my own pace",
            "strengths": "Organising files and following a checklist",
            "interests": ["office", "organising", "computers"],
            "full_time_student": False,
            "weekly_hours": 3,
            "budget_sgd": 0,
        }
        client = ConverseDouble(
            [
                tool_use(
                    "finish-1",
                    "finish_plan",
                    {
                        "resource_ids": ["fictional-office-skills-taster"],
                        "question_keys": [],
                    },
                )
            ]
        )

        result = create_plan(profile, mode="bedrock", client=client)

        finish_schema = next(
            tool["toolSpec"]["inputSchema"]["json"]
            for tool in client.calls[0]["toolConfig"]["tools"]
            if tool["toolSpec"]["name"] == "finish_plan"
        )
        self.assertIn("enum", finish_schema["properties"]["resource_ids"]["items"])
        self.assertEqual(
            [
                "fictional-office-skills-taster",
                "sg-enable-sector-train-place",
                "skillsfuture-careersfinder",
            ],
            finish_schema["properties"]["resource_ids"]["items"]["enum"],
        )
        payload = json.loads(
            client.calls[0]["messages"][0]["content"][0]["text"].split(": ", 1)[1]
        )
        self.assertEqual(
            [
                "fictional-office-skills-taster",
                "sg-enable-sector-train-place",
                "skillsfuture-careersfinder",
            ],
            [item["id"] for item in payload["shortlist"]],
        )
        self.assertTrue(
            all(
                {"checked_date", "unknowns", "next_step"}.issubset(item)
                for item in payload["shortlist"]
            )
        )
        self.assertEqual("draft", result["status"])
        self.assertEqual(1, len(client.calls))

    def test_finish_rejects_eligible_resource_outside_request_shortlist(self):
        profile = {
            **BASE_PROFILE,
            "goal": "Explore office skills at my own pace",
            "strengths": "Organising files and following a checklist",
            "interests": ["office", "organising", "computers"],
            "full_time_student": False,
            "weekly_hours": 3,
            "budget_sgd": 0,
        }
        client = ConverseDouble(
            [
                tool_use(
                    "outside-shortlist",
                    "finish_plan",
                    {"resource_ids": ["career-kaki"], "question_keys": []},
                ),
                tool_use(
                    "finish-valid",
                    "finish_plan",
                    {
                        "resource_ids": ["fictional-office-skills-taster"],
                        "question_keys": [],
                    },
                ),
            ]
        )

        result = create_plan(profile, mode="bedrock", client=client)

        self.assertEqual(
            ["fictional-office-skills-taster"],
            [action["resource_id"] for action in result["actions"]],
        )
        self.assertEqual(2, len(client.calls))
        self.assertIn(
            "resource_outside_shortlist",
            [event.get("failure_type") for event in result["trace"]],
        )
        self.assertNotIn("career-kaki", repr(result))

    def test_no_matching_shortlist_stops_without_model_call(self):
        client = ConverseDouble(
            [
                tool_use(
                    "unexpected-finish",
                    "finish_plan",
                    {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
                )
            ]
        )
        profile = {
            **BASE_PROFILE,
            "goal": "Quartz xylophone",
            "strengths": "",
            "interests": [],
            "full_time_student": False,
        }

        result = create_plan(profile, mode="bedrock", client=client)

        self.assertEqual("partial", result["status"])
        self.assertEqual([], client.calls)
        self.assertIn("no_shortlist", [event.get("failure_type") for event in result["trace"]])

    def test_multiple_tool_calls_require_one_repair(self):
        multiple = tool_use(
            "finish-a",
            "finish_plan",
            {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
        )
        multiple["output"]["message"]["content"].append(
            {
                "toolUse": {
                    "toolUseId": "finish-b",
                    "name": "finish_plan",
                    "input": {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [],
                    },
                }
            }
        )
        client = ConverseDouble(
            [
                multiple,
                tool_use(
                    "finish-valid",
                    "finish_plan",
                    {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertEqual(2, len(client.calls))
        self.assertIn(
            "invalid_model_response",
            [event.get("failure_type") for event in result["trace"]],
        )

    def test_truncated_tool_response_requires_one_repair(self):
        truncated = tool_use(
            "finish-truncated",
            "finish_plan",
            {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
        )
        truncated["stopReason"] = "max_tokens"
        client = ConverseDouble(
            [
                truncated,
                tool_use(
                    "finish-valid",
                    "finish_plan",
                    {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertEqual(2, len(client.calls))
        self.assertIn(
            "invalid_model_response",
            [event.get("failure_type") for event in result["trace"]],
        )

    def test_outbound_clarification_enum_contains_only_null_profile_fields(self):
        profile = {
            **BASE_PROFILE,
            "full_time_student": None,
            "weekly_hours": 3,
            "budget_sgd": None,
        }
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

        create_plan(profile, mode="bedrock", client=client)

        clarification = next(
            tool
            for tool in client.calls[0]["toolConfig"]["tools"]
            if tool["toolSpec"]["name"] == "clarification"
        )
        enum = clarification["toolSpec"]["inputSchema"]["json"]["properties"][
            "question_key"
        ]["enum"]
        self.assertEqual({"confirm_student_status", "confirm_budget_sgd"}, set(enum))
        tool_config = client.calls[0]["toolConfig"]
        self.assertIn("toolChoice", tool_config)
        self.assertEqual({"any": {}}, tool_config["toolChoice"])
        self.assertEqual(
            {"finish_plan", "clarification"},
            {tool["toolSpec"]["name"] for tool in tool_config["tools"]},
        )
        finish = next(
            tool
            for tool in tool_config["tools"]
            if tool["toolSpec"]["name"] == "finish_plan"
        )
        self.assertEqual(
            {
                "confirm_current_access",
                "confirm_participant_priority",
                "confirm_support_preference",
                "confirm_student_status",
                "confirm_budget_sgd",
            },
            set(
                finish["toolSpec"]["inputSchema"]["json"]["properties"][
                    "question_keys"
                ]["items"]["enum"]
            ),
        )

    def test_request_local_tool_specs_do_not_leak_between_profiles(self):
        null_client = ConverseDouble(
            [
                tool_use(
                    "ask-budget",
                    "clarification",
                    {"question_key": "confirm_budget_sgd"},
                )
            ]
        )
        complete_client = ConverseDouble(
            [
                tool_use(
                    "finish-1",
                    "finish_plan",
                    {
                        "resource_ids": ["fictional-office-skills-taster"],
                        "question_keys": [],
                    },
                )
            ]
        )
        null_profile = {
            **BASE_PROFILE,
            "full_time_student": False,
            "weekly_hours": 3,
            "budget_sgd": None,
        }
        complete_profile = {**null_profile, "budget_sgd": 0}

        create_plan(null_profile, mode="bedrock", client=null_client)
        create_plan(complete_profile, mode="bedrock", client=complete_client)

        null_names = {
            tool["toolSpec"]["name"] for tool in null_client.calls[0]["toolConfig"]["tools"]
        }
        complete_names = {
            tool["toolSpec"]["name"]
            for tool in complete_client.calls[0]["toolConfig"]["tools"]
        }
        self.assertIn("clarification", null_names)
        self.assertNotIn("clarification", complete_names)

    def test_request_local_shortlist_ids_do_not_leak_between_profiles(self):
        broad_profile = {
            **BASE_PROFILE,
            "goal": "Explore office skills at my own pace",
            "strengths": "Organising files and following a checklist",
            "interests": ["office", "organising", "computers"],
            "full_time_student": False,
            "weekly_hours": 3,
            "budget_sgd": 0,
        }
        software_profile = {
            **BASE_PROFILE,
            "goal": "Explore software skills",
            "strengths": "using computers",
            "interests": ["software", "digital skills"],
            "full_time_student": False,
            "weekly_hours": 3,
            "budget_sgd": 0,
        }
        broad_client = ConverseDouble(
            [
                tool_use(
                    "finish-broad",
                    "finish_plan",
                    {
                        "resource_ids": ["fictional-office-skills-taster"],
                        "question_keys": [],
                    },
                )
            ]
        )
        software_client = ConverseDouble(
            [
                tool_use(
                    "finish-software",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [],
                    },
                )
            ]
        )

        create_plan(broad_profile, mode="bedrock", client=broad_client)
        create_plan(software_profile, mode="bedrock", client=software_client)

        def allowed_ids(client):
            finish = next(
                tool
                for tool in client.calls[0]["toolConfig"]["tools"]
                if tool["toolSpec"]["name"] == "finish_plan"
            )
            items = finish["toolSpec"]["inputSchema"]["json"]["properties"][
                "resource_ids"
            ]["items"]
            self.assertIn("enum", items)
            return items["enum"]

        self.assertEqual(
            [
                "fictional-office-skills-taster",
                "sg-enable-sector-train-place",
                "skillsfuture-careersfinder",
            ],
            allowed_ids(broad_client),
        )
        self.assertEqual(
            [
                "sg-enable-sector-train-place",
                "skillsfuture-careersfinder",
                "career-kaki",
            ],
            allowed_ids(software_client),
        )

    def test_invalid_model_arguments_get_one_bounded_repair_then_stop(self):
        client = ConverseDouble(
            [
                tool_use(
                    "bad-1",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [],
                        "url": "https://evil.invalid",
                    },
                ),
                tool_use("bad-2", "browse_web", {"url": "https://evil.invalid"}),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("partial", result["status"])
        self.assertEqual([], result["actions"])
        self.assertEqual(2, len(client.calls))
        self.assertEqual(
            ["invalid_tool_arguments", "unknown_tool", "repair_limit"],
            [event["failure_type"] for event in result["trace"] if "failure_type" in event],
        )

    def test_missing_tool_use_id_requires_a_repair(self):
        malformed = tool_use(
            "discarded",
            "finish_plan",
            {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
        )
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
            any(
                event.get("failure_type") == "resource_outside_shortlist"
                for event in result["trace"]
            )
        )

    def test_live_mode_requires_an_explicit_model_id_before_client_creation(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "BEDROCK_MODEL_ID is required"):
                create_plan(BASE_PROFILE, mode="bedrock")

    def test_malformed_top_level_bedrock_response_gets_one_repair(self):
        client = ConverseDouble(
            [
                None,
                tool_use(
                    "finish-valid",
                    "finish_plan",
                    {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertEqual(2, len(client.calls))
        self.assertIn(
            "invalid_model_response",
            [event.get("failure_type") for event in result["trace"]],
        )
        retry_messages = client.calls[1]["messages"]
        self.assertEqual(["user"], [message["role"] for message in retry_messages])
        retry_text = " ".join(part["text"] for part in retry_messages[0]["content"])
        self.assertIn('"profile"', retry_text)
        self.assertIn('"shortlist"', retry_text)
        self.assertIn("invalid_model_response", retry_text)

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

        self.assertEqual("draft", result["status"])
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
            any(event.get("failure_type") == "invalid_question_keys" for event in result["trace"])
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
                    "finish_plan",
                    {"resource_ids": ["made-up-resource"], "question_keys": []},
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
        self.assertIn(
            "resource_outside_shortlist",
            [event.get("failure_type") for event in result["trace"]],
        )

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
                    {"question_key": "confirm_budget_sgd"},
                ),
            ]
        )

        result = create_plan(
            {**BASE_PROFILE, "budget_sgd": None}, mode="bedrock", client=client
        )

        self.assertEqual("needs_clarification", result["status"])
        self.assertEqual(
            ["What budget in Singapore dollars should this plan stay within?"],
            result["questions"],
        )
        self.assertNotIn("example.invalid", repr(result))

    def test_clarification_rejects_budget_question_when_zero_is_known(self):
        client = ConverseDouble(
            [
                tool_use(
                    "redundant-budget",
                    "clarification",
                    {"question_key": "confirm_budget_sgd"},
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
        self.assertFalse(any("budget" in question.lower() for question in result["questions"]))
        self.assertTrue(
            any(event.get("failure_type") == "invalid_question_keys" for event in result["trace"])
        )

    def test_finish_rejects_questions_for_known_false_and_zero_constraints(self):
        known_profile = {
            **BASE_PROFILE,
            "full_time_student": False,
            "weekly_hours": 0,
            "budget_sgd": 0,
        }
        client = ConverseDouble(
            [
                tool_use(
                    "redundant-questions",
                    "finish_plan",
                    {
                        "resource_ids": ["skillsfuture-careersfinder"],
                        "question_keys": [
                            "confirm_student_status",
                            "confirm_weekly_hours",
                            "confirm_budget_sgd",
                        ],
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

        result = create_plan(known_profile, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertEqual([], result["questions"])
        self.assertTrue(
            any(event.get("failure_type") == "invalid_question_keys" for event in result["trace"])
        )

    def test_constraint_question_key_remains_valid_when_value_is_unknown(self):
        client = ConverseDouble(
            [
                tool_use(
                    "ask-budget",
                    "clarification",
                    {"question_key": "confirm_budget_sgd"},
                )
            ]
        )

        result = create_plan(
            {**BASE_PROFILE, "budget_sgd": None}, mode="bedrock", client=client
        )

        self.assertEqual("needs_clarification", result["status"])
        self.assertEqual(
            ["What budget in Singapore dollars should this plan stay within?"],
            result["questions"],
        )

    def test_access_clarification_repairs_to_explicit_fictional_rehearsal_draft(self):
        profile = {
            **BASE_PROFILE,
            "goal": (
                "Rehearse the fictional community office-skills taster slot only. "
                "Draft an exploratory practice plan; no real provider application or "
                "eligibility decision is needed."
            ),
            "full_time_student": False,
            "weekly_hours": 2,
            "budget_sgd": 0,
        }
        client = ConverseDouble(
            [
                tool_use(
                    "invalid-access-question",
                    "clarification",
                    {"question_key": "confirm_current_access"},
                ),
                tool_use(
                    "finish-fictional",
                    "finish_plan",
                    {
                        "resource_ids": ["fictional-office-skills-taster"],
                        "question_keys": [],
                    },
                ),
            ]
        )

        result = create_plan(profile, mode="bedrock", client=client)

        self.assertEqual("draft", result["status"])
        self.assertEqual(
            ["fictional-office-skills-taster"],
            [action["resource_id"] for action in result["actions"]],
        )
        self.assertEqual([], result["questions"])
        self.assertEqual(2, len([event for event in result["trace"] if event["stage"] == "model"]))
        self.assertTrue(
            any(event.get("failure_type") == "invalid_question_keys" for event in result["trace"])
        )
        self.assertTrue(
            any("cannot be enrolled" in check.lower() for check in result["actions"][0]["checks"])
        )

    def test_priority_and_support_are_finish_followups_not_clarification_blockers(self):
        profile = {**BASE_PROFILE, "supporter_goal": BASE_PROFILE["goal"]}

        for question_key in ("confirm_participant_priority", "confirm_support_preference"):
            with self.subTest(question_key=question_key):
                client = ConverseDouble(
                    [
                        tool_use(
                            "invalid-clarification",
                            "clarification",
                            {"question_key": question_key},
                        ),
                        tool_use(
                            "finish-after-repair",
                            "finish_plan",
                            {
                                "resource_ids": ["skillsfuture-careersfinder"],
                                "question_keys": [question_key],
                            },
                        ),
                    ]
                )

                result = create_plan(profile, mode="bedrock", client=client)

                self.assertEqual("draft", result["status"])
                self.assertEqual(1, len(result["actions"]))
                self.assertTrue(result["questions"])
                self.assertTrue(
                    any(
                        event.get("failure_type") == "invalid_question_keys"
                        for event in result["trace"]
                    )
                )

    def test_repair_limit_is_two_model_calls(self):
        client = ConverseDouble(
            [
                tool_use("unknown-1", "browse_web", {}),
                tool_use("unknown-2", "browse_web", {}),
                tool_use(
                    "must-not-run",
                    "finish_plan",
                    {"resource_ids": ["skillsfuture-careersfinder"], "question_keys": []},
                ),
            ]
        )

        result = create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertEqual("partial", result["status"])
        self.assertEqual(2, len(client.calls))
        self.assertEqual(2, len([event for event in result["trace"] if event["stage"] == "tool"]))
        self.assertEqual(1, len(client.responses))
        self.assertTrue(any(event.get("failure_type") == "repair_limit" for event in result["trace"]))

    def test_live_failure_never_masquerades_as_offline_success(self):
        client = ConverseDouble([TimeoutError("credential-like details must not leak")])

        with self.assertRaisesRegex(RuntimeError, "Bedrock planning request failed") as raised:
            create_plan(BASE_PROFILE, mode="bedrock", client=client)

        self.assertNotIn("credential-like", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
