import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.TextView", instance=1).click()
    d.press("back")
