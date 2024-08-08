import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="com.simplemobiletools.gallery.pro:id/search").click()
    d(resourceId="com.simplemobiletools.gallery.pro:id/search_src_text").set_text("Alarm")
    assert d(text="Alarm").exists
