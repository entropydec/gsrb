import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="Settings").click()
    d.swipe(540, 1600, 540, 400)
    d(text="About").click()
    d(className="android.widget.TextView", instance=8).click()
    assert d(text="Android Jetpack").exists
