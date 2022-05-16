import json
from sys import argv
from json import dumps
from requests import get

T = set(["INTERMEDIARY", "BOTH"])

def download(url: str) -> dict:
    print(url)
    try:
        return get(url).json()
    except json.decoder.JSONDecodeError:
        return {"sellers": []}

def recursive_build_json(url: str) -> dict:
    sellers = download(url)["sellers"]
    for s in sellers:
        if s["seller_type"] in T:
            s["sellers.json"] = recursive_build_json(f"http://{s['domain']}/sellers.json")

    return sellers



def save_json(in_: dict, file_path) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(dumps(in_, indent=4))

if __name__ == "__main__":
    #save_json(recursive_build_json(argv[1]), argv[2])
    openx = "https://openx.com/sellers.json"
    print(len(get(openx).json()["sellers"]))

    domains = set([s["domain"] for s in download(openx)["sellers"]])
    print(len(domains))
    #for domain in :
    #    print(domain)