import json

def render_task_get(result, context=None):
    print(json.dumps(result, indent=2))