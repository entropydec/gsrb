import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="More options").click()
    d(className="android.widget.TextView", instance=3).click()
    d(text="NO").click()
