import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="Open navigation menu").click()
    d(description="Settings").click()
    d(description="Accessibility").click()
    d(description="Remove animations\nSystem").click()
    assert d(description="Prevent screen effects").exists
