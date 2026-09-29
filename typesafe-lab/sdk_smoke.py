from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
with TypeSafeClient() as client:
    r = client.system_one(
        state={"document": "I was charged twice. Please fix this ASAP."},
        questions={
            "billing": Noul(instructions="Is this ticket about billing?"),
            "tone": Choice(instructions="What is the customer's tone?",
                           criteria={"calm": None, "frustrated": None, "angry": None}),
            "urgency": Score(instructions="How urgent is this ticket?",
                             criteria=["can wait", "this week", "today"]),
        },
    )
    print("model:", getattr(r, "model", "?"))
    print("noul billing   :", r.nouls["billing"].noul)
    print("choice tone    :", r.choices["tone"].choice, "| conf", r.choices["tone"].confidence)
    print("score urgency  :", r.scores["urgency"].score, "| conf", r.scores["urgency"].confidence)
