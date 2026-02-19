# Contributing to Spec Kit (Fork)

Hi there! Thanks for contributing. This repository is an independent fork of `github/spec-kit` and is not affiliated with GitHub. Contributions to this project are released to the public under the [project's open source license](LICENSE).

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Prerequisites for running and testing code

These are one time installations required to be able to test your changes locally as part of the pull request (PR) submission process.

1. Install [Python 3.11+](https://www.python.org/downloads/)
2. Install [uv](https://docs.astral.sh/uv/) for package management
3. Install [Git](https://git-scm.com/downloads)
4. Have an [AI coding agent available](README.md#-supported-ai-agents)

<details>
<summary><b>💡 Hint if you are using <code>VSCode</code> or <code>GitHub Codespaces</code> as your IDE</b></summary>

<br>

Provided you have [Docker](https://docker.com) installed on your machine, you can leverage [Dev Containers](https://containers.dev) through this [VSCode extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers), to easily set up your development environment, with aforementioned tools already installed and configured, thanks to the `.devcontainer/devcontainer.json` file (located at the root of the project).

To do so, simply:

- Checkout the repo
- Open it with VSCode
- Open the [Command Palette](https://code.visualstudio.com/docs/getstarted/userinterface#_command-palette) and select "Dev Containers: Open Folder in Container..."

On [GitHub Codespaces](https://github.com/features/codespaces) it's even simpler, as it leverages the `.devcontainer/devcontainer.json` automatically upon opening the codespace.

</details>

## Submitting a pull request

> [!NOTE]
> If your pull request introduces a large change that materially impacts the CLI or repository (e.g., new templates, arguments, or other major changes), discuss it with the maintainer first. Large changes without prior agreement may be closed.

1. Fork and clone the repository
2. Configure and install the dependencies: `uv sync`
3. Make sure the CLI works on your machine: `uv run specify --help`
4. Create a new branch: `git checkout -b my-branch-name`
5. Make your change, add tests, and make sure everything still works
6. Test the CLI functionality with a sample project if relevant
7. Push to your fork and submit a pull request
8. Wait for your pull request to be reviewed and merged.

## Issue Taxonomy & Phasing Strategy

To maintain stability while moving fast, we use a **Phased Execution Strategy** for issues.
All engineering tasks must use the `[PhX]` prefix in their title.

### Phase Definitions

| Phase | Description | Parallelism |
| :--- | :--- | :--- |
| **[Ph0] Blockers** | Critical bugs preventing basic usage. Fix immediately. | ❌ Serial |
| **[Ph1] Core Enablers** | Foundation utilities/structs needed by other tasks. | ❌ Serial |
| **[Ph2] Automation** | Core scripts and features. | ✅ Parallel |
| **[Ph3] Integration** | Templates, docs, and metadata linking. | ✅ Parallel |
| **[Ph4] Governance** | Validators and quality gates. | ✅ Parallel |
| **[Ph5] UX & Polish** | Non-blocking improvements. | ✅ Parallel |
| **[Ph6] Backlog** | Future ideas and nice-to-haves. | ✅ Parallel |

**Rules for Agents & Contributors:**
1. **Respect Order:** Do not start a `Ph3` task if `Ph2` dependencies aren't met.
2. **Parallelize:** Tasks with the **same prefix** can be executed concurrently.
3. **Prefixing:** All new technical issues must carry a prefix.

Here are a few things you can do that will increase the likelihood of your pull request being accepted:

- Follow the project's coding conventions.
- Write tests for new functionality.
- Update documentation (`README.md`, `spec-driven.md`) if your changes affect user-facing features.
- Keep your change as focused as possible. If there are multiple changes you would like to make that are not dependent upon each other, consider submitting them as separate pull requests.
- Write a [good commit message](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).
- Test your changes with the Spec-Driven Development workflow to ensure compatibility.

### Upstream PR Policy

If a change is broadly useful to upstream `github/spec-kit`, the maintainer may:

- Ask you to open a corresponding upstream PR, or
- Open one on your behalf with attribution

Fork-specific changes (Phase 0 or distribution overrides) should target this fork only.

## Development workflow

When working on spec-kit:

1. Test changes with the `specify` CLI commands (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks`) in your coding agent of choice
2. Verify templates are working correctly in `templates/` directory
3. Test script functionality in the `scripts/` directory
4. Ensure memory files (`memory/constitution.md`) are updated if major process changes are made

### Testing template and command changes locally

Running `uv run specify init` pulls released packages, which won’t include your local changes.  
To test your templates, commands, and other changes locally, follow these steps:

1. **Create release packages**

   Run the following command to generate the local packages:

   ```bash
   ./.github/workflows/scripts/create-release-packages.sh v1.0.0
   ```

1. **Test with local templates**

   Use the `--local-templates` option to load templates from the local `.genreleases` directory:

   ```bash
   specify init my-test-project --ai claude --local-templates ".genreleases"
   ```

   > **Alternative:** If you prefer not to use the CLI, you can manually copy the package:

   ```bash
   cp -r .genreleases/sdd-copilot-package-sh/. <path-to-test-project>/
   ```

1. **Open and test the agent**

   Navigate to your test project folder and open the agent to verify your implementation.

## AI contributions in Spec Kit

> [!IMPORTANT]
>
> If you are using **any kind of AI assistance** to contribute to Spec Kit,
> it must be disclosed in the pull request or issue.

We welcome and encourage the use of AI tools to help improve Spec Kit! Many valuable contributions have been enhanced with AI assistance for code generation, issue detection, and feature definition.

That being said, if you are using any kind of AI assistance (e.g., agents, ChatGPT) while contributing to Spec Kit,
**this must be disclosed in the pull request or issue**, along with the extent to which AI assistance was used (e.g., documentation comments vs. code generation).

If your PR responses or comments are being generated by an AI, disclose that as well.

As an exception, trivial spacing or typo fixes don't need to be disclosed, so long as the changes are limited to small parts of the code or short phrases.

An example disclosure:

> This PR was written primarily by GitHub Copilot.

Or a more detailed disclosure:

> I consulted ChatGPT to understand the codebase but the solution
> was fully authored manually by myself.

Failure to disclose this is first and foremost rude to the human operators on the other end of the pull request, but it also makes it difficult to
determine how much scrutiny to apply to the contribution.

In a perfect world, AI assistance would produce equal or higher quality work than any human. That isn't the world we live in today, and in most cases
where human supervision or expertise is not in the loop, it's generating code that cannot be reasonably maintained or evolved.

### What we're looking for

When submitting AI-assisted contributions, please ensure they include:

- **Clear disclosure of AI use** - You are transparent about AI use and degree to which you're using it for the contribution
- **Human understanding and testing** - You've personally tested the changes and understand what they do
- **Clear rationale** - You can explain why the change is needed and how it fits within Spec Kit's goals
- **Concrete evidence** - Include test cases, scenarios, or examples that demonstrate the improvement
- **Your own analysis** - Share your thoughts on the end-to-end developer experience

### What we'll close

We reserve the right to close contributions that appear to be:

- Untested changes submitted without verification
- Generic suggestions that don't address specific Spec Kit needs
- Bulk submissions that show no human review or understanding

### Guidelines for success

The key is demonstrating that you understand and have validated your proposed changes. If a maintainer can easily tell that a contribution was generated entirely by AI without human input or testing, it likely needs more work before submission.

Contributors who consistently submit low-effort AI-generated changes may be restricted from further contributions at the maintainers' discretion.

Please be respectful to maintainers and disclose AI assistance.

## Resources

- [Spec-Driven Development Methodology](./spec-driven.md)
- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Help](https://help.github.com)
