import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="More options").click()
    d(text="Chart").click()
    assert d(resourceId="me.blog.korn123.easydiary:id/barChart").exists
