import math
import random
import time
import csv
import os
import arcade
import arcade.gui

# ==============================================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# ==============================================================================

# --- Настройки экрана ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Zombie Defense Optimized"
FULLSCREEN = True

# --- Настройки игрока ---
PLAYER_SPEED = 5
PLAYER_SCALE = 3.0
PLAYER_MAX_HP = 100

# --- Настройки базы ---
BASE_START_MAX_HP = 500
BASE_INTERACTION_DIST = 150
BASE_DAMAGE_FROM_ZOMBIE = 5
BASE_ATTACK_COOLDOWN = 1.0

# --- Настройки зомби ---
ZOMBIE_SPEED = 2
ZOMBIE_SCALE = 3.0
ZOMBIE_MAX_HP = 2
ZOMBIE_DAMAGE = 20
SPAWN_RATE = 1.0

# --- Настройки боя ---
HIT_DELAY = 1.0
BULLET_SPEED = 12
BULLET_SCALE = 2.0
WEAPON_SCALE = 2.5

# --- Настройки декораций ---
DETAILS_SCALE = 3.0
DECO_SCALE = 3.0
NUM_BUSHES = 15
NUM_ROCKS = 8
NUM_TREES = 10

# --- Файлы и системные настройки ---
SAVE_FILE = "savegame.csv"
FONT_UI = "Arial"


# ==============================================================================
# БАЗОВЫЕ КЛАССЫ СУЩНОСТЕЙ
# ==============================================================================

class PixelSprite(arcade.Sprite):
    """Базовый класс для спрайтов с пиксель-арт настройками."""
    pass


class Bullet(PixelSprite):
    """Класс пули. Отвечает за урон и время жизни."""

    def __init__(self, filename, scale, damage, lifetime):
        super().__init__(filename, scale=scale)
        self.damage = damage
        self.lifetime = lifetime

    def update(self, delta_time: float = 1 / 60):
        """Обновление состояния пули."""
        super().update()
        self.lifetime -= delta_time
        if self.lifetime <= 0:
            self.remove_from_sprite_lists()


class Particle(PixelSprite):
    """Класс частицы (кровь, дым, гильзы)."""

    def __init__(self, texture_list, scale=1.0):
        super().__init__(scale=scale)
        self.textures = texture_list
        self.texture = random.choice(texture_list)
        self.change_angle = 0
        self.lifetime = 0.5
        self.fade_rate = 10

    def update(self, delta_time: float = 1 / 60):
        """Обновление физики и прозрачности частицы."""
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.angle += self.change_angle

        # Плавное исчезновение
        if self.alpha > self.fade_rate:
            self.alpha -= self.fade_rate
        else:
            self.remove_from_sprite_lists()


class Zombie(PixelSprite):
    """Класс врага."""

    def __init__(self, filename, scale=1.0):
        super().__init__(filename, scale=scale)
        self.hp = ZOMBIE_MAX_HP
        self.last_attack_time = 0


class Weapon:
    """Класс-контейнер для параметров оружия (не является спрайтом)."""

    def __init__(self, name, texture_path,
                 sound_fire_path, sound_reload_path,
                 mag_size, reload_time, fire_rate,
                 is_auto, damage,
                 price=0, owned=False,
                 bullet_count=1, spread=0, bullet_lifetime=2.0,
                 offset=35):
        self.name = name
        self.price = price
        self.owned = owned

        # Безопасная загрузка ресурсов
        try:
            self.texture = arcade.load_texture(texture_path)
        except FileNotFoundError:
            self.texture = arcade.load_texture("assets/pistol.png")

        try:
            self.sound_fire = arcade.load_sound(sound_fire_path)
        except FileNotFoundError:
            self.sound_fire = None  # Или загрузить заглушку

        try:
            self.sound_reload = arcade.load_sound(sound_reload_path)
        except FileNotFoundError:
            self.sound_reload = None

        self.offset = offset
        self.mag_size = mag_size
        self.current_ammo = mag_size
        self.reload_time = reload_time
        self.fire_rate = fire_rate
        self.is_auto = is_auto

        self.damage = damage
        self.bullet_count = bullet_count
        self.spread = spread
        self.bullet_lifetime = bullet_lifetime

        self.last_shoot_time = 0
        self.is_reloading = False
        self.reload_timer = 0.0


# ==============================================================================
# UI И МЕНЮ
# ==============================================================================

