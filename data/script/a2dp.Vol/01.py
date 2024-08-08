import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()
    d(text="Car Dock").click()
    d(text="Delete").click()
    d(text="Find Devices").click()
    d(text="Car Dock").click()
    d(text="Delete").click()
    assert not d(text="Car Dock").exists
