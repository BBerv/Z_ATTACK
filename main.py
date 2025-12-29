import arcade
import arcade.gui
from game import GameView

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Z ATTACK"


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.anchor_layout = arcade.gui.UIAnchorLayout()
        self.v_box = arcade.gui.UIBoxLayout()

        title_text = arcade.gui.UILabel(
            text="Z ATTACK",
            font_size=60,
            text_color=arcade.color.WHITE
        )
        self.v_box.add(title_text.with_padding(bottom=50))

        self.play_button = arcade.gui.UIFlatButton(text="Играть", width=250)
        self.v_box.add(self.play_button.with_padding(bottom=20))
        self.play_button.on_click = self.start_game_pressed

        self.anchor_layout.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(self.anchor_layout)

    def start_game_pressed(self, event):
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        self.clear()
        self.manager.draw()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=False)
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
