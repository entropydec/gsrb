import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageView", instance=2).click()
    d(resourceId="com.simplemobiletools.filemanager.pro:id/change_view_type").click()
    assert d(text="Grid").exists
    d(text="CANCEL").click()
