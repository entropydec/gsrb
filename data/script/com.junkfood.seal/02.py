import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="Settings").click()
    d(text="General").click()
    d.swipe(540, 1600, 540, 200)
    d(text="Command template").click()
    d(text="Command template").click()
    assert d(text="Edit").exists
