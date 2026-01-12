import arcade


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5


class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        v_box = arcade.gui.UIBoxLayout(space_between=20)
        v_box.add(arcade.gui.UILabel(
            text="ПАУЗА",
            font_size=36,
            text_color=arcade.color.WHITE,
            bold=True
        ))

        resume_btn = arcade.gui.UIFlatButton(text="▶ Продолжить", width=200)
        resume_btn.on_click = self._on_resume
        v_box.add(resume_btn)

        menu_btn = arcade.gui.UIFlatButton(text="⌂ В меню", width=200)
        menu_btn.on_click = self._on_menu
        v_box.add(menu_btn)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def _on_resume(self, event):
        self.manager.disable()
        self.game_view.reset_movement()
        self.window.show_view(self.game_view)

    def _on_menu(self, event):
        self.manager.disable()
        try:
            from main import MenuView
            menu = MenuView()
            self.window.show_view(menu)
        except Exception as e:
            self.window.close()
            arcade.exit()

    def on_draw(self):
        arcade.draw_lrbt_rectangle_filled(
            left=0,
            right=SCREEN_WIDTH,
            bottom=0,
            top=SCREEN_HEIGHT,
            color=(0, 0, 0, 180)
        )
        self.manager.draw()

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.ESCAPE:
            self._on_resume(None)


class GameView(arcade.View):
    def __init__(self, mode: str = "survival", map_type: str = "forest"):
        super().__init__()
        self.mode = mode
        self.map_type = map_type
        self.player_list = arcade.SpriteList()
        self.left = self.right = self.up = self.down = False
        self.player_sprite = None

    def reset_movement(self):
        self.left = self.right = self.up = self.down = False
        if self.player_sprite:
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0

    def setup(self):
        try:
            self.player_sprite = arcade.Sprite("assets/MainCharacter.png", scale=1.0)
            if not self.player_sprite.texture or self.player_sprite.width == 0:
                raise ValueError("Спрайт пуст")
        except Exception as e:
            self.player_sprite = arcade.SpriteSolidColor(40, 60, arcade.color.BLUE)

        self.player_sprite.center_x = SCREEN_WIDTH // 2
        self.player_sprite.center_y = SCREEN_HEIGHT // 2
        self.player_list.append(self.player_sprite)

    def on_show_view(self):
        self.reset_movement()
        bg_color = arcade.color.DARK_OLIVE_GREEN if self.map_type == "forest" else arcade.color.GRAY
        arcade.set_background_color(bg_color)

    def on_draw(self):
        self.clear()
        self.player_list.draw()

        # HUD
        arcade.draw_text(
            f"Режим: {self.mode.upper()}",
            10, SCREEN_HEIGHT - 25,
            arcade.color.WHITE, 14
        )
        arcade.draw_text(
            "ESC — пауза",
            SCREEN_WIDTH - 120, 10,
            arcade.color.WHITE, 12
        )

    def on_update(self, delta_time):
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        if self.up:
            self.player_sprite.change_y = PLAYER_SPEED
        if self.down:
            self.player_sprite.change_y = -PLAYER_SPEED
        if self.left:
            self.player_sprite.change_x = -PLAYER_SPEED
        if self.right:
            self.player_sprite.change_x = PLAYER_SPEED

        self.player_sprite.center_x = max(30, min(SCREEN_WIDTH - 30, self.player_sprite.center_x))
        self.player_sprite.center_y = max(30, min(SCREEN_HEIGHT - 30, self.player_sprite.center_y))

        self.player_list.update()

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.W:
            self.up = True
        elif key == arcade.key.S:
            self.down = True
        elif key == arcade.key.A:
            self.left = True
        elif key == arcade.key.D:
            self.right = True
        elif key == arcade.key.ESCAPE:
            pause_view = PauseView(self)
            self.window.show_view(pause_view)

    def on_key_release(self, key, _modifiers):
        if key == arcade.key.W:
            self.up = False
        elif key == arcade.key.S:
            self.down = False
        elif key == arcade.key.A:
            self.left = False
        elif key == arcade.key.D:
            self.right = False