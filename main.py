import arcade
import arcade.gui

# --- Константы окна ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Z ATTACK"
FULLSCREEN = True

# --- Пути к ресурсам ---
BACKGROUND_PATH = "assets/menu_background.jpg"
FONT_RESOURCE = ":resources:fonts/kenney_blocks.ttf"

# --- Настройки UI ---
BUTTON_WIDTH = 350
BUTTON_HEIGHT = 50
BUTTON_SPACING = 20
MENU_OFFSET_Y = -80

# --- Настройки текста заголовка ---
TITLE_TEXT = "Z ATTACK"
TITLE_FONT_SIZE = 80
TITLE_MAIN_COLOR = arcade.color.RED_DEVIL
TITLE_SHADOW_COLOR = arcade.color.BLACK
TITLE_OFFSET_Y = 150
TITLE_SHADOW_OFFSET = 4

# --- Стилизация кнопок ---
BUTTON_STYLE = {
    "normal": {
        "font_name": ("Kenney Future", "Arial"),
        "font_size": 20,
        "font_color": arcade.color.WHITE,
        "bg": (21, 19, 21),
        "border": None,
        "border_width": 0,
    },
    "hover": {
        "font_name": ("Kenney Future", "Arial"),
        "font_size": 20,
        "font_color": arcade.color.WHITE,
        "bg": (60, 60, 60),
        "border": arcade.color.WHITE,
        "border_width": 2,
    },
    "press": {
        "font_name": ("Kenney Future", "Arial"),
        "font_size": 20,
        "font_color": arcade.color.BLACK,
        "bg": arcade.color.WHITE,
        "border": arcade.color.WHITE,
        "border_width": 2,
    }
}


class MenuView(arcade.View):
    """
    Класс главного меню. Отвечает за отображение интерфейса,
    фон и обработку нажатий кнопок.
    """

    def __init__(self):
        super().__init__()
        self.ui_manager = arcade.gui.UIManager()
        self.background_texture = None
        self.title_font_name = "Arial"

        self._load_assets()
        self._setup_ui()

    def _load_assets(self):
        """Загрузка изображений и шрифтов с безопасной обработкой ошибок."""
        try:
            self.background_texture = arcade.load_texture(BACKGROUND_PATH)
        except FileNotFoundError:
            print(f"Предупреждение: Фон меню не найден по пути {BACKGROUND_PATH}")
            self.background_texture = None

        try:
            arcade.load_font(FONT_RESOURCE)
            self.title_font_name = "Kenney Blocks"
        except Exception as e:
            print(f"Предупреждение: Не удалось загрузить шрифт. Используется стандартный. {e}")

    def _setup_ui(self):
        """Создание кнопок и размещение их на экране."""
        anchor_layout = arcade.gui.UIAnchorLayout()
        buttons_layout = arcade.gui.UIBoxLayout(space_between=BUTTON_SPACING)

        # Кнопка начала игры
        play_button = arcade.gui.UIFlatButton(
            text="ИГРАТЬ",
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            style=BUTTON_STYLE
        )
        play_button.on_click = self._start_game_handler
        buttons_layout.add(play_button)

        # Кнопка выхода
        quit_button = arcade.gui.UIFlatButton(
            text="ВЫХОД",
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            style=BUTTON_STYLE
        )
        quit_button.on_click = self._quit_handler
        buttons_layout.add(quit_button)

        # Добавляем вертикальный блок кнопок в центр с учетом смещения
        anchor_layout.add(
            buttons_layout,
            anchor_x="center_x",
            anchor_y="center_y",
            align_y=MENU_OFFSET_Y
        )
        self.ui_manager.add(anchor_layout)

    def on_show_view(self):
        """Активирует менеджер UI при переходе на этот экран."""
        self.ui_manager.enable()

    def on_hide_view(self):
        """Деактивирует менеджер UI при уходе с этого экрана."""
        self.ui_manager.disable()

    def _start_game_handler(self, event):
        """
        Обработчик кнопки 'Играть'.
        Пытается импортировать и запустить игровой вид.
        """
        try:
            from game import GameView
            game_view = GameView()
            game_view.setup()
            self.window.show_view(game_view)
        except ImportError:
            print("Ошибка: Файл game.py не найден. Убедитесь, что модуль игры существует.")
        except Exception as e:
            print(f"Критическая ошибка при запуске игры: {e}")

    def _quit_handler(self, event):
        """Обработчик кнопки 'Выход'. Завершает приложение."""
        self.window.close()
        arcade.exit()

    def on_draw(self):
        """Отрисовка фона, заголовка и интерфейса."""
        self.clear()
        screen_width = self.window.width
        screen_height = self.window.height

        # Отрисовка фона
        if self.background_texture:
            arcade.draw_texture_rect(self.background_texture, self.window.rect)
        else:
            arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # Координаты заголовка
        title_x = screen_width / 2
        title_y = screen_height - TITLE_OFFSET_Y

        # Отрисовка тени заголовка
        arcade.draw_text(
            TITLE_TEXT,
            title_x + TITLE_SHADOW_OFFSET,
            title_y - TITLE_SHADOW_OFFSET,
            TITLE_SHADOW_COLOR,
            TITLE_FONT_SIZE,
            anchor_x="center",
            font_name=self.title_font_name
        )

        # Отрисовка основного текста заголовка
        arcade.draw_text(
            TITLE_TEXT,
            title_x,
            title_y,
            TITLE_MAIN_COLOR,
            TITLE_FONT_SIZE,
            anchor_x="center",
            font_name=self.title_font_name
        )

        self.ui_manager.draw()


def main():
    """Точка входа в приложение. Настройка окна и запуск меню."""
    window = arcade.Window(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        SCREEN_TITLE,
        fullscreen=FULLSCREEN,
        antialiasing=False
    )

    # Настройка фильтрации для пиксель-арта (четкие грани)
    window.ctx.default_atlas.texture_filter = window.ctx.NEAREST

    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
