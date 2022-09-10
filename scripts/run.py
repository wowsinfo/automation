import email
import os
import sys
import time
from mail import Email

def log(message):
    """
    log message to ../logs with today's date as the name, append to existing logs
    """
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    today = time.strftime("%Y-%m-%d")
    log_file = os.path.join(log_path, today + ".log")
    # time string with milliseconds
    time_str = time.strftime("%H:%M:%S") + ".{:03d}".format(int(time.time() * 100000) % 100000)
    with open(log_file, "a") as f:
        f.write("{}==={}\n".format(time_str, message))
    print(message)

def has_update(path: str, timeout: int = 10) -> bool:
    log("Checking for {} update".format(path))
    counter = 0
    while True:
        # check for game_info.xml, get avilable and installed string from <version name="client" available="0.11.8.0.6223552" installed="0.11.8.0.6223552"/>
        game_info_path = os.path.join(path, "game_info.xml")
        if not os.path.exists(game_info_path):
            log("game_info.xml not found")
            sys.exit(1)
        with open(game_info_path, "r") as f:
            game_info = f.read()
        available = game_info.split('available="')[1].split('"')[0]
        installed = game_info.split('installed="')[1].split('"')[0]
        log("available: {}, installed: {}".format(available, installed))
        if available != installed:
            log("Update available for {}".format(path))
            email = Email()
            email.send("Update available", path)
            return True

        time.sleep(5)
        counter += 5
        if counter >= timeout:
            log("No update found after {} seconds".format(timeout))
            return False

def wait_for_update(path: str) -> None:
    log("Waiting for update to finish")
    while True:
        if not has_update(path):
            log("Update finished")
            email = Email()
            email.send("Update finished", path)
            return
        time.sleep(60)

def generate(path: str) -> None:
    log("Generating data from {}".format(path))
    

if __name__ == '__main__':
    # read from game.path
    try:
        with open("game.path", "r") as f:
            public_path = f.readline().strip()
            test_path = f.readline().strip()

        # check for update
        has_update(public_path)
        has_update(test_path)
        sys.exit(0)
    except Exception as e:
        log("Error: {}".format(e))
        sys.exit(1)
