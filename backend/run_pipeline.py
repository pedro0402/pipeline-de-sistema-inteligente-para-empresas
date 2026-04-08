def collect():
    print("collect")
    return []


def process(items):
    print("process")
    return items


def analyze(items):
    print("analyze")
    return items


def report(items):
    print("report")
    return None


def main():
    print("collect")
    items = collect()
    print("process")
    items = process(items)
    print("analyze")
    items = analyze(items)
    print("report")
    report(items)
    return items


if __name__ == "__main__":
    main()
