import requests


def getrev():
    resp = requests.get("https://pypi.org/pypi/TwitchIO/json")
    data = resp.json()["releases"]

    pre = max(data).split("b")
    final = f"{pre[0]}b{int(pre[1]) + 1}"

    return final


getrev()
