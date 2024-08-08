import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageButton", instance=0).click()
    assert d(text="Create new").exists
    d(text="CANCEL").click()
