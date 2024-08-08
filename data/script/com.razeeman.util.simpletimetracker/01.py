import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageView", instance=3).click()
    d(
        resourceId="com.razeeman.util.simpletimetracker:id/checkboxSettingsShowUntracked"  # noqa
    ).click()
    assert d(text="Show untracked time in records").exists
