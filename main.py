import os
import json
import tkinter as tk
from tkinter import filedialog
import customtkinter
from PIL import Image, ImageTk, ImageFilter, ImageDraw, ImageEnhance
import vlc
from tinytag import TinyTag
import io
import platform
import random
import time

# --- App Configuration & Theme ---
APP_NAME = "All Player"

# Colors
PRIMARY_COLOR = "#1DB954"
PRIMARY_HOVER_COLOR = "#1ED760"
BG_COLOR = "#121212"
FRAME_COLOR = "#181818"
SIDEBAR_COLOR = "gray10"
TEXT_COLOR = "#FFFFFF"
TEXT_MUTED_COLOR = "#A7A7A7"
ACTIVE_BUTTON_COLOR = "#333333"

# Fonts
MAIN_FONT = ("Segoe UI", 13)
MAIN_FONT_BOLD = ("Segoe UI", 13, "bold")
SMALL_FONT = ("Segoe UI", 11)
LARGE_TITLE_FONT = ("Segoe UI", 32, "bold")
SYMBOL_FONT = ("Segoe UI Symbol", 20)

# Dimensions & Padding
CORNER_RADIUS = 8
GENERAL_PADDING = 10

# Configure CustomTkinter
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

# ----------------------------
# Enhanced VLC Player
# ----------------------------
class VLCPlayer:
    """ A wrapper class for the python-vlc library. """
    def __init__(self):
        try:
            # '--no-xlib' is a common fix for Linux environments
            self.instance = vlc.Instance("--no-xlib")
        except NameError:
            self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        self.video_frame = None
        self.event_manager = self.mediaplayer.event_manager()

    def set_video_frame(self, frame):
        """ Sets the Tkinter frame where the video will be displayed. """
        self.video_frame = frame
        if self.video_frame:
            try:
                if platform.system() == "Windows":
                    self.mediaplayer.set_hwnd(self.video_frame.winfo_id())
                else:
                    self.mediaplayer.set_xwindow(self.video_frame.winfo_id())
            except Exception as e:
                print(f"Error setting video output: {e}")

    def play(self, filepath):
        media = self.instance.media_new(filepath)
        self.mediaplayer.set_media(media)
        if self.video_frame and filepath.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            self.set_video_frame(self.video_frame)
        self.mediaplayer.play()

    def pause(self):
        self.mediaplayer.pause()

    def stop(self):
        self.mediaplayer.stop()

    def is_playing(self):
        return self.mediaplayer.is_playing()

    def get_time(self):
        return self.mediaplayer.get_time()

    def set_time(self, time_ms):
        self.mediaplayer.set_time(time_ms)

    def get_length(self):
        return self.mediaplayer.get_length()

    def get_volume(self):
        return self.mediaplayer.audio_get_volume()

    def set_volume(self, volume):
        return self.mediaplayer.audio_set_volume(volume)
        
    def get_track_metadata(self, filepath):
        """ Extracts metadata from a media file using TinyTag. """
        try:
            return TinyTag.get(filepath, image=True)
        except Exception:
            return None

    def get_album_art_pil(self, tag):
        """ Extracts album art and returns it as a Pillow Image object. """
        try:
            if image_object := tag.images.any:
                image_data = image_object.data
                return Image.open(io.BytesIO(image_data))
        except Exception:
            return None

