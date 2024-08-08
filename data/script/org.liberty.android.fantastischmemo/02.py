import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageView", instance=3).click()
    assert d(text="AnyMemo.org").exists
