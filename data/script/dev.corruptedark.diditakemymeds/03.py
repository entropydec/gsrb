import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="dev.corruptedark.diditakemymeds:id/add_med").click()
    d(resourceId="dev.corruptedark.diditakemymeds:id/med_name").set_text("test")
    d(resourceId="dev.corruptedark.diditakemymeds:id/repeat_schedule_button").click()
    d(resourceId="dev.corruptedark.diditakemymeds:id/time_picker_button").click()
    d(description="9 o'clock").click()
    d(description="00 minutes").click()
    d(
        resourceId="dev.corruptedark.diditakemymeds:id/material_timepicker_ok_button"
    ).click()
    d(resourceId="dev.corruptedark.diditakemymeds:id/start_date_button").click()
    d(text="OK").click()
    d(text="CONFIRM").click()
    d(resourceId="dev.corruptedark.diditakemymeds:id/save").click()
    assert d(text="9:00AM").exists
