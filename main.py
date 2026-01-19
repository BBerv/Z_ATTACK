import arcade
import arcade.gui
import os

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Z ATTACK"

BACKGROUND_PATH = "assets/menu_background.jpg"

DEFAULT_STYLE = {
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
    },
    "disabled": {
        "font_name": ("Kenney Future", "Arial"),
        "font_size": 20,
        "font_color": arcade.color.GRAY,
        "bg": (10, 10, 10),
        "border": None,
        "border_width": 0,
    }
}


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        try:
            self.background = arcade.load_texture(BACKGROUND_PATH)
        except FileNotFoundError:
            print(f"Файл фона не найден: {BACKGROUND_PATH}")
            self.background = None

        try:
            arcade.load_font(":resources:fonts/kenney_blocks.ttf")
            self.title_font = "Kenney Blocks"
        except:
            self.title_font = "Arial"

        anchor = arcade.gui.UIAnchorLayout()
        v_box = arcade.gui.UIBoxLayout(space_between=20)

        play_btn = arcade.gui.UIFlatButton(text="ИГРАТЬ", width=350, height=50, style=DEFAULT_STYLE)
        play_btn.on_click = self._start_game_directly
        v_box.add(play_btn)

        quit_btn = arcade.gui.UIFlatButton(text="ВЫХОД", width=350, height=50, style=DEFAULT_STYLE)
        quit_btn.on_click = self._quit
        v_box.add(quit_btn)

        anchor.add(v_box, anchor_x="center_x", anchor_y="center_y", align_y=-80)
        self.manager.add(anchor)

    def _start_game_directly(self, event):
        try:
            from game import GameView
            game = GameView(mode="base_defense", map_type="forest")
            game.setup()
            self.window.show_view(game)
        except ImportError:
            print("Файл game.py не найден, запускаем тестовую заглушку.")
            game = DummyGameView("base_defense", "forest")
            self.window.show_view(game)
        except Exception as e:
            print(f"Ошибка при запуске игры: {e}")

    def _quit(self, event):
        self.window.close()
        arcade.exit()

    def on_draw(self):
        self.clear()

        if self.background:
            arcade.draw_texture_rect(self.background, self.window.rect)
        else:
            arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        arcade.draw_text("Z ATTACK", SCREEN_WIDTH / 2 + 4, SCREEN_HEIGHT - 154,
                         arcade.color.BLACK, 80, anchor_x="center", font_name=self.title_font)
        arcade.draw_text("Z ATTACK", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 150,
                         arcade.color.RED_DEVIL, 80, anchor_x="center", font_name=self.title_font)

        self.manager.draw()


class DummyGameView(arcade.View):
    def __init__(self, mode, map_type):
        super().__init__()
        self.mode = mode
        self.map_type = map_type

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        arcade.draw_text(f"ИГРА НАЧАЛАСЬ\nРежим: {self.mode}\nКарта: {self.map_type}",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.WHITE, 24, anchor_x="center", anchor_y="center")
        arcade.draw_text("Нажми ESC для выхода в меню",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80,
                         arcade.color.GRAY, 16, anchor_x="center")

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.window.show_view(MenuView())


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=False, resizable=True)
    window.center_window()
    menu = MenuView()
    window.show_view(menu)
    arcade.run()


if __name__ == "__main__":
    main()