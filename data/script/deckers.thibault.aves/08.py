import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="Open navigation menu").click()
    d(description="Videos").click()
    assert d(description="No videos").exists
