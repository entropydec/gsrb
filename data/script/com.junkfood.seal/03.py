import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="Settings").click()
    d.swipe(540, 1600, 540, 400)
    d(text="Custom command").click()
    d(text="New template").click()
    d(className="android.widget.EditText", instance=0).set_text("labellabel")
    d(className="android.widget.EditText", instance=1).set_text("test")
    d(text="Confirm").click()
    assert d(text="test").exists
