import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="com.samco.trackandgraph:id/import_button").click()
    d(text="Select File").click()
    d.press("back")
    d(text="CANCEL").click()
