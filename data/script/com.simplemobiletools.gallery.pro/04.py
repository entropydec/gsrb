import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="More options").click()
    d(text="Show all folders content").click()
    d(text="Change filters").click()
    assert d(text="Filter media").exists
    d(text="CANCEL").click()
