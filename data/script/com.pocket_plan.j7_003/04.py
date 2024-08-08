import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="open").click()
    d(text="Settings").click()
    d(text="Backup").click()
    d(text="Export full backup as .zip file").click()
