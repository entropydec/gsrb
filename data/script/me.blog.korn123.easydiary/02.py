import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="me.blog.korn123.easydiary:id/timeline").click()
    d(resourceId="me.blog.korn123.easydiary:id/search").click()
    d(resourceId="me.blog.korn123.easydiary:id/searchView").set_text("test")
    assert d(text="test").exists
