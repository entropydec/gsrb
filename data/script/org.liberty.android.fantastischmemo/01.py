import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageView", instance=2).click()
    assert d(text="/storage/emulated/0/anymemo").exists
