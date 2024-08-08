import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageView", instance=3).click()
    d.swipe(540, 1500, 540, 600)
    d(text="Change activity card size").click()
    assert d(text="DEFAULT WIDTH").exists
