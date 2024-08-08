import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="More options").click()
    d(text="Settings").click()
    d(text="Change visibility and order of library tabs").click()
    assert d(text="Library tabs").exists
