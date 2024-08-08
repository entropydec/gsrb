import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="dev.corruptedark.diditakemymeds:id/add_med").click()
    d(resourceId="dev.corruptedark.diditakemymeds:id/med_name").set_text("test")
    d(resourceId="dev.corruptedark.diditakemymeds:id/as_needed_switch").click()
    d(resourceId="dev.corruptedark.diditakemymeds:id/save").click()
    assert d(text="test").exists
