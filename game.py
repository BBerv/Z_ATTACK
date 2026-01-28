import arcade
import arcade.gui
import math
import random
import time
import traceback

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

PLAYER_SPEED = 5
ZOMBIE_SPEED = 2
SPAWN_RATE = 1.5

PLAYER_MAX_HP = 100
ZOMBIE_DAMAGE = 20
HIT_DELAY = 1.0

BULLET_SPEED = 12
ZOMBIE_MAX_HP = 2

SHOOT_DELAY = 0.15


class Particle(arcade.Sprite):
    def __init__(self, texture_list, scale=1.0):
        super().__init__(scale=scale)
        self.textures = texture_list
        self.texture = random.choice(texture_list)
        self.change_x = 0
        self.change_y = 0
        self.change_angle = 0
        self.lifetime = 0.5
        self.fade_rate = 10

    def update(self, delta_time: float = 1 / 60):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.angle += self.change_angle
        self.alpha -= self.fade_rate
        if self.alpha <= 0:
            self.remove_from_sprite_lists()


class Zombie(arcade.Sprite):
    def __init__(self, filename, scale=1.0):
        super().__init__(filename, scale=scale)
        self.hp = ZOMBIE_MAX_HP


class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        button_style = {
            "normal": {"font_name": ("Arial"), "font_size": 20, "font_color": arcade.color.WHITE, "bg": (50, 50, 50),
                       "border": arcade.color.WHITE, "border_width": 1},
            "hover": {"font_color": arcade.color.WHITE, "bg": (100, 100, 100)},
            "press": {"font_color": arcade.color.BLACK, "bg": arcade.color.WHITE}
        }

        v_box = arcade.gui.UIBoxLayout(space_between=20)
        label = arcade.gui.UILabel(text="ПАУЗА", font_size=36, text_color=arcade.color.WHITE)
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
            self.window.show_view(MenuView())
        except Exception as e:
            print(f"Ошибка перехода в меню: {e}")

    def on_draw(self):
        try:
            self.game_view.on_draw()
            arcade.draw_lbwh_rectangle_filled(0, 0, self.window.width, self.window.height, (0, 0, 0, 150))
            self.manager.draw()
        except Exception as e:
            print(f"Ошибка отрисовки паузы: {e}")

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.ESCAPE: self._on_resume(None)


class GameOverView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.time_elapsed = 0.0
        self.ui_enabled = False

        button_style = {
            "normal": {"font_name": ("Arial"), "font_size": 20, "font_color": arcade.color.WHITE, "bg": (139, 0, 0),
                       "border": arcade.color.WHITE, "border_width": 1},
            "hover": {"font_color": arcade.color.WHITE, "bg": (255, 69, 0)},
            "press": {"font_color": arcade.color.BLACK, "bg": arcade.color.WHITE}
        }

        v_box = arcade.gui.UIBoxLayout(space_between=20)
        label = arcade.gui.UILabel(text="ВЫ ПОГИБЛИ", font_size=48, text_color=arcade.color.RED)
        v_box.add(label.with_padding(bottom=30))

        restart_btn = arcade.gui.UIFlatButton(text="ЗАНОВО", width=250, height=50, style=button_style)
        restart_btn.on_click = self._on_restart
        v_box.add(restart_btn)

        menu_btn = arcade.gui.UIFlatButton(text="В МЕНЮ", width=250, height=50, style=button_style)
        menu_btn.on_click = self._on_menu
        v_box.add(menu_btn)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def on_update(self, delta_time):
        self.time_elapsed += delta_time
        if not self.ui_enabled and self.time_elapsed > 1.0:
            self.manager.enable()
            self.ui_enabled = True

    def _on_restart(self, event):
        self.manager.disable()
        game = GameView()
        game.setup()
        self.window.show_view(game)

    def _on_menu(self, event):
        self.manager.disable()
        try:
            from main import MenuView
            self.window.show_view(MenuView())
        except Exception as e:
            print(f"Ошибка: {e}")

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.BLACK)
        self.manager.draw()
        if not self.ui_enabled:
            arcade.draw_text("...", self.window.width / 2, 100, arcade.color.WHITE, anchor_x="center")


