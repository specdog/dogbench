def slugify(text):
    return text.lower().replace(" ", "-")

def truncate(text, n):
    return text[:n] + "..." if len(text) > n else text
