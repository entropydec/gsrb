import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(text="Sim Card").click()
    d(text="Phone").click()
    assert d(text="Copy all contacts to SIM card").exists
