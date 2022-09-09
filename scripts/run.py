import os
import logging
import time


def shutdown():
    """Shutdown the system after 2 min"""
    os.system("shutdown -s -t 120")


def log(message):
    """
    log message to ../logs with today's date as the name, append to existing logs
    """
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    today = time.strftime("%Y-%m-%d")
    log_file = os.path.join(log_path, today + ".log")
    with open(log_file, "a") as f:
        f.write("INFO: " + message + "\n")
    print(message)


if __name__ == '__main__':
    # the machine boots up at around 10:00, only run this if it is within 10 mins
    if 600 <= int(time.strftime("%H%M")) <= 610:
        shutdown()
        log("Running tasks")
    else:
        log("Tasks will not run at {}".format(time.strftime("%H:%M")))
