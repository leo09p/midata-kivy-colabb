import os
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.core.audio import SoundLoader
from kivy.uix.image import Image
import shutil

PASSWORD = "1234"

class SecureApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical')
        self.login_screen()
        return self.root

    def login_screen(self):
        self.root.clear_widgets()
        self.password_input = TextInput(password=True, multiline=False, hint_text="Enter Password")
        login_button = Button(text="Login", on_press=self.check_password)
        self.root.add_widget(Label(text="MidatA"))
        self.root.add_widget(self.password_input)
        self.root.add_widget(login_button)

    def check_password(self, instance):
        if self.password_input.text == PASSWORD:
            self.folder_screen()
        else:
            self.password_input.text = ''
            self.root.add_widget(Label(text="Incorrect password!", color=(1,0,0,1)))

    def folder_screen(self):
        self.root.clear_widgets()
        create_btn = Button(text="Create Folder", on_press=self.create_folder_popup)
        open_btn = Button(text="Open Folder", on_press=self.open_folder_popup)
        self.root.add_widget(create_btn)
        self.root.add_widget(open_btn)

    def create_folder_popup(self, instance):
        content = BoxLayout(orientation='vertical')
        folder_name_input = TextInput(hint_text="Folder Name")
        create_btn = Button(text="Create", on_press=lambda x: self.create_folder(folder_name_input.text))
        content.add_widget(folder_name_input)
        content.add_widget(create_btn)
        self.popup = Popup(title="Create Folder", content=content, size_hint=(0.8, 0.5))
        self.popup.open()

    def create_folder(self, name):
        os.makedirs(name, exist_ok=True)
        self.popup.dismiss()

    def open_folder_popup(self, instance):
        content = FileChooserIconView()
        content.path = "."
        open_btn = Button(text="Select", size_hint_y=0.1, on_press=lambda x: self.open_folder(content.path, content.selection))
        box = BoxLayout(orientation='vertical')
        box.add_widget(content)
        box.add_widget(open_btn)
        self.popup = Popup(title="Open Folder", content=box, size_hint=(0.9, 0.9))
        self.popup.open()

    def open_folder(self, path, selection):
        self.popup.dismiss()
        if selection:
            self.folder_options(selection[0])

    def folder_options(self, folder_path):
        self.root.clear_widgets()
        img_btn = Button(text="Add Image", on_press=lambda x: self.add_image(folder_path))
        audio_btn = Button(text="Add Audio", on_press=lambda x: self.add_audio(folder_path))
        back_btn = Button(text="Back", on_press=lambda x: self.folder_screen())
        self.root.add_widget(Label(text=f"Folder: {os.path.basename(folder_path)}"))
        self.root.add_widget(img_btn)
        self.root.add_widget(audio_btn)
        self.root.add_widget(back_btn)

    def add_image(self, folder_path):
        content = FileChooserIconView(filters=["*.png", "*.jpg", "*.jpeg"])
        content.path = "."
        select_btn = Button(text="Select Image", size_hint_y=0.1,
                             on_press=lambda x: self.save_image(content.selection, folder_path))
        box = BoxLayout(orientation='vertical')
        box.add_widget(content)
        box.add_widget(select_btn)
        self.popup = Popup(title="Select Image", content=box, size_hint=(0.9, 0.9))
        self.popup.open()

    def save_image(self, selection, folder_path):
        if selection:
            shutil.copy(selection[0], folder_path)
        self.popup.dismiss()

    def add_audio(self, folder_path):
        content = FileChooserIconView(filters=["*.wav", "*.mp3", "*.ogg"])
        content.path = "."
        select_btn = Button(text="Select Audio", size_hint_y=0.1,
                             on_press=lambda x: self.save_audio(content.selection, folder_path))
        box = BoxLayout(orientation='vertical')
        box.add_widget(content)
        box.add_widget(select_btn)
        self.popup = Popup(title="Select Audio", content=box, size_hint=(0.9, 0.9))
        self.popup.open()

    def save_audio(self, selection, folder_path):
        if selection:
            shutil.copy(selection[0], folder_path)
        self.popup.dismiss()

if __name__ == '__main__':
    SecureApp().run()
