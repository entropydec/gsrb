import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="com.android.keepass:id/browse_button").click()
    assert d(description="Show roots").exists
