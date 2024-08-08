import time

import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()
    time.sleep(2)
    d.swipe(900, 900, 100, 900)
    time.sleep(0.5)
    d.swipe(900, 900, 100, 900)
    time.sleep(0.5)
    d(resourceId="com.samco.trackandgraph:id/closeButton").click()
