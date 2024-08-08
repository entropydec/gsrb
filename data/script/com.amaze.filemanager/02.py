import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="com.amaze.filemanager:id/properties", instance=0).click()
    d(resourceId="android:id/title", instance=4).click()
    assert d(text="Location").exists
