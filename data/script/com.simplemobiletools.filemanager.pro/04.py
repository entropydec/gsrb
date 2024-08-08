import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="com.simplemobiletools.filemanager.pro:id/sort").click()
    assert d(text="Sort by").exists
    d(text="CANCEL").click()
