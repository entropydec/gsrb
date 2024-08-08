import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="me.blog.korn123.easydiary:id/planner").click()
    assert d(text="Calendar").exists
