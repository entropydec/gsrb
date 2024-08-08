import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageView", instance=3).click()
    d.swipe(540, 1200, 540, 600)
    d(
        resourceId="com.razeeman.util.simpletimetracker:id/checkboxSettingsUseMilitaryTime"  # noqa
    ).click()
    assert d(text="1:00 PM").exists
