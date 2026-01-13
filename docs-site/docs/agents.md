# Supported AI Agents (Fork)

After `specify init`, slash commands are generated for the agent you select. Use `--ai <agent>` to pick the integration.

## Agents

| `--ai` value | Agent | Type | Install URL | Folder |
| --- | --- | --- | --- | --- |
| `claude` | Claude Code | CLI | https://docs.anthropic.com/en/docs/claude-code/setup | `.claude/` |
| `gemini` | Gemini CLI | CLI | https://github.com/google-gemini/gemini-cli | `.gemini/` |
| `qwen` | Qwen Code | CLI | https://github.com/QwenLM/qwen-code | `.qwen/` |
| `opencode` | opencode | CLI | https://opencode.ai | `.opencode/` |
| `codex` | Codex CLI | CLI | https://github.com/openai/codex | `.codex/` |
| `auggie` | Auggie CLI | CLI | https://docs.augmentcode.com/cli/setup-auggie/install-auggie-cli | `.augment/` |
| `codebuddy` | CodeBuddy CLI | CLI | https://www.codebuddy.ai/cli | `.codebuddy/` |
| `qoder` | Qoder CLI | CLI | https://qoder.com/cli | `.qoder/` |
| `q` | Amazon Q Developer CLI | CLI | https://aws.amazon.com/developer/learning/q-developer-cli/ | `.amazonq/` |
| `amp` | Amp | CLI | https://ampcode.com/manual#install | `.agents/` |
| `shai` | SHAI | CLI | https://github.com/ovh/shai | `.shai/` |
| `copilot` | GitHub Copilot | IDE | — | `.github/` |
| `cursor-agent` | Cursor | IDE | — | `.cursor/` |
| `windsurf` | Windsurf | IDE | — | `.windsurf/` |
| `kilocode` | Kilo Code | IDE | — | `.kilocode/` |
| `roo` | Roo Code | IDE | — | `.roo/` |
| `bob` | IBM Bob | IDE | — | `.bob/` |

## Notes

- CLI-based agents are validated during `specify init` unless you pass `--ignore-agent-tools`.
- IDE-based agents do not require a CLI tool check.
