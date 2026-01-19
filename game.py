import arcade
import arcade.gui
import math
import random

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_SPEED = 5
ZOMBIE_SPEED = 2
SPAWN_RATE = 1.5


class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        button_style = {
            "normal": {
                "font_name": ("Kenney Future", "Arial"),
                "font_size": 20,
                "font_color": arcade.color.WHITE,
                "bg": (50, 50, 50),
                "border": arcade.color.WHITE,
                "border_width": 1,
            },
            "hover": {
                "font_color": arcade.color.WHITE,
                "bg": (100, 100, 100),
            },
            "press": {
                "font_color": arcade.color.BLACK,
                "bg": arcade.color.WHITE,
            }
        }

        v_box = arcade.gui.UIBoxLayout(space_between=20)

        label = arcade.gui.UILabel(
            text="ПАУЗА",
            font_name=("Kenney Future", "Arial"),
            font_size=36,
            text_color=arcade.color.WHITE
        )
        v_box.add(label.with_padding(bottom=20))

        resume_btn = arcade.gui.UIFlatButton(text="ПРОДОЛЖИТЬ", width=250, height=50, style=button_style)
        resume_btn.on_click = self._on_resume
        v_box.add(resume_btn)

        menu_btn = arcade.gui.UIFlatButton(text="В МЕНЮ", width=250, height=50, style=button_style)
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
            print(f"Ошибка перехода в меню: {e}")
            self.window.close()

    def on_draw(self):
        self.game_view.on_draw()
        arcade.draw_rect_filled(self.window.rect, (0, 0, 0, 150))
        self.manager.draw()

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.ESCAPE:
            self._on_resume(None)


class GameView(arcade.View):
    def __init__(self, mode="base_defense", map_type="forest"):
        super().__init__()

        self.player_list = None
        self.wall_list = None
        self.enemy_list = None
        self.player_sprite = None
        self.base_sprite = None

        self.time_since_last_spawn = 0.0

        self.left = False
        self.right = False
        self.up = False
        self.down = False

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()

        try:
            self.base_sprite = arcade.Sprite("assets/base.png", scale=0.6)
        except:
            print("Ошибка: assets/base.png не найден. Использую заглушку.")
            self.base_sprite = arcade.SpriteSolidColor(64, 64, arcade.color.RED)

        self.base_sprite.center_x = SCREEN_WIDTH // 2
        self.base_sprite.center_y = SCREEN_HEIGHT // 2
        self.wall_list.append(self.base_sprite)

        try:
            self.player_sprite = arcade.Sprite("assets/MainCharacter.png", scale=1.5)
        except:
            print("Ошибка: assets/MainCharacter.png не найден. Использую заглушку.")
            self.player_sprite = arcade.SpriteSolidColor(40, 60, arcade.color.BLUE)

        self.player_sprite.center_x = SCREEN_WIDTH // 2 - 100
        self.player_sprite.center_y = SCREEN_HEIGHT // 2
        self.player_list.append(self.player_sprite)

    def spawn_enemy(self):
        try:
            zombie = arcade.Sprite("assets/zombie.png", scale=1.0)
        except:
            zombie = arcade.SpriteSolidColor(30, 30, arcade.color.DARK_GREEN)

        side = random.randint(0, 3)
        spawn_offset = 50

        if side == 0:
            zombie.center_x = random.randint(0, SCREEN_WIDTH)
            zombie.center_y = SCREEN_HEIGHT + spawn_offset
        elif side == 1:
            zombie.center_x = SCREEN_WIDTH + spawn_offset
            zombie.center_y = random.randint(0, SCREEN_HEIGHT)
        elif side == 2:
            zombie.center_x = random.randint(0, SCREEN_WIDTH)
            zombie.center_y = -spawn_offset
        elif side == 3:
            zombie.center_x = -spawn_offset
            zombie.center_y = random.randint(0, SCREEN_HEIGHT)

        self.enemy_list.append(zombie)

    def update_enemies_ai(self):
        for zombie in self.enemy_list:
            dist_to_player = math.sqrt(
                (self.player_sprite.center_x - zombie.center_x) ** 2 +
                (self.player_sprite.center_y - zombie.center_y) ** 2
            )

            dist_to_base = math.sqrt(
                (self.base_sprite.center_x - zombie.center_x) ** 2 +
                (self.base_sprite.center_y - zombie.center_y) ** 2
            )

            if dist_to_player < dist_to_base:
                target_x = self.player_sprite.center_x
                target_y = self.player_sprite.center_y
            else:
                target_x = self.base_sprite.center_x
                target_y = self.base_sprite.center_y

            angle_rad = math.atan2(target_y - zombie.center_y, target_x - zombie.center_x)

            zombie.angle = math.degrees(angle_rad)

            zombie.change_x = math.cos(angle_rad) * ZOMBIE_SPEED
            zombie.change_y = math.sin(angle_rad) * ZOMBIE_SPEED

    def reset_movement(self):
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        if self.player_sprite:
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_OLIVE_GREEN)

    def on_draw(self):
        self.clear()

        self.wall_list.draw()
        self.enemy_list.draw()
        self.player_list.draw()

        arcade.draw_text(
            "ESC — Пауза",
            SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30,
            arcade.color.WHITE, 14
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

        self.player_list.update()

        self.time_since_last_spawn += delta_time
        if self.time_since_last_spawn > SPAWN_RATE:
            self.spawn_enemy()
            self.time_since_last_spawn = 0

        self.update_enemies_ai()
        self.enemy_list.update()

        if self.player_sprite.left < 0:
            self.player_sprite.left = 0
        if self.player_sprite.right > SCREEN_WIDTH:
            self.player_sprite.right = SCREEN_WIDTH
        if self.player_sprite.bottom < 0:
            self.player_sprite.bottom = 0
        if self.player_sprite.top > SCREEN_HEIGHT:
            self.player_sprite.top = SCREEN_HEIGHT

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.W or key == arcade.key.UP:
            self.up = True
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.down = True
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.left = True
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.right = True
        elif key == arcade.key.ESCAPE:
            pause_view = PauseView(self)
            self.window.show_view(pause_view)

    def on_key_release(self, key, _modifiers):
        if key == arcade.key.W or key == arcade.key.UP:
            self.up = False
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.down = False
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.left = False
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.right = False