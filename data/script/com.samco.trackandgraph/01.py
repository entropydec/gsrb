import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="More options").click()
    d(text="Tracker").click()
    d(resourceId="com.samco.trackandgraph:id/featureNameText").set_text("test")
    d.press("back")
    d(text="Set a default value").click()
