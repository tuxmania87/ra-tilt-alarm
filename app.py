import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
interval = 5 * 60


def send_to_webhook(url, message):
    requests.post(url, {"content": message})


def check_last_games(username, mode, interval, num_games):
    url = f"https://lichess.org/api/games/user/{username}?sort=dateDesc&max={num_games}&pgnInJson"
    r = requests.get(url, headers={"Accept": "application/x-ndjson"})
    games = [json.loads(x) for x in r.text.strip("\n").split("\n")]

    # check mode
    for g in games:
        if not g["rated"]:
            return False

        if g["perf"] != mode:
            return False

    # check times
    current_start = time.time() * 1000
    for g in games:

        if current_start - g["lastMoveAt"] > interval:
            return False

        current_start = g["createdAt"]

    # check result
    for g in games:
        is_white = True if g["players"]["white"]["id"] == username.lower() else False

        if is_white and g["winner"] != "black":
            return False

        if not is_white and g["winner"] != "white":
            return False

    return True


config = None

with open("config.json", "r") as f:
    config = json.load(f)

logging.info("starting")
send_to_webhook(config["webhook-url"], "Starting Tilt Monitor")


while True:
    for player in config["observer-list"].keys():
        logging.info(f"Checking {player}")

        # rapid
        if check_last_games(player, "rapid", interval, 3):
            send_to_webhook(config["webhook-url"], f"Tilt Alarm fuer {player}")

        # blitz
        if check_last_games(player, "blitz", interval, 5):
            send_to_webhook(config["webhook-url"], f"Tilt Alarm fuer {player}")

    time.sleep(interval)
