import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="More options").click()
    d(text="More…").click()
    d(text="Change date range").click()
    assert d(text="Today").exists
