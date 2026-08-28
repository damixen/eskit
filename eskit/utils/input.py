def confirm_delete(kind, name):
    print(f"About to delete {kind}: {name}")
    x = input("Confirm delete by typing the name:")
    return x == name
