import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="Show roots").click()
    d(text="Phone").click()
    assert d(text="apex").exists
