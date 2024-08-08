import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(text="Settings").click()
    d(text="Backup database").click()