class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        try:
            self.bullet_texture = arcade.load_texture("assets/pistol_bullet.png")
        except:
            self.bullet_texture = arcade.make_soft_square_texture(10, arcade.color.YELLOW, outer_alpha=255)

        self.player_list = None
        self.wall_list = None
        self.enemy_list = None
        self.bullet_list = None
        self.particle_list = None
        self.gun_list = None

        self.player_sprite = None
        self.pistol_sprite = None
        self.base_sprite = None

        self.physics_engine = None
        self.time_since_last_spawn = 0.0
        self.can_shoot_timer = 0.0

        self.hp = PLAYER_MAX_HP
        self.last_hit_time = 0

        self.left = False
        self.right = False
        self.up = False
        self.down = False

        self.mouse_x = 0
        self.mouse_y = 0

        self.blood_textures = []
        for i in range(4):
            tex = arcade.make_circle_texture(diameter=random.randint(4, 10), color=arcade.color.RED_DEVIL)
            self.blood_textures.append(tex)

        self.smoke_textures = []
        for i in range(3):
            tex = arcade.make_circle_texture(diameter=random.randint(5, 12), color=arcade.color.GRAY)
            self.smoke_textures.append(tex)

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.particle_list = arcade.SpriteList()
        self.gun_list = arcade.SpriteList()

        self.hp = PLAYER_MAX_HP
        self.last_hit_time = 0
        self.can_shoot_timer = 0.0

        cx = self.window.width // 2
        cy = self.window.height // 2

        try:
            self.base_sprite = arcade.Sprite("assets/base.png", scale=0.6)
        except:
            self.base_sprite = arcade.SpriteSolidColor(64, 64, arcade.color.RED)
        self.base_sprite.center_x = cx
        self.base_sprite.center_y = cy
        self.wall_list.append(self.base_sprite)

        try:
            self.player_sprite = arcade.Sprite("assets/MainCharacter.png", scale=1.5)
        except:
            self.player_sprite = arcade.SpriteSolidColor(40, 60, arcade.color.BLUE)
        self.player_sprite.center_x = cx - 100
        self.player_sprite.center_y = cy
        self.player_list.append(self.player_sprite)

        try:
            self.pistol_sprite = arcade.Sprite("assets/pistol.png", scale=0.8)
        except:
            self.pistol_sprite = arcade.SpriteSolidColor(20, 10, arcade.color.BLACK)

        self.gun_list.append(self.pistol_sprite)

        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_OLIVE_GREEN)

    def spawn_enemy(self):
        try:
            zombie = Zombie("assets/zombie.png", scale=2.0)
        except:
            zombie = Zombie(":resources:images/animated_characters/zombie/zombie_idle.png", scale=1.0)
            if not getattr(zombie, 'texture', None):
                zombie = arcade.SpriteSolidColor(30, 30, arcade.color.DARK_GREEN)
                zombie.hp = ZOMBIE_MAX_HP

        side = random.randint(0, 3)
        spawn_offset = 50
        w, h = self.window.width, self.window.height

        if side == 0:
            zombie.center_x = random.randint(0, w)
            zombie.center_y = h + spawn_offset
        elif side == 1:
            zombie.center_x = w + spawn_offset
            zombie.center_y = random.randint(0, h)
        elif side == 2:
            zombie.center_x = random.randint(0, w)
            zombie.center_y = -spawn_offset
        elif side == 3:
            zombie.center_x = -spawn_offset
            zombie.center_y = random.randint(0, h)

        self.enemy_list.append(zombie)

    def create_blood_effect(self, x, y, is_explosion=False):
        count = 15 if is_explosion else 5
        speed_factor = 4.0 if is_explosion else 2.0
        for _ in range(count):
            particle = Particle(self.blood_textures)
            particle.center_x = x
            particle.center_y = y
            angle = random.random() * 2 * math.pi
            speed = random.random() * speed_factor
            particle.change_x = math.cos(angle) * speed
            particle.change_y = math.sin(angle) * speed
            particle.change_angle = random.randint(-5, 5)
            self.particle_list.append(particle)

    def create_muzzle_flash(self, x, y, angle_deg):
        for _ in range(3):
            particle = Particle(self.smoke_textures)
            particle.center_x = x
            particle.center_y = y
            angle_rad = math.radians(angle_deg + random.randint(-15, 15))
            speed = random.random() * 2.0
            particle.change_x = math.cos(angle_rad) * speed
            particle.change_y = math.sin(angle_rad) * speed
            particle.alpha = 200
            particle.fade_rate = 15
            self.particle_list.append(particle)

    def update_enemies_ai(self):
        BASE_STOP_DISTANCE = 55

        for zombie in self.enemy_list:
            target_x_player = self.player_sprite.center_x
            target_y_player = self.player_sprite.center_y
            target_x_base = self.base_sprite.center_x
            target_y_base = self.base_sprite.center_y

            dist_to_player = math.sqrt(
                (target_x_player - zombie.center_x) ** 2 + (target_y_player - zombie.center_y) ** 2)
            dist_to_base = math.sqrt((target_x_base - zombie.center_x) ** 2 + (target_y_base - zombie.center_y) ** 2)

            if dist_to_player < dist_to_base:
                angle_rad = math.atan2(target_y_player - zombie.center_y, target_x_player - zombie.center_x)
                zombie.angle = math.degrees(angle_rad)
                zombie.change_x = math.cos(angle_rad) * ZOMBIE_SPEED
                zombie.change_y = math.sin(angle_rad) * ZOMBIE_SPEED
            else:
                if dist_to_base < BASE_STOP_DISTANCE:
                    zombie.change_x = 0
                    zombie.change_y = 0
                else:
                    angle_rad = math.atan2(target_y_base - zombie.center_y, target_x_base - zombie.center_x)
                    zombie.angle = math.degrees(angle_rad)
                    zombie.change_x = math.cos(angle_rad) * ZOMBIE_SPEED
                    zombie.change_y = math.sin(angle_rad) * ZOMBIE_SPEED

    def reset_movement(self):
        self.left = False;
        self.right = False;
        self.up = False;
        self.down = False
        self.player_sprite.change_x = 0;
        self.player_sprite.change_y = 0

    def draw_health_bar(self):
        bar_x = 20
        bar_y = self.window.height - 40
        bar_width = 200
        bar_height = 20

        arcade.draw_lbwh_rectangle_filled(bar_x, bar_y, bar_width, bar_height, arcade.color.GRAY)
        health_width = (self.hp / PLAYER_MAX_HP) * bar_width
        if health_width < 0: health_width = 0

        color = arcade.color.GREEN
        if self.hp < PLAYER_MAX_HP * 0.3:
            color = arcade.color.RED
        elif self.hp < PLAYER_MAX_HP * 0.6:
            color = arcade.color.ORANGE

        arcade.draw_lbwh_rectangle_filled(bar_x, bar_y, health_width, bar_height, color)
        arcade.draw_lbwh_rectangle_outline(bar_x, bar_y, bar_width, bar_height, arcade.color.WHITE, 2)
        arcade.draw_text(f" {int(self.hp)}/{PLAYER_MAX_HP}", bar_x + 5, bar_y + 2, arcade.color.WHITE, 12, bold=True)

    def on_draw(self):
        try:
            self.clear()
            self.wall_list.draw()
            self.particle_list.draw()
            self.enemy_list.draw()
            self.player_list.draw()
            self.gun_list.draw()
            self.bullet_list.draw()
            self.draw_health_bar()
            arcade.draw_text("ESC - Пауза | ЛКМ - Огонь", self.window.width - 300, 30, arcade.color.WHITE, 14)

            if time.time() - self.last_hit_time < 0.1:
                arcade.draw_lbwh_rectangle_filled(0, 0, self.window.width, self.window.height, (255, 0, 0, 50))
        except Exception as e:
            print(f"Критическая ошибка отрисовки: {e}")

    def on_update(self, delta_time):
        try:
            self.can_shoot_timer += delta_time

            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0

            if self.up: self.player_sprite.change_y = PLAYER_SPEED
            if self.down: self.player_sprite.change_y = -PLAYER_SPEED
            if self.left: self.player_sprite.change_x = -PLAYER_SPEED
            if self.right: self.player_sprite.change_x = PLAYER_SPEED

            self.physics_engine.update()

            self.pistol_sprite.center_x = self.player_sprite.center_x
            self.pistol_sprite.center_y = self.player_sprite.center_y

            dx = self.mouse_x - self.player_sprite.center_x
            dy = self.mouse_y - self.player_sprite.center_y
            angle_rad = math.atan2(dy, dx)
            self.pistol_sprite.angle = math.degrees(angle_rad)

            self.time_since_last_spawn += delta_time
            if self.time_since_last_spawn > SPAWN_RATE:
                self.spawn_enemy()
                self.time_since_last_spawn = 0

            self.update_enemies_ai()
            self.enemy_list.update()

            self.bullet_list.update()

            for bullet in list(self.bullet_list):
                if (bullet.center_x < 0 or bullet.center_x > self.window.width or
                        bullet.center_y < 0 or bullet.center_y > self.window.height):
                    bullet.remove_from_sprite_lists()
                    continue

                hit_walls = arcade.check_for_collision_with_list(bullet, self.wall_list)
                if hit_walls:
                    bullet.remove_from_sprite_lists()
                    self.create_muzzle_flash(bullet.center_x, bullet.center_y, bullet.angle)
                    continue

                hit_zombies = arcade.check_for_collision_with_list(bullet, self.enemy_list)
                if hit_zombies:
                    bullet.remove_from_sprite_lists()
                    for zombie in hit_zombies:
                        self.create_blood_effect(zombie.center_x, zombie.center_y, is_explosion=False)
                        zombie.hp -= 1
                        if zombie.hp <= 0:
                            self.create_blood_effect(zombie.center_x, zombie.center_y, is_explosion=True)
                            zombie.remove_from_sprite_lists()

            self.particle_list.update()

            hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.enemy_list)
            if hit_list:
                if time.time() - self.last_hit_time > HIT_DELAY:
                    self.hp -= ZOMBIE_DAMAGE
                    self.last_hit_time = time.time()
                    print(f"УРОН! Здоровье: {self.hp}")

                    if self.hp <= 0:
                        game_over = GameOverView()
                        self.window.show_view(game_over)

            if self.player_sprite.left < 0: self.player_sprite.left = 0
            if self.player_sprite.right > self.window.width: self.player_sprite.right = self.window.width
            if self.player_sprite.bottom < 0: self.player_sprite.bottom = 0
            if self.player_sprite.top > self.window.height: self.player_sprite.top = self.window.height

        except Exception as e:
            print(f"Ошибка в обновлении: {e}")
            traceback.print_exc()

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.can_shoot_timer >= SHOOT_DELAY:
                self.can_shoot_timer = 0

                bullet = arcade.Sprite(self.bullet_texture, scale=1.0)

                dx = x - self.pistol_sprite.center_x
                dy = y - self.pistol_sprite.center_y
                angle_rad = math.atan2(dy, dx)

                spawn_dist = 60
                bullet.center_x = self.pistol_sprite.center_x + math.cos(angle_rad) * spawn_dist
                bullet.center_y = self.pistol_sprite.center_y + math.sin(angle_rad) * spawn_dist

                bullet.angle = math.degrees(angle_rad)
                bullet.change_x = math.cos(angle_rad) * BULLET_SPEED
                bullet.change_y = math.sin(angle_rad) * BULLET_SPEED

                self.bullet_list.append(bullet)
                self.create_muzzle_flash(bullet.center_x, bullet.center_y, math.degrees(angle_rad))

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
            self.up = False;
            self.down = False;
            self.left = False;
            self.right = False
            self.player_sprite.change_x = 0;
            self.player_sprite.change_y = 0
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


if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Zombie Defense", fullscreen=True)
    view = GameView()
    view.setup()
    window.show_view(view)
    arcade.run()