class ShopView(arcade.View):
    """Экран магазина (крафта)."""

    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self._setup_ui()

    def _setup_ui(self):
        # Основной контейнер
        main_layout = arcade.gui.UIBoxLayout(space_between=20)

        title = arcade.gui.UILabel(
            text="МЕНЮ КРАФТА", font_size=30,
            text_color=arcade.color.WHITE, font_name=FONT_UI
        )
        main_layout.add(title.with_padding(bottom=20))

        # Горизонтальный контейнер для товаров
        items_layout = arcade.gui.UIBoxLayout(vertical=False, space_between=30)

        # 1. Улучшение базы
        base_item = self._create_shop_item(
            title="Укрепление базы\n+50 HP",
            texture_path="assets/baseshopimage.png",
            price=self.game_view.base_upgrade_cost,
            is_owned=False,
            on_click_handler=self.buy_base_upgrade
        )
        self.btn_base = base_item["button"]  # Сохраняем ссылку для обновления текста
        items_layout.add(base_item["layout"])

        # 2. Дробовик
        shotgun_w = self.game_view.weapons[1]
        shotgun_item = self._create_shop_item(
            title="Дробовик\n(Убойная мощь)",
            texture_path="assets/shotgunshopimage.png",
            price=shotgun_w.price,
            is_owned=shotgun_w.owned,
            on_click_handler=self.buy_shotgun
        )
        self.btn_shot = shotgun_item["button"]
        items_layout.add(shotgun_item["layout"])

        # 3. Винтовка
        rifle_w = self.game_view.weapons[2]
        rifle_item = self._create_shop_item(
            title="Винтовка\n(Скорострельность)",
            texture_path="assets/riffleshopimage.png",
            price=rifle_w.price,
            is_owned=rifle_w.owned,
            on_click_handler=self.buy_rifle
        )
        self.btn_rif = rifle_item["button"]
        items_layout.add(rifle_item["layout"])

        main_layout.add(items_layout)

        # Кнопка закрытия
        close_btn = arcade.gui.UIFlatButton(text="ЗАКРЫТЬ (ESC)", width=200, height=50)
        close_btn.on_click = self.close_shop
        main_layout.add(close_btn.with_padding(top=50))

        # Центрирование
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(main_layout, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def _create_shop_item(self, title, texture_path, price, is_owned, on_click_handler):
        """Вспомогательный метод для создания карточки товара."""
        col = arcade.gui.UIBoxLayout()

        try:
            texture = arcade.load_texture(texture_path)
        except FileNotFoundError:
            texture = arcade.make_circle_texture(20, arcade.color.GRAY)

        img_btn = arcade.gui.UITextureButton(texture=texture, width=100, height=40)
        col.add(img_btn.with_padding(bottom=10))

        desc_lbl = arcade.gui.UILabel(
            text=title, width=150, align="center", multiline=True,
            font_size=12, text_color=arcade.color.WHITE
        )
        col.add(desc_lbl.with_padding(bottom=10))

        if is_owned:
            btn = arcade.gui.UIFlatButton(text="КУПЛЕНО", width=150, height=40)
            btn.style = {"normal": {"font_color": arcade.color.GRAY, "bg": (50, 50, 50)}}
        else:
            btn = arcade.gui.UIFlatButton(text=f"Цена: {price}", width=150, height=40)
            btn.on_click = on_click_handler

        col.add(btn)
        return {"layout": col, "button": btn}

    def buy_base_upgrade(self, event):
        cost = self.game_view.base_upgrade_cost
        if self.game_view.details_count >= cost:
            self.game_view.details_count -= cost
            self.game_view.base_max_hp += 50
            self.game_view.base_hp += 50
            self.game_view.base_upgrade_cost += 1

            # Обновление UI
            self.btn_base.text = f"Цена: {self.game_view.base_upgrade_cost}"
            self.game_view.invalidate_cache(base=True, details=True)

    def buy_shotgun(self, event):
        w = self.game_view.weapons[1]
        if not w.owned and self.game_view.details_count >= w.price:
            self.game_view.details_count -= w.price
            w.owned = True
            self.btn_shot.text = "КУПЛЕНО"
            self.btn_shot.on_click = None
            self.game_view.invalidate_cache(details=True)

    def buy_rifle(self, event):
        w = self.game_view.weapons[2]
        if not w.owned and self.game_view.details_count >= w.price:
            self.game_view.details_count -= w.price
            w.owned = True
            self.btn_rif.text = "КУПЛЕНО"
            self.btn_rif.on_click = None
            self.game_view.invalidate_cache(details=True)

    def close_shop(self, event):
        self.manager.disable()
        self.window.show_view(self.game_view)

    def on_draw(self):
        self.game_view.on_draw()
        arcade.draw_lbwh_rectangle_filled(0, 0, self.window.width, self.window.height, (0, 0, 0, 200))
        self.manager.draw()
        arcade.draw_text(f"Деталей: {self.game_view.details_count}",
                         self.window.width - 20, self.window.height - 20,
                         arcade.color.YELLOW, 20, anchor_x="right", anchor_y="top", bold=True)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE or key == arcade.key.F:
            self.close_shop(None)


class PauseView(arcade.View):
    """Экран паузы."""

    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.manager = arcade.gui.UIManager()

        self._setup_ui()

    def _setup_ui(self):
        button_style = {
            "normal": {"font_name": (FONT_UI), "font_size": 20, "font_color": arcade.color.WHITE,
                       "bg": (50, 50, 50), "border": arcade.color.WHITE, "border_width": 1},
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

    def on_show_view(self):
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def _on_resume(self, event):
        self.game_view.reset_movement()
        self.window.show_view(self.game_view)

    def _on_menu(self, event):
        try:
            from main import MenuView
            self.window.show_view(MenuView())
        except ImportError:
            print("Ошибка: main.py не найден или цикличный импорт")
            self._on_resume(None)

    def on_draw(self):
        self.game_view.on_draw()
        arcade.draw_lbwh_rectangle_filled(0, 0, self.window.width, self.window.height, (0, 0, 0, 150))
        self.manager.draw()

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.ESCAPE:
            self._on_resume(None)


class GameOverView(arcade.View):
    """Экран проигрыша."""

    def __init__(self, reason="ВЫ ПОГИБЛИ", days_survived=1):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.time_elapsed = 0.0
        self.ui_enabled = False
        self.reason_text = reason
        self.days_survived = days_survived

        self._setup_ui()

    def _setup_ui(self):
        button_style = {
            "normal": {"font_name": (FONT_UI), "font_size": 20, "font_color": arcade.color.WHITE,
                       "bg": (139, 0, 0), "border": arcade.color.WHITE, "border_width": 1},
            "hover": {"font_color": arcade.color.WHITE, "bg": (255, 69, 0)},
            "press": {"font_color": arcade.color.BLACK, "bg": arcade.color.WHITE}
        }

        v_box = arcade.gui.UIBoxLayout(space_between=20)

        label = arcade.gui.UILabel(text=self.reason_text, font_size=48, text_color=arcade.color.RED)
        v_box.add(label.with_padding(bottom=10))

        days_label = arcade.gui.UILabel(text=f"ДНЕЙ ПРОЖИТО: {self.days_survived}", font_size=24,
                                        text_color=arcade.color.YELLOW)
        v_box.add(days_label.with_padding(bottom=30))

        restart_btn = arcade.gui.UIFlatButton(text="ЗАНОВО", width=250, height=50, style=button_style)
        restart_btn.on_click = self._on_restart
        v_box.add(restart_btn)

        menu_btn = arcade.gui.UIFlatButton(text="В МЕНЮ", width=250, height=50, style=button_style)
        menu_btn.on_click = self._on_menu
        v_box.add(menu_btn)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def on_hide_view(self):
        self.manager.disable()

    def on_update(self, delta_time):
        self.time_elapsed += delta_time
        # Небольшая задержка перед активацией кнопок
        if not self.ui_enabled and self.time_elapsed > 1.0:
            self.manager.enable()
            self.ui_enabled = True

    def _on_restart(self, event):
        game = GameView()
        game.setup()
        self.window.show_view(game)

    def _on_menu(self, event):
        try:
            from main import MenuView
            self.window.show_view(MenuView())
        except ImportError:
            print("Ошибка перехода в меню")
            self._on_restart(None)

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.BLACK)
        self.manager.draw()
        if not self.ui_enabled:
            arcade.draw_text("...", self.window.width / 2, 100, arcade.color.WHITE, anchor_x="center")


# ==============================================================================
# ОСНОВНОЙ КЛАСС ИГРЫ
# ==============================================================================

class GameView(arcade.View):
    """
    Основной класс игрового процесса.
    Управляет состоянием мира, игроком, врагами, камерой и отрисовкой.
    """

    def __init__(self):
        super().__init__()

        # --- Камеры ---
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()

        # --- Ресурсы (предзагрузка) ---
        try:
            self.detail_texture = arcade.load_texture("assets/details.png")
        except FileNotFoundError:
            self.detail_texture = arcade.make_circle_texture(20, arcade.color.YELLOW)

        # Предзагрузка текстур частиц
        self.blood_textures = [
            arcade.make_circle_texture(diameter=random.randint(4, 10), color=arcade.color.RED_DEVIL)
            for _ in range(4)
        ]
        self.smoke_textures = [
            arcade.make_circle_texture(diameter=random.randint(5, 12), color=arcade.color.GRAY)
            for _ in range(3)
        ]

        # --- Списки спрайтов ---
        self.decoration_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.base_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.particle_list = arcade.SpriteList()
        self.gun_list = arcade.SpriteList()
        self.items_list = arcade.SpriteList()
        self.ui_list = arcade.SpriteList()

        # --- Ссылки на ключевые объекты ---
        self.player_sprite = None
        self.weapon_sprite = None
        self.base_sprite = None
        self.ui_detail_sprite = None
        self.physics_engine = None

        # --- Игровое состояние ---
        self.hp = PLAYER_MAX_HP
        self.base_hp = BASE_START_MAX_HP
        self.base_max_hp = BASE_START_MAX_HP
        self.base_upgrade_cost = 6
        self.details_count = 0

        self.last_hit_time = 0
        self.time_since_last_spawn = 0.0

        # --- Волны ---
        self.day = 1
        self.wave = 0
        self.zombies_to_spawn_total = 0
        self.zombies_spawned_count = 0
        self.wave_in_progress = False
        self.wave_timer = 0.0
        self.wave_cooldown = 3.0

        # --- Ввод ---
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.mouse_pressed = False
        self.mouse_x = 0
        self.mouse_y = 0

        # --- Оружие ---
        self.weapons = []
        self.current_weapon_index = 0
        self.bob_time = 0.0

        # --- Текстовые объекты UI ---
        self._init_ui_text()

        # Кэш переменных для оптимизации обновления текста
        self._cache_day = -1
        self._cache_wave = -1
        self._cache_wave_state = None
        self._cache_timer_int = -1
        self._cache_base_hp = -1
        self._cache_base_max_hp = -1
        self._cache_player_hp = -1
        self._cache_ammo = -1
        self._cache_details = -1
        self._cache_weapon_name = ""

    def _init_ui_text(self):
        """Инициализация объектов текста для GUI."""
        cx = self.window.width // 2
        top_y = self.window.height - 40

        self.text_day_wave = arcade.Text(
            "ПОДГОТОВКА...", cx, top_y, arcade.color.WHITE, 24, anchor_x="center", bold=True
        )
        self.text_base_hp = arcade.Text(
            "", cx, top_y - 28, arcade.color.WHITE, 12, anchor_x="center", bold=True
        )
        self.text_player_hp = arcade.Text(
            "", 30, self.window.height - 52, arcade.color.WHITE, 20, bold=True
        )

        start_x, start_y = 20, 20
        self.text_ammo_curr = arcade.Text(
            "0", start_x, start_y, arcade.color.WHITE, 30, font_name=FONT_UI, bold=True
        )
        self.text_ammo_max = arcade.Text(
            "/0", start_x + 40, start_y, arcade.color.WHITE, 30, font_name=FONT_UI, bold=True
        )
        self.text_reloading = arcade.Text(
            "ПЕРЕЗАРЯДКА...", start_x, start_y + 40, arcade.color.YELLOW, 12, bold=True
        )
        self.text_weapon_name = arcade.Text(
            "", start_x, start_y + 60, arcade.color.CYAN, 14, bold=True
        )

        self.text_help = arcade.Text(
            "ESC-Пауза | ЛКМ-Огонь | R-Перезарядка | 1,2,3-Смена оружия",
            self.window.width - 650, 30, arcade.color.WHITE, 14
        )
        self.text_details_count = arcade.Text(
            "0", self.window.width - 50, 20, arcade.color.WHITE, 30, anchor_x="right", bold=True
        )

    def setup(self):
        """Настройка новой игры или сброс."""
        self.decoration_list.clear()
        self.player_list.clear()
        self.wall_list.clear()
        self.base_list.clear()
        self.enemy_list.clear()
        self.bullet_list.clear()
        self.particle_list.clear()
        self.gun_list.clear()
        self.items_list.clear()
        self.ui_list.clear()

        self.hp = PLAYER_MAX_HP
        self.base_hp = BASE_START_MAX_HP
        self.base_max_hp = BASE_START_MAX_HP
        self.base_upgrade_cost = 6
        self.details_count = 0
        self.day = 1
        self.wave = 0
        self.wave_in_progress = False
        self.wave_timer = 0.0
        self.wave_cooldown = 3.0

        # Генерация мира
        self.generate_new_level()
        self._setup_weapons()
        self._setup_entities()

        # Физика
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)

        self._cache_day = -1  # Сброс кэша

        # Загрузка сохранения
        if os.path.exists(SAVE_FILE):
            self.load_game()

    def _setup_weapons(self):
        pistol = Weapon(
            name="Пистолет",
            texture_path="assets/pistol.png",
            sound_fire_path="assets/sounds/pistol_fire.wav",
            sound_reload_path="assets/sounds/pistol_reload.wav",
            mag_size=7, reload_time=1.0, fire_rate=0.15, is_auto=False, damage=1,
            owned=True, price=0, offset=35
        )
        shotgun = Weapon(
            name="Дробовик",
            texture_path="assets/shotgun.png",
            sound_fire_path="assets/sounds/shotgun_fire.wav",
            sound_reload_path="assets/sounds/shotgun_reload.wav",
            mag_size=5, reload_time=2.0, fire_rate=0.8, is_auto=False, damage=10,
            bullet_count=5, spread=15, bullet_lifetime=0.25,
            owned=False, price=5, offset=45
        )
        rifle = Weapon(
            name="Автомат",
            texture_path="assets/riffle.png",
            sound_fire_path="assets/sounds/pistol_fire.wav",
            sound_reload_path="assets/sounds/riffle_reload.wav",
            mag_size=30, reload_time=1.5, fire_rate=0.1, is_auto=True, damage=1,
            bullet_lifetime=2.0,
            owned=False, price=12, offset=45
        )
        self.weapons = [pistol, shotgun, rifle]
        self.current_weapon_index = 0

    def _setup_entities(self):
        cx, cy = self.window.width // 2, self.window.height // 2

        # UI Деталь
        self.ui_detail_sprite = PixelSprite(scale=2.5)
        self.ui_detail_sprite.texture = self.detail_texture
        self.ui_detail_sprite.center_x = self.window.width - 40
        self.ui_detail_sprite.center_y = 35
        self.ui_list.append(self.ui_detail_sprite)

        # База
        self.base_sprite = PixelSprite("assets/base.png", scale=2)
        self.base_sprite.center_x, self.base_sprite.center_y = cx, cy
        self.base_list.append(self.base_sprite)

        # Игрок
        self.player_sprite = PixelSprite("assets/MainCharacter.png", scale=PLAYER_SCALE)
        self.player_sprite.center_x, self.player_sprite.center_y = cx, cy - 100
        self.player_list.append(self.player_sprite)

        # Оружие
        self.weapon_sprite = PixelSprite(scale=WEAPON_SCALE)
        self.update_weapon_texture()
        self.gun_list.append(self.weapon_sprite)

    def generate_new_level(self):
        self.decoration_list.clear()
        bg_colors = [
            arcade.color.DARK_OLIVE_GREEN, arcade.color.DARK_SLATE_GRAY,
            arcade.color.OLIVE_DRAB, arcade.color.SIENNA, arcade.color.FOREST_GREEN
        ]
        arcade.set_background_color(random.choice(bg_colors))

        def spawn_decor(filename, count, min_dist=250):
            try:
                arcade.load_texture(filename)
            except Exception:
                return

            for _ in range(count):
                sprite = PixelSprite(filename, scale=DECO_SCALE)
                for _ in range(10):  # 10 попыток найти место
                    x = random.randint(0, self.window.width)
                    y = random.randint(0, self.window.height)
                    if math.hypot(x - self.window.width // 2, y - self.window.height // 2) > min_dist:
                        sprite.center_x, sprite.center_y = x, y
                        self.decoration_list.append(sprite)
                        break

        spawn_decor("assets/bash.png", NUM_BUSHES)
        spawn_decor("assets/rock.png", NUM_ROCKS)
        spawn_decor("assets/tree1.png", NUM_TREES // 2)
        spawn_decor("assets/tree2.png", NUM_TREES // 2)

    def save_game(self):
        try:
            with open(SAVE_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['day', 'hp', 'base_hp', 'base_max_hp', 'details',
                                 'upgrade_cost', 'shotgun_owned', 'rifle_owned'])
                writer.writerow([
                    self.day, self.hp, self.base_hp, self.base_max_hp,
                    self.details_count, self.base_upgrade_cost,
                    self.weapons[1].owned, self.weapons[2].owned
                ])
            print(f"Игра сохранена. День: {self.day}")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load_game(self):
        if not os.path.exists(SAVE_FILE): return
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.day = int(row['day'])
                    self.hp = float(row['hp'])
                    self.base_hp = float(row['base_hp'])
                    self.base_max_hp = float(row['base_max_hp'])
                    self.details_count = int(row['details'])
                    self.base_upgrade_cost = int(row['upgrade_cost'])
                    self.weapons[1].owned = (row['shotgun_owned'] == 'True')
                    self.weapons[2].owned = (row['rifle_owned'] == 'True')

            print(f"Игра загружена. День: {self.day}")
            self.generate_new_level()
            self.invalidate_cache(day=True, base=True, details=True)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")

    def invalidate_cache(self, day=False, base=False, details=False):
        """Сброс кэша UI."""
        if day: self._cache_day = -1
        if base: self._cache_base_hp = -1
        if details: self._cache_details = -1

    def update_weapon_texture(self):
        curr_weapon = self.weapons[self.current_weapon_index]
        self.weapon_sprite.texture = curr_weapon.texture

    @property
    def active_weapon(self):
        return self.weapons[self.current_weapon_index]

    def start_next_wave(self):
        self.wave += 1
        if self.wave > 3:
            self.day += 1
            self.wave = 1
            self.save_game()
            self.generate_new_level()

        count = 4 + (self.day * 2) + (self.wave * 3) + random.randint(0, self.day + 2)
        self.zombies_to_spawn_total = int(count)
        self.zombies_spawned_count = 0
        self.wave_in_progress = True
        print(f"День {self.day}, Волна {self.wave}: Зомби {self.zombies_to_spawn_total}")

    def spawn_enemy(self):
        if self.zombies_spawned_count >= self.zombies_to_spawn_total: return

        zombie = Zombie("assets/zombie.png", scale=ZOMBIE_SCALE)
        side = random.randint(0, 3)
        offset = 50
        w, h = self.window.width, self.window.height

        if side == 0:
            zombie.position = (random.randint(0, w), h + offset)
        elif side == 1:
            zombie.position = (w + offset, random.randint(0, h))
        elif side == 2:
            zombie.position = (random.randint(0, w), -offset)
        elif side == 3:
            zombie.position = (-offset, random.randint(0, h))

        self.enemy_list.append(zombie)
        self.zombies_spawned_count += 1

    def spawn_detail(self, x, y):
        detail = PixelSprite(scale=DETAILS_SCALE)
        detail.texture = self.detail_texture
        detail.center_x, detail.center_y = x, y
        self.items_list.append(detail)

    def create_blood_effect(self, x, y, is_explosion=False):
        count = 15 if is_explosion else 5
        speed = 4.0 if is_explosion else 2.0
        for _ in range(count):
            p = Particle(self.blood_textures)
            p.center_x, p.center_y = x, y
            angle = random.random() * 2 * math.pi
            s = random.random() * speed
            p.change_x = math.cos(angle) * s
            p.change_y = math.sin(angle) * s
            p.change_angle = random.randint(-5, 5)
            self.particle_list.append(p)

    def create_muzzle_flash(self, x, y, angle_deg):
        for _ in range(3):
            p = Particle(self.smoke_textures)
            p.center_x, p.center_y = x, y
            angle_rad = math.radians(angle_deg + random.randint(-15, 15))
            s = random.random() * 2.0
            p.change_x = math.cos(angle_rad) * s
            p.change_y = math.sin(angle_rad) * s
            p.alpha = 200
            p.fade_rate = 15
            self.particle_list.append(p)

    def update_enemies_ai(self):
        BASE_STOP_DISTANCE = 55
        current_time = time.time()

        for zombie in self.enemy_list:
            dist_p = arcade.get_distance_between_sprites(zombie, self.player_sprite)
            dist_b = arcade.get_distance_between_sprites(zombie, self.base_sprite)

            target = self.player_sprite if dist_p < dist_b else self.base_sprite
            is_base = (target == self.base_sprite)

            angle_rad = math.atan2(target.center_y - zombie.center_y,
                                   target.center_x - zombie.center_x)

            if is_base and dist_b < BASE_STOP_DISTANCE:
                zombie.change_x, zombie.change_y = 0, 0
                if current_time - zombie.last_attack_time > BASE_ATTACK_COOLDOWN:
                    self.base_hp -= BASE_DAMAGE_FROM_ZOMBIE
                    zombie.last_attack_time = current_time
            else:
                zombie.angle = math.degrees(angle_rad)
                zombie.change_x = math.cos(angle_rad) * ZOMBIE_SPEED
                zombie.change_y = math.sin(angle_rad) * ZOMBIE_SPEED

    def reset_movement(self):
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

    def start_reload(self):
        w = self.active_weapon
        if not w.is_reloading and w.current_ammo < w.mag_size:
            w.is_reloading = True
            w.reload_timer = 0.0
            if w.sound_reload:
                arcade.play_sound(w.sound_reload)

    def update_text_objects(self):
        # Кэширование для оптимизации. Текст обновляется только при изменении значений.
        timer_remaining = int(self.wave_cooldown - self.wave_timer)

        # Обновление текста волны
        if (self.day != self._cache_day or
                self.wave != self._cache_wave or
                self.wave_in_progress != self._cache_wave_state or
                (not self.wave_in_progress and timer_remaining != self._cache_timer_int)):

            self._cache_day = self.day
            self._cache_wave = self.wave
            self._cache_wave_state = self.wave_in_progress
            self._cache_timer_int = timer_remaining

            info = f"ДЕНЬ {self.day} | ВОЛНА {self.wave}/3"
            if not self.wave_in_progress:
                info += f" (ПОДГОТОВКА: {max(0, timer_remaining)})"
            self.text_day_wave.text = info

        # HP Базы
        int_base_hp = int(max(0, self.base_hp))
        if int_base_hp != self._cache_base_hp or self.base_max_hp != self._cache_base_max_hp:
            self._cache_base_hp = int_base_hp
            self._cache_base_max_hp = self.base_max_hp
            self.text_base_hp.text = f"БАЗА: {int_base_hp}/{self.base_max_hp}"

        # HP Игрока
        int_player_hp = int(max(0, self.hp))
        if int_player_hp != self._cache_player_hp:
            self._cache_player_hp = int_player_hp
            self.text_player_hp.text = f"HP: {int_player_hp}/{PLAYER_MAX_HP}"

        # Патроны
        w = self.active_weapon
        if w.current_ammo != self._cache_ammo:
            self._cache_ammo = w.current_ammo
            self.text_ammo_curr.text = str(w.current_ammo)
            self.text_ammo_curr.color = arcade.color.RED if w.current_ammo < w.mag_size * 0.3 else arcade.color.WHITE
            self.text_ammo_max.text = f"/{w.mag_size}"
            offset_x = len(self.text_ammo_curr.text) * 18 + 5
            self.text_ammo_max.x = 20 + offset_x

        if w.name != self._cache_weapon_name:
            self._cache_weapon_name = w.name
            self.text_weapon_name.text = w.name.upper()

        if self.details_count != self._cache_details:
            self._cache_details = self.details_count
            self.text_details_count.text = str(self.details_count)
            text_width = self.text_details_count.content_width
            self.ui_detail_sprite.center_x = self.window.width - 50 - text_width - 35

    def draw_ui_shapes(self):
        # Полоска здоровья игрока
        bar_x, bar_y, bar_w, bar_h = 20, self.window.height - 60, 300, 30
        arcade.draw_lbwh_rectangle_filled(bar_x, bar_y, bar_w, bar_h, arcade.color.GRAY)

        hp_pct = self.hp / PLAYER_MAX_HP
        fill_w = max(0, hp_pct * bar_w)
        color = arcade.color.GREEN
        if hp_pct < 0.3:
            color = arcade.color.RED
        elif hp_pct < 0.6:
            color = arcade.color.ORANGE

        arcade.draw_lbwh_rectangle_filled(bar_x, bar_y, fill_w, bar_h, color)
        arcade.draw_lbwh_rectangle_outline(bar_x, bar_y, bar_w, bar_h, arcade.color.WHITE, 2)

        # Полоска здоровья базы
        cx = self.window.width // 2
        top_y = self.window.height - 40
        base_w, base_h = 300, 20
        base_x, base_y = cx - base_w // 2, top_y - 30

        arcade.draw_lbwh_rectangle_filled(base_x, base_y, base_w, base_h, (50, 50, 50))
        fill_w_base = max(0, (self.base_hp / self.base_max_hp) * base_w)
        b_color = arcade.color.RED if self.base_hp < 150 else arcade.color.BLUE

        arcade.draw_lbwh_rectangle_filled(base_x, base_y, fill_w_base, base_h, b_color)
        arcade.draw_lbwh_rectangle_outline(base_x, base_y, base_w, base_h, arcade.color.WHITE, 2)

    def on_draw(self):
        self.clear()
        self.window.ctx.default_atlas.texture_filter = self.window.ctx.NEAREST

        # 1. СЛОЙ МИРА
        self.camera.use()
        self.decoration_list.draw(pixelated=True)
        self.base_list.draw(pixelated=True)
        self.items_list.draw(pixelated=True)
        self.particle_list.draw(pixelated=True)
        self.enemy_list.draw(pixelated=True)
        self.player_list.draw(pixelated=True)
        self.gun_list.draw(pixelated=True)
        self.bullet_list.draw(pixelated=True)

        # Подсказки
        for item in self.items_list:
            if arcade.get_distance_between_sprites(self.player_sprite, item) < 50:
                arcade.draw_text("E - Подобрать", item.center_x, item.top + 10,
                                 arcade.color.YELLOW, 12, anchor_x="center")

        if arcade.get_distance_between_sprites(self.player_sprite, self.base_sprite) < BASE_INTERACTION_DIST:
            arcade.draw_text("Открыть меню крафта - F", self.base_sprite.center_x,
                             self.base_sprite.top + 20, arcade.color.CYAN, 14,
                             anchor_x="center", bold=True)

        # 2. СЛОЙ GUI
        self.gui_camera.use()
        self.draw_ui_shapes()

        self.text_day_wave.draw()
        self.text_base_hp.draw()
        self.text_player_hp.draw()
        self.text_ammo_curr.draw()
        self.text_ammo_max.draw()
        self.text_weapon_name.draw()
        self.text_help.draw()
        self.ui_list.draw(pixelated=True)
        self.text_details_count.draw()

        if self.active_weapon.is_reloading:
            self.text_reloading.draw()

        # Эффект удара (красный экран)
        if time.time() - self.last_hit_time < 0.1:
            arcade.draw_lbwh_rectangle_filled(0, 0, self.window.width, self.window.height, (255, 0, 0, 50))

    def on_update(self, delta_time):
        # Регенерация базы
        if self.base_hp < self.base_max_hp:
            self.base_hp = min(self.base_max_hp, self.base_hp + 2 * delta_time)

        # Обновление оружия
        w = self.active_weapon
        w.last_shoot_time += delta_time
        if w.is_reloading:
            w.reload_timer += delta_time
            if w.reload_timer >= w.reload_time:
                w.current_ammo = w.mag_size
                w.is_reloading = False
                w.reload_timer = 0.0
                self._cache_ammo = -1

        # Автоматическая стрельба
        if self.mouse_pressed and w.is_auto and not w.is_reloading:
            self.attempt_shoot()

        # Движение игрока
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        if self.up: self.player_sprite.change_y = PLAYER_SPEED
        if self.down: self.player_sprite.change_y = -PLAYER_SPEED
        if self.left: self.player_sprite.change_x = -PLAYER_SPEED
        if self.right: self.player_sprite.change_x = PLAYER_SPEED
        self.physics_engine.update()

        # Ограничение движения (Clamp)
        self.player_sprite.left = max(0, self.player_sprite.left)
        self.player_sprite.right = min(SCREEN_WIDTH, self.player_sprite.right)
        self.player_sprite.bottom = max(0, self.player_sprite.bottom)
        self.player_sprite.top = min(SCREEN_HEIGHT, self.player_sprite.top)

        # Анимация "шага" (Bobbing)
        if self.player_sprite.change_x != 0 or self.player_sprite.change_y != 0:
            self.bob_time += delta_time * 15
            bob = math.sin(self.bob_time) * 0.1
            self.player_sprite.scale_y = PLAYER_SCALE + bob
            self.player_sprite.scale_x = PLAYER_SCALE - (bob * 0.5)
        else:
            self.player_sprite.scale_y = PLAYER_SCALE
            self.player_sprite.scale_x = PLAYER_SCALE

        # Камера (Плавное слежение)
        tx, ty = self.player_sprite.center_x, self.player_sprite.center_y
        cx, cy = self.camera.position
        self.camera.position = (cx + (tx - cx) * 0.1, cy + (ty - cy) * 0.1)

        # Поворот оружия
        world_mx = self.mouse_x + (self.camera.position.x - self.window.width / 2)
        world_my = self.mouse_y + (self.camera.position.y - self.window.height / 2)
        dx = world_mx - self.weapon_sprite.center_x
        dy = world_my - self.weapon_sprite.center_y
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)

        extra_rot = (w.reload_timer / w.reload_time) * 360 if w.is_reloading else 0

        self.weapon_sprite.center_x = self.player_sprite.center_x + math.cos(angle_rad) * w.offset
        self.weapon_sprite.center_y = self.player_sprite.center_y + math.sin(angle_rad) * w.offset

        base_angle = -angle_deg
        if dx < 0:
            # Отражение спрайта при взгляде влево
            self.player_sprite.scale_x = -PLAYER_SCALE if self.player_sprite.scale_x > 0 else self.player_sprite.scale_x
            self.weapon_sprite.scale_y = -WEAPON_SCALE
            self.weapon_sprite.angle = base_angle - extra_rot
        else:
            self.player_sprite.scale_x = PLAYER_SCALE if self.player_sprite.scale_x > 0 else -self.player_sprite.scale_x
            self.weapon_sprite.scale_y = WEAPON_SCALE
            self.weapon_sprite.angle = base_angle + extra_rot

        # Логика волн
        if not self.wave_in_progress:
            self.wave_timer += delta_time
            if self.wave_timer > self.wave_cooldown:
                self.start_next_wave()
        else:
            if self.zombies_spawned_count < self.zombies_to_spawn_total:
                self.time_since_last_spawn += delta_time
                if self.time_since_last_spawn > SPAWN_RATE:
                    self.spawn_enemy()
                    self.time_since_last_spawn = 0

            if self.zombies_spawned_count >= self.zombies_to_spawn_total and len(self.enemy_list) == 0:
                self.wave_in_progress = False
                self.wave_timer = 0.0
                self.wave_cooldown = 10.0 if self.wave >= 3 else 3.0

        # Обновление врагов
        self.update_enemies_ai()
        self.enemy_list.update()
        self.update_text_objects()

        if self.base_hp <= 0:
            self.window.show_view(GameOverView("БАЗА УНИЧТОЖЕНА", days_survived=self.day))

        # Обновление пуль и коллизий
        self.bullet_list.update()
        for bullet in list(self.bullet_list):
            if arcade.check_for_collision_with_list(bullet, self.wall_list):
                bullet.remove_from_sprite_lists()
                self.create_muzzle_flash(bullet.center_x, bullet.center_y, bullet.angle)
                continue

            hit_zombies = arcade.check_for_collision_with_list(bullet, self.enemy_list)
            if hit_zombies:
                bullet.remove_from_sprite_lists()
                for zombie in hit_zombies:
                    self.create_blood_effect(zombie.center_x, zombie.center_y, False)
                    zombie.hp -= bullet.damage
                    if zombie.hp <= 0:
                        self.create_blood_effect(zombie.center_x, zombie.center_y, True)
                        if random.randint(1, 3) == 1:
                            self.spawn_detail(zombie.center_x, zombie.center_y)
                        zombie.remove_from_sprite_lists()

        self.particle_list.update()

        # Урон игроку
        if arcade.check_for_collision_with_list(self.player_sprite, self.enemy_list):
            if time.time() - self.last_hit_time > HIT_DELAY:
                self.hp -= ZOMBIE_DAMAGE
                self.last_hit_time = time.time()
                if self.hp <= 0:
                    self.window.show_view(GameOverView("ВЫ ПОГИБЛИ", days_survived=self.day))

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def attempt_shoot(self):
        w = self.active_weapon
        if w.is_reloading: return
        if w.current_ammo <= 0:
            self.start_reload()
            return

        if w.last_shoot_time >= w.fire_rate:
            w.last_shoot_time = 0
            w.current_ammo -= 1
            if w.sound_fire:
                arcade.play_sound(w.sound_fire)
            self._cache_ammo = -1

            world_mx = self.mouse_x + (self.camera.position.x - self.window.width / 2)
            world_my = self.mouse_y + (self.camera.position.y - self.window.height / 2)

            dx = world_mx - self.weapon_sprite.center_x
            dy = world_my - self.weapon_sprite.center_y
            base_angle_rad = math.atan2(dy, dx)
            base_angle_deg = math.degrees(base_angle_rad)
            barrel_length = 30

            for _ in range(w.bullet_count):
                bullet = Bullet("assets/pistol_bullet.png", scale=BULLET_SCALE,
                                damage=w.damage, lifetime=w.bullet_lifetime)

                angle_offset = random.uniform(-w.spread, w.spread)
                final_deg = base_angle_deg + angle_offset
                final_rad = math.radians(final_deg)

                bullet.center_x = self.weapon_sprite.center_x + math.cos(base_angle_rad) * barrel_length
                bullet.center_y = self.weapon_sprite.center_y + math.sin(base_angle_rad) * barrel_length
                bullet.angle = final_deg
                bullet.change_x = math.cos(final_rad) * BULLET_SPEED
                bullet.change_y = math.sin(final_rad) * BULLET_SPEED

                self.bullet_list.append(bullet)

            self.create_muzzle_flash(
                self.weapon_sprite.center_x + math.cos(base_angle_rad) * barrel_length,
                self.weapon_sprite.center_y + math.sin(base_angle_rad) * barrel_length,
                base_angle_deg
            )

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_pressed = True
            if not self.active_weapon.is_auto:
                self.attempt_shoot()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_pressed = False

    def on_key_press(self, key, _modifiers):
        if key in (arcade.key.W, arcade.key.UP):
            self.up = True
        elif key in (arcade.key.S, arcade.key.DOWN):
            self.down = True
        elif key in (arcade.key.A, arcade.key.LEFT):
            self.left = True
        elif key in (arcade.key.D, arcade.key.RIGHT):
            self.right = True
        elif key == arcade.key.R:
            self.start_reload()

        elif key == arcade.key.KEY_1:
            self._switch_weapon(0)
        elif key == arcade.key.KEY_2:
            self._switch_weapon(1)
        elif key == arcade.key.KEY_3:
            self._switch_weapon(2)

        elif key == arcade.key.E:
            self._try_pickup_item()

        elif key == arcade.key.F:
            dist = arcade.get_distance_between_sprites(self.player_sprite, self.base_sprite)
            if dist < BASE_INTERACTION_DIST:
                self.reset_movement()
                self.mouse_pressed = False
                self.window.show_view(ShopView(self))

        elif key == arcade.key.ESCAPE:
            self.reset_movement()
            self.window.show_view(PauseView(self))

    def on_key_release(self, key, _modifiers):
        if key in (arcade.key.W, arcade.key.UP):
            self.up = False
        elif key in (arcade.key.S, arcade.key.DOWN):
            self.down = False
        elif key in (arcade.key.A, arcade.key.LEFT):
            self.left = False
        elif key in (arcade.key.D, arcade.key.RIGHT):
            self.right = False

    def _switch_weapon(self, index):
        if self.weapons[index].owned:
            self.current_weapon_index = index
            self.update_weapon_texture()
            self._cache_ammo = -1

    def _try_pickup_item(self):
        closest, min_dist = None, 50
        for item in self.items_list:
            dist = arcade.get_distance_between_sprites(self.player_sprite, item)
            if dist < min_dist:
                closest, min_dist = item, dist

        if closest:
            closest.remove_from_sprite_lists()
            self.details_count += 1
            self._cache_details = -1


if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True, antialiasing=False)
    view = GameView()
    view.setup()
    window.show_view(view)
    arcade.run()