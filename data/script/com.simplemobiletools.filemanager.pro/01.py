import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="More options").click()
    d(text="Add to favorites").click()
    d(description="More options").click()
    d.press("back")
    assert d(resourceId="com.simplemobiletools.filemanager.pro:id/go_to_favorite").exists
