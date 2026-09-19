from mock_interview.llm.config import (
    get_llm_config,
    validate_llm_config,
)


print("=" * 70)
print("LLM CONFIGURATION TEST")
print("=" * 70)

print()

config = get_llm_config()

for key, value in config.items():
    print(
        f"{key}: {value}"
    )

print()

try:

    validate_llm_config()

    print(
        "Configuration status: VALID"
    )

except ValueError as error:

    print(
        "Configuration status: INVALID"
    )

    print(
        "Error:",
        error
    )

print()
print("=" * 70)
print("LLM CONFIGURATION TEST COMPLETED")
print("=" * 70)