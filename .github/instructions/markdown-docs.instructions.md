---
applyTo: "**/*.md"
---

# Markdown Documentation Instructions

When editing Markdown files in this repository, follow these guidelines:

## Linting Requirements

**ALWAYS** run the markdown linter before committing:

```bash
npx markdownlint-cli2 "**/*.md"
```

The project uses `.markdownlint-cli2.jsonc` for configuration.

## Markdown Standards

1. **Headers**: Use ATX-style headers (`#`, `##`, `###`)
2. **Lists**: Use 2-space indentation for nested lists
3. **Emphasis**: Use asterisks for bold (`**bold**`) and italic (`*italic*`)
4. **Code Blocks**: Always specify language for syntax highlighting
5. **Links**: Use reference-style links for repeated URLs when possible
6. **Line Length**: No strict limit (MD013 disabled), but keep it readable

## Documentation Structure

- **README.md**: User-facing documentation, quickstart, installation
- **AGENTS.md**: Technical guide for adding new AI agent support
- **CONTRIBUTING.md**: Contributor guidelines and development workflow
- **spec-driven.md**: Spec-Driven Development methodology explanation
- **CHANGELOG.md**: Version history (update when changing CLI)

## Content Guidelines

- Use clear, concise language
- Include code examples for technical concepts
- Keep tables aligned and formatted consistently
- Use emojis sparingly and consistently with existing style
- Maintain consistent terminology across all documentation
- Cross-reference related documents when appropriate

## Special Files

- **Templates** (`templates/*.md`): May contain placeholder variables
- **Agent Commands** (`templates/commands/*.md`): Include frontmatter with `description` field
- **Docs** (`docs/*.md`): More detailed documentation, may have different formatting needs
