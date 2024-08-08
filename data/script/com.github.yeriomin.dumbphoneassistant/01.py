import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(text="Sim Card").click()
    assert d(text="Copy to phone or delete all contacts").exists
