from cProfile import run
import email
import os
import shutil
import sys
import time
import subprocess
import traceback
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

def run_command(command):
    """Run a command and return the output"""
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = p.communicate()
    output = output.decode("utf-8").replace("\r\n", "\n")
    error = error.decode("utf-8").replace("\r\n", "\n")
    log(output)
    log(error)

    # check if output contains 'error', 'fatal', 'exception' or similar
    for out in [output, error]:
        if any(x in out.lower() for x in ["error", "fatal", "exception"]):
            log("Error in command: {}".format(command))
            raise Exception("Error in command: {}".format(command))
    if p.returncode != 0:
        log("Error in command: {}".format(command))
        raise Exception("Error in command: {}".format(command))

def has_update(path: str, timeout: int = 60) -> bool:
    log("Checking for {} update".format(path))
    counter = 0
    while True:
        # check for game_info.xml, get avilable and installed string from <version name="client" available="0.11.8.0.6223552" installed="0.11.8.0.6223552"/>
        game_info_path = os.path.join(path, "game_info.xml")
        if not os.path.exists(game_info_path):
            log("game_info.xml not found")
            raise Exception("game_info.xml not found")
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

def move(src: str, dest: str) -> None:
    """
    Move from src to dest, if dest exists, delete it first
    """
    log("Moving {} to {}".format(src, dest))
    if os.path.exists(dest):
        log("Deleting {}".format(dest))
        shutil.rmtree(dest)
    folder_path = os.path.dirname(dest)
    if not os.path.exists(folder_path):
        log("Creating {}".format(folder_path))
        os.makedirs(folder_path)
    shutil.move(src, dest)

def generate(path: str) -> None:
    log("Generating data from {}".format(path))
    public_test = False
    with open(os.path.join(path, "game_info.xml"), "r") as f:
        game_info = f.read()
        if '<id>WOWS.PT.PRODUCTION</id>' in game_info:
            public_test = True
        version = game_info.split('available="')[1].split('"')[0]

    python_path = 'C:/Users/nateq/Documents/GitHub/automation/.env/Scripts/python.exe'
    run_command(python_path + ' clean.py')
    run_command(python_path + ' unpack.py ' + path)
    run_command(python_path + ' generate.py')
    run_command(python_path + ' additional.py --all')

    # move to data folder, put it under the same folder as automation
    folder_name = 'data/public_test' if public_test else 'data/live'
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), folder_name)
    move('./app', os.path.join(data_path, 'app'))
    move('./wowsinfo.json', os.path.join(data_path, 'app/data/wowsinfo.json'))
    move('./lang.json', os.path.join(data_path, 'app/lang/lang.json'))

    # commit and push
    suffix = 'PT' if public_test else ''
    run_command('cd {} && git add .'.format(data_path))
    run_command('cd {} && git commit -m "Update {} {}"'.format(data_path, version, suffix))

    # tag the latest commit
    tag = version + suffix
    run_command('cd {} && git tag -a {} -m "Update {} {}"'.format(data_path, tag, version, suffix))

def push_github() -> None:
    """
    Push changes of data repo to github
    """
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    run_command('cd {} && git push origin master --tags'.format(data_path))
    
if __name__ == '__main__':
    # read from game.path
    try:
        with open("game.path", "r") as f:
            public_path = f.readline().strip()
            test_path = f.readline().strip()

        hasError = False
        hasUpdate = False
        try:
            if has_update(public_path):
                wait_for_update(public_path)
                generate(public_path)
                hasUpdate = True
        except Exception as e:
            # duplicate tag maybe
            traceback.print_exc()
            log(e)
            hasError = True
        
        try:
            if has_update(test_path):
                wait_for_update(test_path)
                generate(test_path)
                hasUpdate = True
        except Exception as e:
            traceback.print_exc()
            log(e)
            hasError = True

        if hasUpdate:
            email = Email()
            if not hasError:
                push_github()
                email.send("Game Update success", "All changes are pushed to github")
                sys.exit(0)
            else:
                email.send("Game Update failed", "Please review the log")
                sys.exit(1)
    except Exception as e:
        traceback.print_exc()
        log(e)
        email = Email()
        email.send("Game Update failed", "Unknown error")
        sys.exit(1)
