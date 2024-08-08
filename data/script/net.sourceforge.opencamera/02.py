import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageButton", instance=1).click()
    assert d(text="Photo Mode:").exists