# ----------------------------
# Modern Progress Bar
# ----------------------------
class ModernProgressBar(customtkinter.CTkProgressBar):
    """ A custom progress bar that enlarges on hover and allows seeking. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(
            height=6,
            corner_radius=3,
            fg_color="gray25",
            progress_color=PRIMARY_COLOR
        )
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.seek_callback = None

    def on_hover(self, event):
        self.configure(height=10)

    def on_leave(self, event):
        self.configure(height=6)

    def on_click(self, event):
        if self.seek_callback:
            percentage = event.x / self.winfo_width()
            self.seek_callback(percentage)

    def set_seek_callback(self, callback):
        self.seek_callback = callback

# ----------------------------
# Modern Media Card
# ----------------------------
class MediaCard(customtkinter.CTkFrame):
    """ A clickable card to display a single media item in the library list. """
    def __init__(self, parent, filepath, thumbnail, title, subtitle, click_callback, **kwargs):
        super().__init__(parent, **kwargs)
        self.filepath = filepath
        self.click_callback = click_callback
        self.configure(fg_color="transparent", corner_radius=12)
        
        self.container = customtkinter.CTkFrame(self, fg_color="gray15", corner_radius=CORNER_RADIUS)
        self.container.pack(fill="both", expand=True, padx=4, pady=4)
        
        thumb_size = 60
        self.thumbnail_frame = customtkinter.CTkFrame(self.container, fg_color="gray10", width=thumb_size, height=thumb_size, corner_radius=6)
        self.thumbnail_frame.pack_propagate(False)
        self.thumbnail_frame.pack(side="left", padx=(8, 12), pady=8)
        
        if thumbnail:
            self.thumbnail_label = customtkinter.CTkLabel(self.thumbnail_frame, image=thumbnail, text="")
            self.thumbnail_label.pack(expand=True)
        
        self.text_frame = customtkinter.CTkFrame(self.container, fg_color="transparent")
        self.text_frame.pack(side="left", fill="both", expand=True, pady=8)
        
        self.title_label = customtkinter.CTkLabel(self.text_frame, text=title, font=MAIN_FONT_BOLD, anchor="w", justify="left")
        self.title_label.pack(fill="x", pady=(0, 2))
        
        if subtitle:
            self.subtitle_label = customtkinter.CTkLabel(self.text_frame, text=subtitle, font=SMALL_FONT, text_color=TEXT_MUTED_COLOR, anchor="w")
            self.subtitle_label.pack(fill="x")
        
        self.play_indicator = customtkinter.CTkLabel(self.container, text="▶", font=("Segoe UI", 20), text_color=PRIMARY_COLOR)
        
        self.bind_events()
    
    def bind_events(self):
        """ Binds hover and click events to all widgets in the card for a seamless experience. """
        widgets = [self, self.container, self.thumbnail_frame, self.text_frame, self.title_label]
        if hasattr(self, 'subtitle_label'): widgets.append(self.subtitle_label)
        if hasattr(self, 'thumbnail_label'): widgets.append(self.thumbnail_label)
        for widget in widgets:
            widget.bind("<Enter>", self.on_hover)
            widget.bind("<Leave>", self.on_leave)
            widget.bind("<Button-1>", self.on_click)
    
    def on_hover(self, event): self.container.configure(fg_color="gray20")
    def on_leave(self, event): self.container.configure(fg_color="gray15")
    def on_click(self, event): self.click_callback(self.filepath)
    
    def set_selected(self, selected):
        """ Visually indicates if the card is the currently playing item. """
        if selected:
            self.configure(fg_color=PRIMARY_COLOR)
            self.play_indicator.pack(side="right", padx=(0, 15))
        else:
            self.configure(fg_color="transparent")
            self.play_indicator.pack_forget()

# ----------------------------
# Media Tab
# ----------------------------
class MediaTab:
    """ Manages a single tab in the UI, including its library, file list, and search. """
    def __init__(self, main_app, tab_name, file_types, media_type):
        self.main_app = main_app
        self.library_file = f"{tab_name.lower()}_library.json"
        self.library_data = []
        self.file_types = file_types
        self.media_type = media_type
        self.current_selection = None
        self.cards = {}
        self.empty_label_container = None 
        self.tab = main_app.tab_view.add(tab_name)
        self.setup_ui()
        self.load_library()
    
    def setup_ui(self):
        self.container = customtkinter.CTkFrame(self.tab, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=GENERAL_PADDING, pady=GENERAL_PADDING)
        
        search_frame = customtkinter.CTkFrame(self.container, fg_color="gray15", corner_radius=10, height=40)
        search_frame.pack(fill="x", pady=(0, 10))
        search_frame.pack_propagate(False)
        customtkinter.CTkLabel(search_frame, text="🔍", font=("Segoe UI", 14)).pack(side="left", padx=(10, 5))
        self.search_entry = customtkinter.CTkEntry(search_frame, placeholder_text=f"Search {self.media_type}...", border_width=0, fg_color="transparent")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.filter_media)
        
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.container, fg_color="transparent", scrollbar_button_color="gray25", scrollbar_button_hover_color="gray35")
        self.scrollable_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        button_frame = customtkinter.CTkFrame(self.container, fg_color="transparent")
        button_frame.pack(fill="x")
        button_frame.grid_columnconfigure((0,1), weight=1)

        customtkinter.CTkButton(button_frame, text="Add Files", height=40, fg_color=PRIMARY_COLOR, hover_color=PRIMARY_HOVER_COLOR, corner_radius=CORNER_RADIUS, font=("Segoe UI", 12, "bold"), command=self.add_files).grid(row=0, column=0, sticky="ew", padx=(0,5))
        customtkinter.CTkButton(button_frame, text="Remove", height=40, fg_color="#b91d1d", hover_color="#d62626", corner_radius=CORNER_RADIUS, font=("Segoe UI", 12, "bold"), command=self.remove_selected).grid(row=0, column=1, sticky="ew", padx=(5,0))
    
    def filter_media(self, event):
        search_term = self.search_entry.get().lower()
        for filepath, card in self.cards.items():
            title_text = card.title_label.cget("text").lower()
            subtitle_text = card.subtitle_label.cget("text").lower() if hasattr(card, 'subtitle_label') else ""
            
            if search_term in title_text or search_term in subtitle_text:
                card.pack(fill="x", pady=2)
            else:
                card.pack_forget()

    def on_item_click(self, filepath):
        if self.current_selection and self.current_selection in self.cards:
            self.cards[self.current_selection].set_selected(False)
        self.current_selection = filepath
        if filepath in self.cards:
            self.cards[filepath].set_selected(True)
        self.main_app.play_media(filepath, self)
    
    def load_library(self):
        if os.path.exists(self.library_file):
            try:
                with open(self.library_file, "r", encoding="utf-8") as f: self.library_data = json.load(f)
            except json.JSONDecodeError: 
                self.library_data = []
        self.refresh_media_list()
    
    def save_library(self):
        try:
            with open(self.library_file, "w", encoding="utf-8") as f: json.dump(self.library_data, f, indent=4)
        except IOError: 
            pass

    def show_empty_message(self):
        """ Displays a visually appealing message when the library is empty. """
        if self.empty_label_container:
            self.empty_label_container.destroy()

        self.empty_label_container = customtkinter.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.empty_label_container.place(relx=0.5, rely=0.4, anchor="center")

        icon = "🎵" if self.media_type == "Music" else "🎬" if self.media_type == "Videos" else "🖼️"
        icon_label = customtkinter.CTkLabel(self.empty_label_container, text=icon, font=("Segoe UI", 60), text_color=TEXT_MUTED_COLOR)
        icon_label.pack()
        
        text_label = customtkinter.CTkLabel(
            self.empty_label_container, 
            text=f"Your {self.media_type} library is empty.\nClick 'Add Files' to get started.",
            font=MAIN_FONT,
            text_color=TEXT_MUTED_COLOR,
            justify="center"
        )
        text_label.pack(pady=(10, 0))

    def refresh_media_list(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.cards.clear()
        self.empty_label_container = None

        if not self.library_data:
            self.show_empty_message()
        else:
            for filepath in self.library_data: self.create_media_card(filepath)

    def create_video_icon(self, size):
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        width, height = size
        triangle = [(width * 0.35, height * 0.25), (width * 0.35, height * 0.75), (width * 0.75, height * 0.5)]
        draw.polygon(triangle, fill="white")
        return image

    def create_media_card(self, filepath):
        filename = os.path.basename(filepath)
        title, _ = os.path.splitext(filename)
        subtitle, thumbnail = None, None
        
        if self.media_type == "Pictures":
            try:
                img = Image.open(filepath)
                img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                thumbnail = customtkinter.CTkImage(light_image=img, dark_image=img, size=(60, 60))
                subtitle = f"{img.width}x{img.height}"
            except Exception: pass
        elif self.media_type == "Music":
            tag = self.main_app.player.get_track_metadata(filepath)
            if tag:
                title = tag.title or title
                subtitle = tag.artist or "Unknown Artist"
                if album_art := self.main_app.player.get_album_art_pil(tag):
                    album_art.thumbnail((60, 60), Image.Resampling.LANCZOS)
                    thumbnail = customtkinter.CTkImage(light_image=album_art, dark_image=album_art, size=(60, 60))
        elif self.media_type == "Videos":
            try:
                icon_image = self.create_video_icon((60, 60))
                thumbnail = customtkinter.CTkImage(light_image=icon_image, dark_image=icon_image, size=(60, 60))
                size = os.path.getsize(filepath)
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        subtitle = f"{size:.1f} {unit}"; break
                    size /= 1024.0
            except Exception: pass
        
        card = MediaCard(self.scrollable_frame, filepath, thumbnail, title, subtitle, self.on_item_click)
        card.pack(fill="x", pady=2)
        self.cards[filepath] = card
    
    def add_files(self):
        if filepaths := filedialog.askopenfilenames(title="Select Files", filetypes=self.file_types):
            new_files = [fp for fp in filepaths if fp not in self.library_data]
            if new_files:
                if self.empty_label_container:
                    self.empty_label_container.destroy()
                    self.empty_label_container = None
                self.library_data.extend(new_files)
                self.save_library()
                for filepath in new_files: self.create_media_card(filepath)
    
    def remove_selected(self):
        if self.current_selection and self.current_selection in self.library_data:
            self.library_data.remove(self.current_selection)
            self.save_library()
            if self.current_selection in self.cards:
                self.cards[self.current_selection].destroy()
                del self.cards[self.current_selection]
            self.current_selection = None
            if not self.library_data:
                self.show_empty_message()

# ----------------------------
# Main Application
# ----------------------------
class ModernMediaPlayer(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1400x850")
        self.minsize(1200, 700)
        
        self.player = VLCPlayer()
        self.current_media_filepath = None
        self.current_media_tab = None
        self.current_album_art = None
        self.is_muted = False
        self.welcome_frame = None
        self.is_shuffle, self.repeat_mode = False, 0
        
        # --- FIX: ATTACH EVENT HANDLER ONLY ONCE ---
        # This tells the player to call self.handle_media_end whenever a track finishes.
        # By doing this here, we ensure it's only set up one time.
        self.player.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.handle_media_end)

        self.setup_main_layout()
        self.create_sidebar()
        self.create_main_panel()
        self.create_controls()
        self.update_progress()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.display_container.bind("<Configure>", self.on_resize)
    
    def setup_main_layout(self):
        self.configure(fg_color=BG_COLOR)
        self.main_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=GENERAL_PADDING, pady=GENERAL_PADDING)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)
    
    def create_sidebar(self):
        self.sidebar = customtkinter.CTkFrame(self.main_container, width=380, fg_color=SIDEBAR_COLOR, corner_radius=15, border_width=1, border_color="gray15")
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, GENERAL_PADDING))
        self.sidebar.grid_propagate(False)
        
        title_frame = customtkinter.CTkFrame(self.sidebar, fg_color="transparent", height=80)
        title_frame.pack(fill="x", padx=25, pady=20)
        title_frame.pack_propagate(False)
        customtkinter.CTkLabel(title_frame, text="All", font=LARGE_TITLE_FONT, text_color=PRIMARY_COLOR).pack(side="left")
        customtkinter.CTkLabel(title_frame, text="Player", font=("Segoe UI", 32, "normal"), text_color=TEXT_COLOR).pack(side="left", padx=(8, 0))
        
        self.tab_view = customtkinter.CTkTabview(self.sidebar, fg_color="transparent", 
                                                 segmented_button_fg_color="gray20",
                                                 segmented_button_selected_color=PRIMARY_COLOR,
                                                 segmented_button_unselected_color="gray15",
                                                 segmented_button_selected_hover_color=PRIMARY_HOVER_COLOR,
                                                 corner_radius=10)
        self.tab_view.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.music_tab = MediaTab(self, "Music", [("Audio Files", "*.mp3 *.wav *.flac *.m4a *.ogg")], "Music")
        self.video_tab = MediaTab(self, "Videos", [("Video Files", "*.mp4 *.mkv *.avi *.mov *.webm")], "Videos")
        self.picture_tab = MediaTab(self, "Pictures", [("Image Files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")], "Pictures")
    
    def create_main_panel(self):
        self.content_area = customtkinter.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(1, weight=0)
        self.content_area.grid_columnconfigure(0, weight=1)
        self.display_container = customtkinter.CTkFrame(self.content_area, fg_color=SIDEBAR_COLOR, corner_radius=15, border_width=1, border_color="gray15")
        self.display_container.grid(row=0, column=0, sticky="nsew")
        
        self.image_label = customtkinter.CTkLabel(self.display_container, text="", fg_color="transparent")
        self.video_frame = customtkinter.CTkFrame(self.display_container, fg_color="#000000")
        self.show_welcome_screen()

    # --- UI Creation Refactored ---
    def create_controls(self):
        base_controls_frame = customtkinter.CTkFrame(self.content_area, fg_color="transparent")
        base_controls_frame.grid(row=1, column=0, sticky="ew", pady=(GENERAL_PADDING, 0))

        self.controls_container = customtkinter.CTkFrame(base_controls_frame, fg_color=SIDEBAR_COLOR, corner_radius=15, height=100, border_width=1, border_color="gray15")
        self._create_now_playing_ui(self.controls_container)
        self._create_center_controls_ui(self.controls_container)
        self._create_volume_ui(self.controls_container)
        
        self.image_controls_container = customtkinter.CTkFrame(base_controls_frame, fg_color=SIDEBAR_COLOR, corner_radius=15, height=100, border_width=1, border_color="gray15")
        self._create_image_controls_ui(self.image_controls_container)

    def _create_now_playing_ui(self, parent):
        container = customtkinter.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=20, pady=10, fill="y")
        self.now_playing_art_label = customtkinter.CTkLabel(container, text="", width=60, height=60, fg_color="gray15", corner_radius=6)
        self.now_playing_art_label.pack(side="left", padx=(0, 15))
        
        text_frame = customtkinter.CTkFrame(container, fg_color="transparent")
        text_frame.pack(side="left", fill="y", expand=True)
        self.now_playing_title = customtkinter.CTkLabel(text_frame, text="Not Playing", font=MAIN_FONT_BOLD, anchor="sw")
        self.now_playing_title.pack(fill="x", expand=True)
        self.now_playing_artist = customtkinter.CTkLabel(text_frame, text=" ", font=SMALL_FONT, text_color=TEXT_MUTED_COLOR, anchor="nw")
        self.now_playing_artist.pack(fill="x", expand=True)

    def _create_center_controls_ui(self, parent):
        central_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        central_frame.pack(side="left", fill="both", expand=True, padx=20)
        
        progress_frame = customtkinter.CTkFrame(central_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=20, pady=(10, 5))
        self.time_label = customtkinter.CTkLabel(progress_frame, text="00:00", font=SMALL_FONT, text_color=TEXT_MUTED_COLOR)
        self.time_label.pack(side="left", padx=(0, 10))
        
        self.progress_bar = ModernProgressBar(progress_frame)
        self.progress_bar.set_seek_callback(self.seek)
        self.progress_bar.pack(side="left", fill="x", expand=True)
        self.progress_bar.set(0)

        self.duration_label = customtkinter.CTkLabel(progress_frame, text="00:00", font=SMALL_FONT, text_color=TEXT_MUTED_COLOR)
        self.duration_label.pack(side="left", padx=(10, 0))
        
        buttons_frame = customtkinter.CTkFrame(central_frame, fg_color="transparent")
        buttons_frame.pack(expand=True)
        btn_style = {"fg_color": "transparent", "hover_color": "gray20", "font": SYMBOL_FONT, "text_color": TEXT_COLOR}
        self.shuffle_btn = customtkinter.CTkButton(buttons_frame, text="🔀", width=40, height=40, corner_radius=20, command=self.toggle_shuffle, **btn_style)
        self.shuffle_btn.pack(side="left", padx=5)
        self.prev_btn = customtkinter.CTkButton(buttons_frame, text="⏮", width=50, height=50, corner_radius=25, command=self.play_previous, **btn_style)
        self.prev_btn.pack(side="left", padx=5)
        self.play_pause_btn = customtkinter.CTkButton(buttons_frame, text="▶", width=50, height=50, corner_radius=25, fg_color=PRIMARY_COLOR, hover_color=PRIMARY_HOVER_COLOR, font=("Segoe UI Symbol", 24), command=self.toggle_play_pause)
        self.play_pause_btn.pack(side="left", padx=10)
        self.next_btn = customtkinter.CTkButton(buttons_frame, text="⏭", width=50, height=50, corner_radius=25, command=self.play_next, **btn_style)
        self.next_btn.pack(side="left", padx=5)
        self.repeat_btn = customtkinter.CTkButton(buttons_frame, text="🔁", width=40, height=40, corner_radius=20, command=self.toggle_repeat, **btn_style)
        self.repeat_btn.pack(side="left", padx=5)

    def _create_volume_ui(self, parent):
        volume_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        volume_frame.pack(side="right", padx=20, fill="y", pady=10)
        
        btn_style = {"fg_color": "transparent", "hover_color": "gray20", "font": SYMBOL_FONT, "text_color": TEXT_COLOR}
        self.volume_btn = customtkinter.CTkButton(volume_frame, text="🔊", command=self.toggle_mute, width=30, **btn_style)
        self.volume_btn.pack(side="left", padx=(0, 10))
        self.volume_slider = customtkinter.CTkSlider(volume_frame, from_=0, to=100, width=120, command=self.set_volume, button_color=PRIMARY_COLOR, button_hover_color=PRIMARY_HOVER_COLOR, progress_color=PRIMARY_COLOR)
        self.volume_slider.pack(side="left", expand=True)
        self.volume_slider.set(70)
        
    def _create_image_controls_ui(self, parent):
        image_buttons_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        image_buttons_frame.pack(expand=True)
        btn_style = {"width": 150, "height": 50, "fg_color": "gray20", "hover_color": "gray25", "corner_radius": CORNER_RADIUS}
        customtkinter.CTkButton(image_buttons_frame, text="⏮ Previous", command=self.play_previous_image, **btn_style).pack(side="left", padx=20)
        customtkinter.CTkButton(image_buttons_frame, text="Next ⏭", command=self.play_next_image, **btn_style).pack(side="left", padx=20)

    # --- Core App Logic ---
    def show_welcome_screen(self):
        self.welcome_frame = customtkinter.CTkFrame(self.display_container, fg_color="transparent")
        self.welcome_frame.place(relx=0.5, rely=0.5, anchor="center")
        customtkinter.CTkLabel(self.welcome_frame, text=f"Welcome to {APP_NAME}", font=("Segoe UI", 48, "bold"), text_color=PRIMARY_COLOR).pack(pady=(0, 10))
        customtkinter.CTkLabel(self.welcome_frame, text="Your Modern Media Experience", font=("Segoe UI", 18), text_color=TEXT_MUTED_COLOR).pack()

    def clear_display_area(self):
        self.video_frame.pack_forget()
        self.image_label.pack_forget()
        self.image_label.configure(image=None)
        self.controls_container.pack_forget()
        self.image_controls_container.pack_forget()
        self.set_now_playing_text("Not Playing", "")
        self.now_playing_art_label.configure(image=None)
        self.current_album_art = None

    def play_media(self, filepath, tab_instance):
        if self.welcome_frame:
            self.welcome_frame.destroy()
            self.welcome_frame = None
        self.player.stop()
        self.clear_display_area()
        self.current_media_filepath = filepath
        self.current_media_tab = tab_instance
        
        # --- FIX: REMOVED THE REPEATED EVENT ATTACHMENT FROM HERE ---

        if tab_instance.media_type == "Pictures":
            self.display_picture(filepath)
            self.image_controls_container.pack(fill="both", expand=True)
        elif tab_instance.media_type in ["Music", "Videos"]:
            self.controls_container.pack(fill="both", expand=True)
            if tab_instance.media_type == "Music": self.display_music(filepath)
            else: self.display_video(filepath)
            self.player.play(filepath)
            self.play_pause_btn.configure(text="⏸")
        
        self.progress_bar.set(0)
    
    def display_picture(self, filepath):
        try:
            pil_image = Image.open(filepath)
            self.update_idletasks()
            dw, dh = self.display_container.winfo_width(), self.display_container.winfo_height()
            iw, ih = pil_image.size
            if iw > dw or ih > dh:
                ratio = min(dw / iw, dh / ih)
                new_size = (int(iw * ratio), int(ih * ratio))
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            
            ctk_image = customtkinter.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
            self.image_label.configure(image=ctk_image)
            self.image_label.pack(fill="both", expand=True)
        except Exception as e:
            self.image_label.configure(image=None, text=f"Error displaying image: {e}")
            self.image_label.pack(fill="both", expand=True)
    
    def display_music(self, filepath):
        tag = self.player.get_track_metadata(filepath)
        title = os.path.basename(filepath)
        artist = "Unknown Artist"
        if tag:
            title = tag.title or title
            artist = tag.artist or artist
        
        self.set_now_playing_text(title, artist)
        
        self.current_album_art = self.player.get_album_art_pil(tag)
        if self.current_album_art:
            thumb_img = self.current_album_art.copy()
            thumb_img.thumbnail((60, 60), Image.Resampling.LANCZOS)
            ctk_thumb = customtkinter.CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(60, 60))
            self.now_playing_art_label.configure(image=ctk_thumb)

            self.create_music_backdrop(self.current_album_art)
            self.image_label.pack(fill="both", expand=True)
    
    def create_music_backdrop(self, album_art):
        self.update_idletasks()
        dw, dh = self.display_container.winfo_width(), self.display_container.winfo_height()
        if dw < 100 or dh < 100: return
        
        bg = album_art.copy().resize((dw, dh), Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        bg = ImageEnhance.Brightness(bg).enhance(0.5)
        
        art_size = int(min(dw, dh) * 0.5)
        album_art_resized = album_art.copy()
        album_art_resized.thumbnail((art_size, art_size), Image.Resampling.LANCZOS)
        
        mask = Image.new('L', album_art_resized.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0) + album_art_resized.size, radius=20, fill=255)
        
        bg.paste(album_art_resized, ((dw - album_art_resized.width) // 2, (dh - album_art_resized.height) // 2), mask)
        
        ctk_image = customtkinter.CTkImage(light_image=bg, dark_image=bg, size=(dw, dh))
        self.image_label.configure(image=ctk_image)
    
    def display_video(self, filepath):
        self.video_frame.pack(fill="both", expand=True)
        self.player.set_video_frame(self.video_frame)

    def set_now_playing_text(self, title, artist):
        """ Sets the now playing text, truncating if it's too long. """
        max_len = 40
        if len(title) > max_len:
            title = title[:max_len] + "..."
        if len(artist) > max_len:
            artist = artist[:max_len] + "..."
        self.now_playing_title.configure(text=title)
        self.now_playing_artist.configure(text=artist)
    
    def toggle_play_pause(self):
        if self.current_media_filepath and self.current_media_tab.media_type != "Pictures":
            if self.player.is_playing():
                self.player.pause()
                self.play_pause_btn.configure(text="▶")
            else:
                self.player.mediaplayer.play()
                self.play_pause_btn.configure(text="⏸")
    
    def play_next(self): self._play_adjacent_media(1, self.current_media_tab)
    def play_previous(self): self._play_adjacent_media(-1, self.current_media_tab)
    def play_next_image(self): self._play_adjacent_media(1, self.picture_tab)
    def play_previous_image(self): self._play_adjacent_media(-1, self.picture_tab)

    def _play_adjacent_media(self, direction, media_tab):
        if not (media_tab and self.current_media_filepath and media_tab.library_data): return
        try:
            data = media_tab.library_data
            if not data: return
            current_index = data.index(self.current_media_filepath)
            
            if self.is_shuffle and media_tab.media_type != "Pictures" and len(data) > 1:
                next_index = random.choice([i for i in range(len(data)) if i != current_index])
            else:
                next_index = (current_index + direction) % len(data)
            
            media_tab.on_item_click(data[next_index])
        except (ValueError, IndexError): 
            pass

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        color = PRIMARY_COLOR if self.is_shuffle else TEXT_COLOR
        fg = ACTIVE_BUTTON_COLOR if self.is_shuffle else "transparent"
        self.shuffle_btn.configure(text_color=color, fg_color=fg)
    
    def toggle_repeat(self):
        self.repeat_mode = (self.repeat_mode + 1) % 3
        if self.repeat_mode == 0: # Off
            self.repeat_btn.configure(text="🔁", text_color=TEXT_COLOR, fg_color="transparent")
        elif self.repeat_mode == 1: # Repeat All
            self.repeat_btn.configure(text="🔁", text_color=PRIMARY_COLOR, fg_color=ACTIVE_BUTTON_COLOR)
        else: # Repeat One
            self.repeat_btn.configure(text="🔂", text_color=PRIMARY_COLOR, fg_color=ACTIVE_BUTTON_COLOR)

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.player.set_volume(0)
            self.volume_btn.configure(text="🔇")
        else:
            self.player.set_volume(int(self.volume_slider.get()))
            self.volume_btn.configure(text="🔊")

    def set_volume(self, value): 
        volume = int(value)
        self.player.set_volume(volume)
        if self.is_muted and volume > 0:
            self.is_muted = False
            self.volume_btn.configure(text="🔊")
        elif not self.is_muted and volume == 0:
             self.is_muted = True
             self.volume_btn.configure(text="🔇")

    def seek(self, value):
        if self.player.get_length() > 0:
            self.player.set_time(int(self.player.get_length() * value))
    
    def update_progress(self):
        if self.player.is_playing():
            total_duration = self.player.get_length()
            if total_duration > 0:
                current_time = self.player.get_time()
                self.progress_bar.set(current_time / total_duration)
                self.time_label.configure(text=self.format_time(current_time))
                self.duration_label.configure(text=self.format_time(total_duration))
        self.after(250, self.update_progress)

    def handle_media_end(self, event):
        """ Called by the VLC event manager when a track finishes. """
        if self.repeat_mode == 2: # Repeat One
            self.after(100, lambda: self.play_media(self.current_media_filepath, self.current_media_tab))
        elif self.repeat_mode == 1: # Repeat All
            self.after(100, self.play_next)
        else: # No repeat
            try:
                data = self.current_media_tab.library_data
                current_index = data.index(self.current_media_filepath)
                if current_index < len(data) - 1:
                    self.after(100, self.play_next)
                else: 
                    # Last song finished, reset UI
                    self.play_pause_btn.configure(text="▶")
                    self.progress_bar.set(0)
                    self.time_label.configure(text="00:00")
            except (ValueError, AttributeError, IndexError):
                pass
                
    def on_resize(self, event):
        """ Redraws the blurred background when the window is resized. """
        if self.current_media_tab and self.current_media_tab.media_type == "Music" and self.current_album_art:
            self.create_music_backdrop(self.current_album_art)

    def format_time(self, ms):
        seconds = int(ms / 1000)
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
    
    def on_closing(self):
        self.player.stop()
        self.destroy()

if __name__ == "__main__":
    app = ModernMediaPlayer()
    app.mainloop()