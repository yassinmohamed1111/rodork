
---

## 4. CONTRIBUTING.md

```markdown
# Contributing to RoDork

Thank you for helping improve RoDork! This guide explains how to add dorks, fix bugs, and extend the tool.

## Adding Dorks
1. Edit `data/dorks.json` or use the interactive `add_dork` command inside the shell.
2. Each dork must have:
   - `id`: unique string (user dorks start with 'u', official with 'd' or 'n')
   - `query`: the Shodan search string
   - `category`: one of `manufacturer`, `protocol`, `technology`, `simulation`, `cloud`, `tool`, `config`, `accessory`
   - `description`: short explanation
   - `risk_level`: `critical`, `high`, `medium`, or `low`
   - `source`: `"new"` if you contribute, or `"user"` if added via CLI
   - `date_added`: date string

3. Verify your dork does not duplicate an existing one. Run `list_dorks` inside RoDork to see all.
4. Open a pull request with your changes.

## Extending the Tool
- The code is modular: `shodan_client.py` handles API, `filter_engine.py` contains risk logic and filtering, `output_formatter.py` displays results.
- To add new filter criteria, modify `apply_filters()` in `filter_engine.py`.
- To improve risk assessment, edit `calculate_risk()`.

## Code Style
- Follow PEP8.
- Use meaningful variable names.
- Test your changes locally before submitting a PR.

## Questions?
Open an issue on GitHub.
