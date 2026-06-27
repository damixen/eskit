def confirm_delete(kind, name):
    print(f"About to delete {kind}: {name}\n")
    x = input("Confirm delete by typing:")
    print("\n")
    return x == name
