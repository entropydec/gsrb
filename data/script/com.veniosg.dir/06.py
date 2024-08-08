import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="com.veniosg.dir:id/menu_search").click()
    d(resourceId="android:id/search_src_text").set_text("Alarms")
    assert d(text="Alarms").exists
