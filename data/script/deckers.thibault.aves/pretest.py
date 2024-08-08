import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.Switch", instance=0).click()
    d(className="android.widget.Switch", instance=1).click()
    d(className="android.widget.Switch", instance=2).click()
    d(description="CONTINUE").click()
