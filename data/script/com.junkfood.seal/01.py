import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="Settings").click()
    d(text="Format").click()
    d.swipe(540, 1600, 540, 400)
    d(text="Embed subtitles").click()
