import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(text="NEXT").click()
    d(text="NEXT").click()
    d(text="NEXT").click()
    d(text="NEXT").click()
    d(text="NEXT").click()
    d(text="NEXT").click()
