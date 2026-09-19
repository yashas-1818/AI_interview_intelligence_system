def extract_job_text(text: str) -> str:
    """
    Clean and normalize job description text.
    """

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


if __name__ == "__main__":
    print("Job parser module loaded successfully.")