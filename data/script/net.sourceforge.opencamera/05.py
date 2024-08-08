import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(className="android.widget.ImageButton", instance=2).click()
    d(text="On screen GUI…").click()
    d(text="Preview size").click()
    assert d(text="Match photo size (WYSIWYG)").exists
