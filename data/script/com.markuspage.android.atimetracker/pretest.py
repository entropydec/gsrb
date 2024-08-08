import time

import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()
    time.sleep(0.5)
    if d(text="Continue").exists:
        d(text="Continue").click()
    time.sleep(0.5)
    d(text="OK").click()
    time.sleep(0.5)
    if d(text="OK").exists:
        d(text="OK").click()
