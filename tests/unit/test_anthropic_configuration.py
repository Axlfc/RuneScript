import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.models import anthropic_config


class AnthropicSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env_path = Path(self.temp.name) / ".env"
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.path_patch = patch.object(anthropic_config, "ENV_PATH", self.env_path)
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)

    def test_save_reload_keep_key_and_preserve_other_dotenv_settings(self):
        self.env_path.write_text("OTHER_SETTING=untouched\n", encoding="utf-8")
        anthropic_config.save_anthropic_settings("sk-test", "wrkspc_test", "claude-test")
        anthropic_config.save_anthropic_settings("", "wrkspc_other", "claude-other")
        os.environ.clear()
        self.assertEqual(anthropic_config.load_anthropic_settings(), ("sk-test", "wrkspc_other", "claude-other"))
        self.assertIn("OTHER_SETTING=untouched", self.env_path.read_text(encoding="utf-8"))

    def test_workspace_can_be_cleared_and_process_environment_wins(self):
        anthropic_config.save_anthropic_settings("sk-test", "wrkspc_test", "claude-test")
        anthropic_config.save_anthropic_settings("", "", "claude-test")
        os.environ.clear()
        os.environ["ANTHROPIC_API_KEY"] = "external-key"
        self.assertEqual(anthropic_config.load_anthropic_settings(), ("external-key", "", "claude-test"))

    def test_rejects_invalid_input_without_creating_a_file(self):
        for values in (("", "", "model"), ("ANTHROPIC_API_KEY", "", "model"),
                       ("sk-test\nOTHER=bad", "", "model"), ("sk-test", "", "")):
            with self.subTest(values=values), self.assertRaises(ValueError):
                anthropic_config.save_anthropic_settings(*values)
        self.assertFalse(self.env_path.exists())

    def test_client_sends_workspace_header_only_when_configured(self):
        sdk = types.ModuleType("anthropic")
        sdk.Anthropic = Mock(return_value=object())
        with patch.dict(sys.modules, {"anthropic": sdk}):
            with self.assertRaisesRegex(ValueError, "API key missing"):
                anthropic_config.create_anthropic_client()
            os.environ.update(ANTHROPIC_API_KEY="sk-test", ANTHROPIC_WORKSPACE_ID="wrkspc_test")
            anthropic_config.create_anthropic_client()
            sdk.Anthropic.assert_called_with(api_key="sk-test", default_headers={"anthropic-workspace-id": "wrkspc_test"})
            os.environ["ANTHROPIC_WORKSPACE_ID"] = ""
            anthropic_config.create_anthropic_client()
            sdk.Anthropic.assert_called_with(api_key="sk-test", default_headers=None)

    def test_new_env_file_is_private_on_posix(self):
        anthropic_config.save_anthropic_settings("sk-test", "", "model")
        if os.name == "posix":
            self.assertEqual(self.env_path.stat().st_mode & 0o077, 0)

    def test_project_cli_uses_claude_and_reports_api_failure_to_stderr(self):
        sdk = types.ModuleType("anthropic")
        sdk.APIError = type("APIError", (Exception,), {})
        client = Mock()
        client.messages.create.return_value = types.SimpleNamespace(content=[types.SimpleNamespace(text="project response")])
        sdk.Anthropic = Mock(return_value=client)
        google = types.ModuleType("google")
        google.genai = types.ModuleType("google.genai")
        genai_types = types.ModuleType("google.genai.types")
        genai_types.GenerateContentConfig = genai_types.Part = genai_types.SafetySetting = object
        colorama = types.ModuleType("colorama")
        colorama.init = Mock()
        colorama.Fore = colorama.Back = colorama.Style = object()
        params = types.ModuleType("src.controllers.parameters")
        params.read_config_parameter = lambda key: "claude" if key.endswith("last_selected_llm_server_provider") else None
        exceptions = types.ModuleType("src.core.exceptions")
        exceptions.QuotaExhaustedError = type("QuotaExhaustedError", (Exception,), {})
        modules = {"anthropic": sdk, "google": google, "google.genai": google.genai,
                   "google.genai.types": genai_types, "colorama": colorama,
                   "requests": types.ModuleType("requests"), "openai": types.ModuleType("openai"),
                   "src.controllers.parameters": params, "src.core.exceptions": exceptions}
        os.environ.update(ANTHROPIC_API_KEY="sk-test", ANTHROPIC_WORKSPACE_ID="wrkspc_test", ANTHROPIC_MODEL="claude-test")
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location("test_ai_assistant", Path("src/models/ai_assistant.py"))
            assistant = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(assistant)
            assistant.add_message = Mock()
            output = io.StringIO()
            with patch.object(sys, "argv", ["ai_assistant.py", "project prompt"]), contextlib.redirect_stdout(output):
                assistant.main()
            self.assertEqual(output.getvalue().strip(), "project response")
            self.assertEqual(client.messages.create.call_args.kwargs["model"], "claude-test")
            sdk.Anthropic.assert_called_with(api_key="sk-test", default_headers={"anthropic-workspace-id": "wrkspc_test"})
            with patch.object(assistant, "initialize_claude_client", side_effect=AssertionError("local Ollama selected")):
                self.assertEqual(assistant.AIAssistant().generate("project prompt"), "project response")
            client.messages.create.side_effect = sdk.APIError("unavailable")
            errors = io.StringIO()
            with patch.object(sys, "argv", ["ai_assistant.py", "project prompt"]), contextlib.redirect_stderr(errors):
                with self.assertRaises(SystemExit) as raised:
                    assistant.main()
            self.assertEqual(raised.exception.code, 1)
            self.assertIn("Claude API request failed", errors.getvalue())
            self.assertEqual(assistant.add_message.call_count, 2)


if __name__ == "__main__":
    unittest.main()
