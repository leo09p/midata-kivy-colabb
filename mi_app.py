import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.core.window import Window

import os
import json
import hashlib
import time
import sounddevice as sd
from scipy.io.wavfile import write, read as wav_read
from plyer import camera

# Configuración de color de fondo
Window.clearcolor = (0.95, 0.95, 0.95, 1)

BASE_FOLDER = "vault_data"
PASSWORD_FILE = os.path.join(BASE_FOLDER, "password.json")


def create_button(text, size_hint_y=0.1, font_size=22, bg_color=(0.2, 0.6, 0.86, 1)):
    btn = Button(
        text=text,
        size_hint_y=size_hint_y,
        font_size=font_size,
        background_normal='',
        background_color=bg_color,
        color=(1, 1, 1, 1),
        padding=(10, 10)
    )
    return btn


class VaultApp(App):
    def build(self):
        if not os.path.exists(BASE_FOLDER):
            os.makedirs(BASE_FOLDER)

        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.current_folder = None

        if not os.path.exists(PASSWORD_FILE):
            self.show_create_password_screen()
        else:
            self.show_login_screen()

        return self.main_layout

    # Pantalla de creación de contraseña
    def show_create_password_screen(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(Label(text="Crear contraseña", font_size=32, size_hint_y=0.2, color=(0, 0, 0, 1)))
        self.password_input = TextInput(password=True, multiline=False, font_size=24, size_hint_y=0.2)
        self.main_layout.add_widget(self.password_input)

        save_button = create_button("Guardar")
        save_button.bind(on_press=self.save_password)
        self.main_layout.add_widget(save_button)

    def save_password(self, instance):
        password = self.password_input.text.strip()
        if not password:
            self.show_popup("La contraseña no puede estar vacía.")
            return
        hashed = hashlib.sha256(password.encode()).hexdigest()
        with open(PASSWORD_FILE, "w") as f:
            json.dump({"password": hashed}, f)
        self.show_popup("Contraseña guardada. Inicia sesión.")
        self.show_login_screen()

    # Pantalla de login
    def show_login_screen(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(Label(text="Ingresa tu contraseña", font_size=32, size_hint_y=0.2, color=(0, 0, 0, 1)))
        self.login_input = TextInput(password=True, multiline=False, font_size=24, size_hint_y=0.2)
        self.main_layout.add_widget(self.login_input)

        login_button = create_button("Entrar")
        login_button.bind(on_press=self.check_login)
        self.main_layout.add_widget(login_button)

    def check_login(self, instance):
        password = self.login_input.text.strip()
        with open(PASSWORD_FILE, "r") as f:
            data = json.load(f)
        hashed = hashlib.sha256(password.encode()).hexdigest()
        if hashed == data["password"]:
            self.show_main_screen()
        else:
            self.show_popup("Contraseña incorrecta")

    # Pantalla principal (reconstruida siempre correctamente)
    def show_main_screen(self):
        self.main_layout.clear_widgets()

        self.main_layout.add_widget(Label(text="Tus carpetas", font_size=32, size_hint_y=0.1, color=(0, 0, 0, 1)))

        add_folder_button = create_button("➕ Crear nueva carpeta")
        add_folder_button.bind(on_press=self.create_new_folder)
        self.main_layout.add_widget(add_folder_button)

        scroll = ScrollView(size_hint_y=0.8, bar_width=10)
        self.folder_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=5)
        self.folder_box.bind(minimum_height=self.folder_box.setter('height'))
        scroll.add_widget(self.folder_box)
        self.main_layout.add_widget(scroll)

        self.load_folders()

    def create_new_folder(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.folder_input = TextInput(hint_text="Nombre de la carpeta", multiline=False, font_size=20)
        content.add_widget(self.folder_input)

        save_button = create_button("Crear", size_hint_y=0.3)
        content.add_widget(save_button)

        popup = Popup(title="Nueva carpeta", content=content, size_hint=(0.8, 0.5))
        save_button.bind(on_press=lambda *args: self.save_folder(popup))
        popup.open()

    def save_folder(self, popup):
        folder_name = self.folder_input.text.strip()
        if not folder_name:
            self.show_popup("Nombre vacío.")
            return

        folder_path = os.path.join(BASE_FOLDER, folder_name)
        if os.path.exists(folder_path):
            self.show_popup("Ya existe una carpeta con ese nombre.")
            return

        os.makedirs(os.path.join(folder_path, "notas"))
        os.makedirs(os.path.join(folder_path, "imagenes"))
        os.makedirs(os.path.join(folder_path, "audios"))
        popup.dismiss()
        self.show_main_screen()

    def load_folders(self):
        self.folder_box.clear_widgets()
        folders = [f for f in os.listdir(BASE_FOLDER) if os.path.isdir(os.path.join(BASE_FOLDER, f)) and f != "password.json"]

        for folder in folders:
            btn = create_button(folder, size_hint_y=None, font_size=24, bg_color=(0.3, 0.7, 0.5, 1))
            btn.height = 60
            btn.bind(on_press=lambda instance, name=folder: self.enter_folder(name))
            self.folder_box.add_widget(btn)

    # Entrar a una carpeta
    def enter_folder(self, folder_name):
        self.current_folder = folder_name
        self.main_layout.clear_widgets()

        self.main_layout.add_widget(Label(text=f"📂 {folder_name}", font_size=28, size_hint_y=0.1, color=(0, 0, 0, 1)))

        button_layout = BoxLayout(size_hint_y=0.15, spacing=10)

        add_note_button = create_button("➕ Nueva Nota", font_size=20)
        add_note_button.bind(on_press=self.create_new_note)
        button_layout.add_widget(add_note_button)

        add_image_button = create_button("📸 Agregar Imagen", font_size=20)
        add_image_button.bind(on_press=self.add_new_image)
        button_layout.add_widget(add_image_button)

        take_photo_button = create_button("📷 Tomar Foto", font_size=20, bg_color=(0.3, 0.8, 0.4, 1))
        take_photo_button.bind(on_press=self.take_photo)
        button_layout.add_widget(take_photo_button)

        record_audio_button = create_button("🎙 Grabar Audio", font_size=20, bg_color=(0.8, 0.3, 0.3, 1))
        record_audio_button.bind(on_press=self.record_audio)
        button_layout.add_widget(record_audio_button)

        self.main_layout.add_widget(button_layout)

        back_button = create_button("⬅️ Volver", font_size=22, bg_color=(0.4, 0.4, 0.4, 1))
        back_button.bind(on_press=lambda x: self.show_main_screen())
        self.main_layout.add_widget(back_button)

        scroll = ScrollView(size_hint_y=0.65)
        self.folder_content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=5)
        self.folder_content_box.bind(minimum_height=self.folder_content_box.setter('height'))
        scroll.add_widget(self.folder_content_box)
        self.main_layout.add_widget(scroll)

        self.load_notes()
        self.load_images()
        self.load_audios()

    # Notas
    def create_new_note(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title_input = TextInput(hint_text="Título de la nota", multiline=False, font_size=20)
        body_input = TextInput(hint_text="Contenido de la nota", multiline=True, font_size=20, size_hint_y=3)
        content.add_widget(title_input)
        content.add_widget(body_input)

        save_button = create_button("Guardar Nota", size_hint_y=0.3)
        content.add_widget(save_button)

        popup = Popup(title="Nueva Nota", content=content, size_hint=(0.8, 0.8))
        save_button.bind(on_press=lambda *args: self.save_new_note(title_input.text.strip(), body_input.text.strip(), popup))
        popup.open()

    def save_new_note(self, title, body, popup):
        if not title or not body:
            self.show_popup("El título o el contenido no pueden estar vacíos.")
            return

        folder_path = os.path.join(BASE_FOLDER, self.current_folder, "notas")
        note_file = os.path.join(folder_path, f"{title}.txt")

        if os.path.exists(note_file):
            self.show_popup("Ya existe una nota con ese título.")
            return

        with open(note_file, "w", encoding="utf-8") as f:
            f.write(body)
        popup.dismiss()
        self.enter_folder(self.current_folder)

    def load_notes(self):
        folder_path = os.path.join(BASE_FOLDER, self.current_folder, "notas")
        notes = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
        for note in notes:
            btn = create_button(note[:-4], size_hint_y=None, font_size=20, bg_color=(0.5, 0.5, 0.8, 1))
            btn.height = 60
            btn.bind(on_press=lambda instance, n=note: self.view_note(n))
            self.folder_content_box.add_widget(btn)

    def view_note(self, note_filename):
        folder_path = os.path.join(BASE_FOLDER, self.current_folder, "notas")
        note_path = os.path.join(folder_path, note_filename)
        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()

        content_box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content_box.add_widget(Label(text=note_filename[:-4], font_size=24, size_hint_y=0.2, color=(0, 0, 0, 1)))
        content_box.add_widget(Label(text=content, font_size=20, color=(0, 0, 0, 1)))

        close_button = create_button("Cerrar", size_hint_y=0.3)
        content_box.add_widget(close_button)

        popup = Popup(title="Nota", content=content_box, size_hint=(0.8, 0.8))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    # Imágenes
    def add_new_image(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        filechooser = FileChooserIconView(path='.', size_hint_y=0.9)
        content.add_widget(filechooser)

        save_button = create_button("Guardar Imagen", size_hint_y=0.1)
        content.add_widget(save_button)

        popup = Popup(title="Seleccionar Imagen", content=content, size_hint=(0.9, 0.9))
        save_button.bind(on_press=lambda *args: self.save_image(filechooser.selection, popup))
        popup.open()

    def save_image(self, selection, popup):
        if not selection:
            self.show_popup("No has seleccionado ningún archivo.")
            return

        src_path = selection[0]
        filename = os.path.basename(src_path)
        dest_path = os.path.join(BASE_FOLDER, self.current_folder, "imagenes", filename)

        if os.path.exists(dest_path):
            self.show_popup("Ya existe una imagen con ese nombre.")
            return

        with open(src_path, 'rb') as src_file, open(dest_path, 'wb') as dest_file:
            dest_file.write(src_file.read())

        popup.dismiss()
        self.enter_folder(self.current_folder)

    def load_images(self):
        folder_path = os.path.join(BASE_FOLDER, self.current_folder, "imagenes")
        images = [f for f in os.listdir(folder_path)]
        for img_file in images:
            img_path = os.path.join(folder_path, img_file)
            try:
                img_widget = Image(source=img_path, size_hint_y=None, height=300)
                self.folder_content_box.add_widget(img_widget)
            except:
                self.show_popup(f"No se pudo cargar la imagen: {img_file}")

    def take_photo(self, instance):
        try:
            filename = f"{int(time.time())}.jpg"
            dest_path = os.path.join(BASE_FOLDER, self.current_folder, "imagenes", filename)
            camera.take_picture(filename=dest_path, on_complete=lambda x: self.enter_folder(self.current_folder))
        except Exception as e:
            self.show_popup(f"Error al abrir la cámara: {str(e)}")

    # Audios
    def record_audio(self, instance):
        duration = 5
        sample_rate = 44100

        self.show_popup("Grabando audio durante 5 segundos...")

        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2)
        sd.wait()

        folder_path = os.path.join(BASE_FOLDER, self.current_folder, "audios")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        filename = f"{int(time.time())}.wav"
        filepath = os.path.join(folder_path, filename)
        write(filepath, sample_rate, recording)

        self.show_popup("Audio guardado exitosamente.")
        self.enter_folder(self.current_folder)

    def load_audios(self):
        folder_path = os.path.join(BASE_FOLDER, self.current_folder, "audios")
        if not os.path.exists(folder_path):
            return

        audios = [f for f in os.listdir(folder_path) if f.endswith(".wav")]
        for audio_file in audios:
            btn = create_button(f"🎧 {audio_file}", size_hint_y=None, height=60, font_size=18, bg_color=(0.8, 0.5, 0.2, 1))
            btn.bind(on_press=lambda instance, af=audio_file: self.play_audio(af))
            self.folder_content_box.add_widget(btn)

    def play_audio(self, audio_filename):
        folder_path = os.path.join(BASE_FOLDER, self.current_folder, "audios")
        filepath = os.path.join(folder_path, audio_filename)
        samplerate, data = wav_read(filepath)
        sd.play(data, samplerate)
        self.show_popup("Reproduciendo...")

    # Popup genérico
    def show_popup(self, message, title='Mensaje'):
        content = BoxLayout(orientation='vertical', padding=20)
        content.add_widget(Label(text=message, font_size=20, color=(0, 0, 0, 1)))
        close_button = create_button("Cerrar", size_hint_y=0.3)
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.3))
        content.add_widget(close_button)
        close_button.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == '__main__':
    VaultApp().run()
