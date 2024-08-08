import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(text="SETTINGS").click()
    assert d(text="Application").exists
