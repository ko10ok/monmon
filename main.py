import sys
import win32api
import win32con
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu


def create_blank_icon():
    """Создает простую иконку (квадрат) для трея средствами Qt."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("black"))
    painter = QPainter(pixmap)
    painter.setBrush(QColor("white"))
    painter.drawRect(16, 16, 32, 32)
    painter.end()
    return QIcon(pixmap)


def rotate_monitor(device_name, orientation):
    """Меняет ориентацию экрана через Windows API."""
    try:
        dm = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)

        current_is_landscape = dm.DisplayOrientation in (
            win32con.DMDO_DEFAULT,
            win32con.DMDO_180,
        )
        target_is_landscape = orientation in (
            win32con.DMDO_DEFAULT,
            win32con.DMDO_180,
        )

        if current_is_landscape != target_is_landscape:
            dm.PelsWidth, dm.PelsHeight = dm.PelsHeight, dm.PelsWidth

        dm.DisplayOrientation = orientation
        win32api.ChangeDisplaySettingsEx(device_name, dm, win32con.CDS_UPDATEREGISTRY)
    except Exception as e:
        print(f"Ошибка при повороте экрана {device_name}: {e}")


def get_orientation_code(angle):
    """Сопоставляет угол с константами Windows."""
    mapping = {
        0: win32con.DMDO_DEFAULT,
        90: win32con.DMDO_90,
        180: win32con.DMDO_180,
        270: win32con.DMDO_270,
    }
    return mapping.get(angle, win32con.DMDO_DEFAULT)


def main():
    # Инициализируем приложение Qt
    app = QApplication(sys.argv)

    # Чтобы приложение не закрывалось, если закрыты все окна
    app.setQuitOnLastWindowClosed(False)

    # Создаем иконку в трее
    tray_icon = QSystemTrayIcon(create_blank_icon(), parent=app)
    tray_icon.setToolTip("Поворот экранов")

    # Создаем главное контекстное меню
    main_menu = QMenu()

    # Список углов, который ломался в прошлый раз
    angles_list = [0, 90, 180, 270]

    # Опрашиваем мониторы встроенными средствами win32api
    try:
        monitors = win32api.EnumDisplayMonitors()
        for i, monitor in enumerate(monitors):
            monitor_info = win32api.GetMonitorInfo(monitor)
            device_name = monitor_info["Device"]
            short_name = device_name.split('\\')[-1]

            # Создаем вложенное подменю для текущего монитора
            monitor_menu = main_menu.addMenu(f"Монитор {i + 1} ({short_name})")

            # Добавляем углы поворота в подменю
            for angle in angles_list:
                action = QAction(f"{angle}°", monitor_menu)

                # Привязываем клик к функции поворота
                action.triggered.connect(
                    lambda checked=False, d=device_name, a=angle: rotate_monitor(
                        d, get_orientation_code(a)
                    )
                )
                monitor_menu.addAction(action)

    except Exception as e:
        # Запасной вариант, если система заблокировала EnumDisplayMonitors в рантайме
        for i, dev_name in enumerate(["\\\\.\\DISPLAY1", "\\\\.\\DISPLAY2"]):
            monitor_menu = main_menu.addMenu(f"Монитор {i + 1} (DISPLAY{i + 1})")
            for angle in angles_list:
                action = QAction(f"{angle}°", monitor_menu)
                action.triggered.connect(
                    lambda checked=False, d=dev_name, a=angle: rotate_monitor(
                        d, get_orientation_code(a)
                    )
                )
                monitor_menu.addAction(action)

    # Добавляем разделитель и кнопку Выход
    main_menu.addSeparator()
    exit_action = QAction("Выход", main_menu)
    exit_action.triggered.connect(app.quit)
    main_menu.addAction(exit_action)

    # Привязываем меню к иконке в трее
    tray_icon.setContextMenu(main_menu)
    tray_icon.show()

    # Запускаем бесконечный цикл обработки событий Qt
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
