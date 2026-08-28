


def render_init(result, context=None):
    print("ESKit initialized.")
    demo = result.get("demo", False)
    if demo:
        print("Demo folder copied.")
