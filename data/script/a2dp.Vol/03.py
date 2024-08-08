import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="android:id/text1").click()
    d(text="Edit").click()
    d(text="Enable Reading Text Messages?").click()
    assert d(text="Music Stream").exists
