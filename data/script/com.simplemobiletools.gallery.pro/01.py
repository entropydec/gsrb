import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="com.simplemobiletools.gallery.pro:id/sort").click()
    d(
        resourceId="com.simplemobiletools.gallery.pro:id/sorting_dialog_radio_name"
    ).click()
    d(text="CANCEL").click()
