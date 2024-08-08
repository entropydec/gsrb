import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="com.simplemobiletools.filemanager.pro:id/search").click()
    d(resourceId="com.simplemobiletools.filemanager.pro:id/search_src_text").set_text(
        "Alarms"
    )
    assert d(text="Internal/Alarms").exists
