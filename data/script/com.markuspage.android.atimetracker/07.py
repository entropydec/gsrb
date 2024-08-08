import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(description="More options").click()
    d(text="Add task").click()
    d(resourceId="com.markuspage.android.atimetracker:id/task_edit_name_edit").set_text(
        "test"
    )
    d(text="Add task", instance=1).click()
    d(className="android.widget.TextView", text="test").long_click()
    d(text="Edit Task").click()
    d(resourceId="com.markuspage.android.atimetracker:id/task_edit_name_edit").set_text(
        "test_changed"
    )
    d(text="OK").click()
    assert d(text="test_changed").exists
