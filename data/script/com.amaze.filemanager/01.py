import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageButton", instance=8).click()
    d(text="SMB Connection").click()
    assert d(text="Server IP Address").exists
    d(text="CANCEL").click()
