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
            game = GameView()
            game.setup()
            self.window.show_view(game)
        except ImportError:
            print("Файл game.py не найден.")
        except Exception as e:
            print(f"Ошибка при запуске игры: {e}")

    def _quit(self, event):
        self.window.close()
        arcade.exit()

    def on_draw(self):
        self.clear()
        w = self.window.width
        h = self.window.height

        if self.background:
            arcade.draw_texture_rect(self.background, self.window.rect)
        else:
            arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        arcade.draw_text("Z ATTACK", w / 2 + 4, h - 154,
                         arcade.color.BLACK, 80, anchor_x="center", font_name=self.title_font)
        arcade.draw_text("Z ATTACK", w / 2, h - 150,
                         arcade.color.RED_DEVIL, 80, anchor_x="center", font_name=self.title_font)

        self.manager.draw()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
    menu = MenuView()
    window.show_view(menu)
    arcade.run()


if __name__ == "__main__":
    main()
