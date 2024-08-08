import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="More options").click()
    d(text="Add task").click()
    d(resourceId="com.markuspage.android.atimetracker:id/task_edit_name_edit").set_text(
        "test"
    )
    d(text="Add task", instance=1).click()
    assert d(className="android.widget.TextView", instance=1).info["text"] == "test"
