import re
from langchain_core.messages import AIMessage


def normalize_markdown_tables(text: str) -> str:
    """
    Normalize Markdown tables so that each table row appears
    on its own line.

    Example input:
        | Name | Price | | AAPL | $210 | | MSFT | $500 |

    Output:
        | Name | Price |
        | AAPL | $210 |
        | MSFT | $500 |
    """

    if not text or "|" not in text:
        return text

    lines = text.splitlines()
    output = []

    in_table = False

    for line in lines:
        stripped = line.strip()

        # Detect a markdown table row
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True

            # If multiple table rows are accidentally on one line,
            # split them when we find "| |"
            parts = re.split(r"\|\s*(?=\|)", stripped)

            # The above can be unreliable for normal cells,
            # so handle the common malformed pattern explicitly.
            if "||" in stripped:
                rows = re.split(r"\s*\|\|\s*", stripped)

                for row in rows:
                    row = row.strip()

                    if not row:
                        continue

                    if not row.startswith("|"):
                        row = "|" + row

                    if not row.endswith("|"):
                        row = row + "|"

                    output.append(row)
            else:
                output.append(stripped)

        else:
            in_table = False
            output.append(line)

    return "\n".join(output)