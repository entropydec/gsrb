import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(text="Alarms").long_click()
    d(resourceId="com.veniosg.dir:id/menu_file_ops").click()
    d(text="Copy").click()
    d(resourceId="com.veniosg.dir:id/menu_clear_clipboard").click()
