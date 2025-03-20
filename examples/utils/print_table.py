"""
Utility functions for Namecheap examples.
"""


def print_table(headers, rows):
    """
    Print data in a nicely formatted table.

    Args:
        headers: List of column header strings
        rows: List of lists, where each inner list is a row of data

    Example:
        headers = ["Name", "Age", "City"]
        rows = [
            ["John", 30, "New York"],
            ["Alice", 25, "Los Angeles"]
        ]
        print_table(headers, rows)
    """
    # Calculate column widths based on the longest item in each column
    col_widths = []
    for i in range(len(headers)):
        col_width = len(str(headers[i]))
        for row in rows:
            col_width = max(col_width, len(str(row[i])))
        col_widths.append(col_width + 2)  # Add some padding

    # Print headers
    header_row = ""
    for i, header in enumerate(headers):
        header_row += f"{header:<{col_widths[i]}}"
    print(header_row)

    # Print separator
    separator = ""
    for width in col_widths:
        separator += "-" * width
    print(separator)

    # Print rows
    for row in rows:
        row_str = ""
        for i, cell in enumerate(row):
            row_str += f"{str(cell):<{col_widths[i]}}"
        print(row_str)
