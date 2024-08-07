import logging
import re
import subprocess
import time

from uiautomator2 import Device, ShellResponse

logger = logging.getLogger(__name__)

permission_pattern = r"^\s*?(?P<permission>android\.permission\.[A-Za-z_]+?):\s*?granted=(?P<granted>false|true).*?$"  # noqa

wait_time = 5


def get_version(device: str, package: str) -> str | None:
    """根据 app 包名获取版本号

    Args:
        package (str): 包名

    Returns:
        str | None: 版本号
    """
    result = subprocess.run(
        ["adb", "-s", device, "shell", "dumpsys", "package", package],
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    for line in result.stdout.decode("utf-8").split("\n"):
        if line.strip().startswith("versionName"):
            return line.split("=")[1].strip()
    return None


def get_label(apk: str) -> str | None:
    result = subprocess.run(["aapt", "dump", "badging", apk], capture_output=True)
    if result.returncode != 0:
        return None
    for line in result.stdout.decode("utf-8").split("\n"):
        if line.strip().startswith("application-label:"):
            return line.split(":")[1].strip("\r").strip("'")
    return None


def get_permission_list(device: Device, package: str) -> list[str]:
    """获取当前包的权限列表

    Args:
        device (Device): u2 device
        package (str): 包名

    Returns:
        list[str]: 需求的权限列表
    """
    result: list[str] = []
    info = device.shell(["dumpsys", "package", package])
    assert isinstance(info, ShellResponse)
    output: str = info.output
    for line in output.split("\n"):
        if match := re.match(
            permission_pattern,
            line,
        ):
            permission: str = match.group("permission")
            logger.debug(f"{package}: {permission}")
            result.append(permission)
    return result


def grant_permission(device: Device, package: str) -> None:
    """为应用赋予权限

    Args:
        device (Device): u2 device
        package (str): 包名
    """
    logger.debug(f"grant permissons for {package}")
    for permission in get_permission_list(device, package):
        device.shell(["pm", "grant", package, permission])
        logger.debug(f"execute: pm grant {package} {permission}")


def init_app(device: Device, package: str, pretest: str | None = None) -> None:
    """初始化 app

    分为四步

    * 停止 app am force-stop
    * 清除用户信息 pm clear
    * 重新赋予权限
    * 启动 app

    Args:
        device (Device): u2 device
        package (str): 包名
        pretest (str | None, optional): 测试前的初始化动作. Defaults to None.
    """
    logger.debug(f"stop app {package}")
    device.app_stop(package)
    logger.debug(f"clear app {package}")
    device.app_clear(package)
    grant_permission(device, package)
    logger.debug(f"start app {package}")
    device.app_start(package, use_monkey=True)

    if pretest:
        logger.debug("exec pretest script")
        print(pretest)
        g = globals()
        g["__name__"] = "__main__"
        exec(pretest, g)

    time.sleep(wait_time)
