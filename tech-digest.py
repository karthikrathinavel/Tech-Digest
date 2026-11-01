import requests

def push_via_ntfy(title, markdown_summary, article_url):
    requests.post(
        "https://ntfy.sh/tech-digest-karthik",
        data=markdown_summary.encode("utf-8"),
        headers={
            "Title": f"Tech Digest: {title[:50]}",
            "Priority": "high",
            "Tags": "books,bulb",
            "Actions": f"view, Open Source Article, {article_url}",
        }
    )
push_via_ntfy(
    "The Art of Computer Programming",
    "A comprehensive monograph written by Donald Knuth that covers many kinds of programming algorithms and their analysis.",
    "https://en.wikipedia.org/wiki/The_Art_of_Computer_Programming"
)  