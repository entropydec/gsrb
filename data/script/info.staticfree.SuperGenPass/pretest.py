import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()
    d.implicitly_wait(3)
    try:
        d(text="OK").click()
    except Exception:
        pass
