import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(text="Sim Card").click()
    d(resourceId="com.github.yeriomin.dumbphoneassistant:id/button_delete").click()
    d(resourceId="android:id/button1").click()
