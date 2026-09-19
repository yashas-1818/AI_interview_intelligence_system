from mock_interview.interview.answer_analyzer import analyze_answer


def main():

    print("=" * 70)
    print("ANSWER ANALYZER TEST")
    print("=" * 70)

    test_cases = [

        {
            "question": "Tell me about your machine learning project.",
            "answer": (
                "I worked on a machine learning project using Python "
                "and NLP. I performed data preprocessing, trained the "
                "model, evaluated its performance and deployed the "
                "system through an API."
            ),
        },

        {
            "question": "Explain your experience with Python.",
            "answer": (
                "I have experience with Python."
            ),
        },

        {
            "question": "How did you handle a difficult technical problem?",
            "answer": (
                "I first identified the problem, analyzed the data, "
                "debugged the implementation and then designed a "
                "solution. The result was better system performance."
            ),
        },

        {
            "question": "Explain your project architecture.",
            "answer": "",
        },
    ]

    for index, case in enumerate(
        test_cases,
        start=1,
    ):

        print(f"\n[TEST {index}]")
        print("-" * 70)

        result = analyze_answer(
            question=case["question"],
            answer=case["answer"],
        )

        print(
            f"Question: {case['question']}"
        )

        print(
            f"Answer: {case['answer']}"
        )

        print(
            f"Quality: {result['quality']}"
        )

        print(
            f"Score: {result['score']}"
        )

        print(
            f"Needs follow-up: "
            f"{result['needs_followup']}"
        )

        print(
            f"Follow-up action: "
            f"{result['followup_action']}"
        )

        print(
            f"Technical depth: "
            f"{result['technical_depth_level']}"
        )

        print(
            f"Completeness: "
            f"{result['completeness_level']}"
        )

        print(
            f"Clarity: "
            f"{result['clarity_level']}"
        )

        print(
            f"Vagueness: "
            f"{result['vagueness_level']}"
        )

        print(
            f"Topics: "
            f"{result['answer_topics']['topics']}"
        )

        print(
            f"Follow-up targets: "
            f"{result['follow_up_targets']['targets']}"
        )

    print("\n" + "=" * 70)
    print("ANSWER ANALYZER TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()