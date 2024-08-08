import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.view.View", instance=8).click()
    assert d(text="Downloads").exists
