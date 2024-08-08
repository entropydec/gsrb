import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="com.pocket_plan.j7_003:id/clAddNote").click()
    d(resourceId="com.pocket_plan.j7_003:id/etNoteTitle").set_text("test")
    d(resourceId="com.pocket_plan.j7_003:id/item_editor_save").click()
    d(
        resourceId="com.pocket_plan.j7_003:id/navigation_bar_item_icon_view", instance=0
    ).click()
    d(text="test").click()
    d(resourceId="com.pocket_plan.j7_003:id/item_editor_move").click()
    assert d(text="Move note").exists
