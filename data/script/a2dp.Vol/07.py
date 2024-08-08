import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageButton", instance=0).click()
    d(resourceId="android:id/title", instance=2).click()
    d(resourceId="android:id/button1").click()
    d(text="Find Devices").click()
    assert d(text="Car Dock").exists
