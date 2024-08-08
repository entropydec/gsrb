import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(text="Items").click()
    d(resourceId="org.ebur.debitum:id/fab").click()
    d(resourceId="org.ebur.debitum:id/button_new_person").click()
    d(className="android.widget.EditText", instance=0).set_text("Tom")
    d(text="SAVE").click()
    d(text="Gave").click()
    d(className="android.widget.EditText", instance=1).set_text("test")
    d(text="SAVE").click()
    assert d(text="test").exists
