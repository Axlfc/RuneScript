import requests

# Sending the query in the get request parameter
query = "How to print hello world in python"
url = f'http://localhost:8004/query-stream/?query={query}'

with requests.get(url, stream=True) as r:
    for chunk in r.iter_content(1024):
        print(chunk.decode('utf-8'), end="")