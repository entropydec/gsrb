import uiautomator2 as u2

if __name__ == "__main__":
    d = u2.connect()

    d(resourceId="dev.corruptedark.diditakemymeds:id/add_med").click()
    d(resourceId="dev.corruptedark.diditakemymeds:id/cancel").click()
