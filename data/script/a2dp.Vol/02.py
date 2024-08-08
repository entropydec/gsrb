import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(text="Stop Service").click()
    d(text="Car Dock").click()
    d(text="Delete").click()
    d(text="Find Devices").click()
    assert d(text="Start Service").exists
