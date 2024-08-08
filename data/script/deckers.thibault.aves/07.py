import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="Open navigation menu").click()
    d(description="Settings").click()
    d(description="Viewer").click()
    d(description="Overlay").click()
    d(description="Blur effect").click()
