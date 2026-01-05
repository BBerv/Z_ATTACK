import arcade
import arcade.gui

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Z ATTACK"


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        anchor = arcade.gui.UIAnchorLayout()
        v_box = arcade.gui.UIBoxLayout()

        title = arcade.gui.UILabel(text="Z ATTACK", font_size=60, text_color=arcade.color.WHITE)
        v_box.add(title.with_padding(bottom=50))

        play_btn = arcade.gui.UIFlatButton(text="Играть", width=250)
        v_box.add(play_btn.with_padding(bottom=20))
        play_btn.on_click = self._go_to_mode

        quit_btn = arcade.gui.UIFlatButton(text="Выход", width=250)
        v_box.add(quit_btn)
        quit_btn.on_click = self._quit

        anchor.add(v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def _go_to_mode(self, event):
        self.window.show_view(SelectModeView())

    def _quit(self, event):
        self.window.close()
        arcade.exit()

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        self.clear()
        self.manager.draw()


class SelectModeView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        anchor = arcade.gui.UIAnchorLayout()
        v_box = arcade.gui.UIBoxLayout(space_between=15)

        back = arcade.gui.UIFlatButton(text="← Назад", width=100)
        back.on_click = self._go_back
        v_box.add(back)

        v_box.add(arcade.gui.UILabel(text="Выберите режим", font_size=36, text_color=arcade.color.WHITE))

        survival = arcade.gui.UIFlatButton(text="Выживание", width=220)
        survival.on_click = lambda e: self._select_mode("survival")
        v_box.add(survival)

        defense = arcade.gui.UIFlatButton(text="Защита базы", width=220)
        defense.on_click = lambda e: self._select_mode("base_defense")
        v_box.add(defense)

        anchor.add(v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def _go_back(self, event):
        self.window.show_view(MenuView())

    def _select_mode(self, mode):
        self.window.show_view(SelectMapView(mode))

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        self.clear()
        arcade.draw_text("РЕЖИМ ИГРЫ", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60,
                         arcade.color.WHITE, 24, anchor_x="center")
        self.manager.draw()


class SelectMapView(arcade.View):
    def __init__(self, mode: str):
        super().__init__()
        self.mode = mode
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        anchor = arcade.gui.UIAnchorLayout()
        v_box = arcade.gui.UIBoxLayout(space_between=15)

        back = arcade.gui.UIFlatButton(text="← Назад", width=100)
        back.on_click = self._go_back
        v_box.add(back)

        v_box.add(arcade.gui.UILabel(text="Выберите карту", font_size=36, text_color=arcade.color.WHITE))

        forest = arcade.gui.UIFlatButton(text="Лес", width=200)
        forest.on_click = self._start_forest
        v_box.add(forest)

        anchor.add(v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def _go_back(self, event):
        self.window.show_view(SelectModeView())

    def _start_forest(self, event):
        from game import GameView
        game = GameView(mode=self.mode, map_type="forest")
        game.setup()
        self.window.show_view(game)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        self.clear()
        arcade.draw_text(f"Режим: {self.mode.upper()}", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50,
                         arcade.color.LIGHT_GREEN, 20, anchor_x="center")
        self.manager.draw()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=False)
    menu = MenuView()
    window.show_view(menu)
    arcade.run()


if __name__ == "__main__":
    main()
