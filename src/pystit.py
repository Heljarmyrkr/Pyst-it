# Pyst-it - Copyright (c) 2024 Kauã Rodrigues Dada
# Licensed under the Custom License
# You may not sell or redistribute the software for commercial purposes.
# You must include attribution when modifying the software.

import customtkinter as ctk
from tkinter import PhotoImage, messagebox, filedialog
from typing import List, Optional, Dict
from dataclasses import dataclass
import random
import json
import sys
import os
import colorsys


@dataclass
class StickyNoteConfig:
    width: int = 240
    height: int = 280
    max_chars: int = 18
    font_name: str = "Sticky Notes"
    font_size: int = 40
    alpha: float = 0.99
    colors: List[str] = None

    def __post_init__(self):
        if self.colors is None:
            self.colors = [
                "#FF6FAD",
                "#E9806A",
                "#F89C1D",
                "#C7EC51",
                "#8BC6C4",
                "#2FC8F2",
                "#6C3499",
                "#FCFF9C",
            ]


class StickyNote(ctk.CTkFrame):
    def __init__(
            self,
            parent,
            config: StickyNoteConfig,
            color: str,
            images: Dict[str, PhotoImage],
            is_rgb: bool = False
    ):
        super().__init__(
            parent,
            width=config.width,
            height=config.height,
            fg_color=color,
            corner_radius=0,
        )

        self.parent = parent
        self.config = config
        self.images = images
        self.text_areas = []
        self.is_rgb = is_rgb
        self.rgb_color_timer = None
        self.drawing_canvas = None

        self._create_toolbar()
        self._setup_text_areas()
        self._setup_lines()

        if self.is_rgb:
            self._start_rgb_color_cycle()

    def _create_toolbar(self):
        self.toolbar = ctk.CTkFrame(
            self,
            width=self.config.width,
            height=20,
            corner_radius=0,
            fg_color="#070707",
        )
        self.toolbar.place(x=0, y=0)

        buttons = [
            ("new", "New note", self._open_new_window),
            ("save", "Save", self._save_note),
            ("open", "Open", self._open_file),
            ("notify", "Notify", self._notify),
            ("draw", "Draw", self._open_drawing_note),
            ("options", "Options", self._show_options),
        ]

        for i, (image_key, tooltip, command) in enumerate(buttons):
            x_pos = 0 if image_key != "options" else 220
            if image_key != "options":
                x_pos = i * 22

            button = ctk.CTkButton(
                self.toolbar,
                image=self.images[image_key],
                text="",
                width=20 if image_key != "options" else 5,
                height=20,
                corner_radius=0,
                fg_color="#070707",
                hover_color="#262626",
                command=command,
            )
            button.place(x=x_pos, y=-1)

    def _setup_text_areas(self):
        font = (self.config.font_name, self.config.font_size)

        for i in range(6):
            text_area = ctk.CTkEntry(
                self,
                width=230,
                height=30,
                fg_color=self.cget("fg_color"),
                font=font,
                text_color="black",
                border_width=0,
            )
            text_area.place(x=5, y=30 + (i * 40))
            text_area.configure(state="normal")

            text_area.bind("<KeyRelease>", self._limit_text)
            text_area.bind("<MouseWheel>", self._prevent_scroll)

            self.text_areas.append(text_area)

    def _setup_lines(self):
        for i in range(6):
            line = ctk.CTkFrame(
                self, fg_color="#1A1C1E", corner_radius=0, width=202, height=2
            )
            line.place(x=20, y=65 + (i * 40))

    def _start_rgb_color_cycle(self):
        def change_color():
            hue = (random.random() * 360) / 360.0
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1, 1)]
            new_color = f'#{r:02x}{g:02x}{b:02x}'

            self.configure(fg_color=new_color)
            for area in self.text_areas:
                area.configure(fg_color=new_color)

            self.rgb_color_timer = self.after(500, change_color)

        change_color()

    def _open_drawing_note(self):
        drawing_note = DrawingNoteWindow(self)
        drawing_note.mainloop()

    def _limit_text(self, event):
        current_text = event.widget.get()
        if len(current_text) > self.config.max_chars:
            event.widget.delete(self.config.max_chars, "end")

    def _prevent_scroll(self, event):
        return "break"

    def get_content(self) -> List[str]:
        return [area.get() for area in self.text_areas]

    def set_content(self, lines: List[str]):
        for area, line in zip(self.text_areas, lines + [""] * len(self.text_areas)):
            area.delete(0, "end")
            area.insert(0, line.strip())

    def _save_note(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("JSON Files", "*.json"), ],
        )
        if file_path:
            content = self.get_content()

            if file_path.endswith(".json"):
                with open(file_path, "w") as file:
                    json.dump({"content": content}, file)
            else:
                with open(file_path, "w") as file:
                    file.write("\n".join(content))

            if isinstance(self.parent, App):
                self.parent._auto_save()
            messagebox.showinfo("Success", "Your notes have been saved successfully!")

    def _open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("JSON Files", "*.json")]
        )
        if file_path:
            try:
                if file_path.endswith(".json"):
                    with open(file_path, "r") as file:
                        data = json.load(file)
                        content = data.get("content", [])
                else:
                    with open(file_path, "r") as file:
                        content = file.read().splitlines()

                self.set_content(content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def _open_new_window(self):
        is_rare_rgb = random.random() < 0.01
        new_window = ctk.CTkToplevel(self)
        new_window.title("Pyst-it")
        new_window.geometry(f"{self.config.width}x{self.config.height}")
        new_window.resizable(False, False)
        new_window.attributes("-alpha", self.config.alpha)
        new_window.attributes("-topmost", 1)
        new_window.after(
            250, lambda: new_window.iconbitmap(App.get_resource_path("iconicon.ico"))
        )

        if is_rare_rgb:
            color = "#000000"
            new_note = StickyNote(new_window, self.config, color, self.images, is_rgb=True)
            messagebox.showinfo("Rare Note!", "You've discovered a rare RGB Sticky Note!")
        else:
            color = random.choice(self.config.colors)
            new_note = StickyNote(new_window, self.config, color, self.images)

        new_note.pack(fill="both", expand=True)

    def _notify(self):
        pass

    def _show_options(self):
        messagebox.showinfo(
            "About",
            "Thank you for using Pyst-it!\n\n"
            "A simple and elegant sticky notes application for your desktop.\n"
            "Features:\n"
            "- Multiple notes\n"
            "- Auto-save\n"
            "- TXT/JSON file support\n"
            "\n"
            "-Heljarmyrkr",
        )

class DrawingNoteWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Pyst-it ✏️")
        self.geometry("240x280")
        self.resizable(False, False)
        self.after(
            250, lambda: self.iconbitmap(App.get_resource_path("iconicon.ico"))
        )

        color = random.choice(parent.config.colors)
        self.config(bg=color)

        self.canvas = ctk.CTkCanvas(self, width=400,
                                    height=400, bg=color,
                                    borderwidth=0, highlightthickness=0)
        self.canvas.pack()

        #Store previous mouse position
        self.last_x = None
        self.last_y = None
        self.lines = []

        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

        self.bind("<Control-z>", self.undo_last_line)

        self.clear_button = ctk.CTkButton(self, text="Clear", command=self.clear_drawing)
        self.clear_button.pack(side="left", padx=5)
        self.save_button = ctk.CTkButton(self, text="Save", command=self.save_drawing)
        self.save_button.pack(side="left", padx=5)


    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y

    def draw(self, event):
        if self.last_x and self.last_y:
            line = self.canvas.create_line(
                self.last_x, self.last_y, event.x, event.y,
                width=5, fill="black", capstyle="round", smooth=True
            )
            self.lines.append(line)
        self.last_x, self.last_y = event.x, event.y

    def stop_draw(self, event):
        self.last_x, self.last_y = None, None

    def undo_last_line(self, event):
        if self.lines:
            last_line = self.lines.pop()
            self.canvas.delete(last_line)

    def clear_drawing(self):
        self.canvas.delete("all")
        self.lines.clear()

    def save_drawing(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if file_path:
            self.canvas.postscript(file="temp.ps", colormode='color')
            from PIL import Image
            img = Image.open("temp.ps")
            img.save(file_path)
            os.remove("temp.ps")
            messagebox.showinfo("Saved", f"Drawing saved as {file_path}")


class App(ctk.CTk):
    @staticmethod
    def get_resource_path(resource_name: str) -> str:
        if getattr(sys, "frozen", False):
            resource_path = os.path.join(sys._MEIPASS, resource_name)
        else:
            resource_path = os.path.join(os.path.dirname(__file__), resource_name)
        return resource_path

    @staticmethod
    def load_resources():
        return {
            "new": PhotoImage(file=App.get_resource_path("new.png")),
            "save": PhotoImage(file=App.get_resource_path("save.png")),
            "options": PhotoImage(file=App.get_resource_path("options.png")),
            "open": PhotoImage(file=App.get_resource_path("open.png")),
            "draw": PhotoImage(file=App.get_resource_path("draw.png")),
            "notify": PhotoImage(file=App.get_resource_path("notify.png"))
        }

    def __init__(self):
        super().__init__()

        self.config = StickyNoteConfig()
        self._setup_window()

        self.images = self.load_resources()

        self._create_sticky_note()
        self._load_auto_save()

    def _setup_window(self):
        #Window settings
        self.title("Pyst-it")
        self.geometry(f"{self.config.width}x{self.config.height}")
        self.resizable(False, False)
        self.iconbitmap(self.get_resource_path("iconicon.ico"))
        self.attributes("-alpha", self.config.alpha)
        self.attributes("-topmost", 1)

        ctk.FontManager.load_font(self.get_resource_path("Sticky Notes.ttf"))

    def _create_sticky_note(self):
        #Create the main post-it
        color = random.choice(self.config.colors)
        self.current_note = StickyNote(self, self.config, color, self.images)
        self.current_note.pack(fill="both", expand=True)

    def _auto_save(self):
        #Auto save the main post-it
        auto_save_path = self.get_resource_path("auto_save.json")
        content = self.current_note.get_content()

        try:
            with open(auto_save_path, "w") as file:
                json.dump({"content": content}, file)
        except Exception:
            pass

    def _load_auto_save(self):
        auto_save_path = self.get_resource_path("auto_save.json")

        try:
            if os.path.exists(auto_save_path):
                with open(auto_save_path, "r") as file:
                    data = json.load(file)
                    content = data.get("content", [])
                    self.current_note.set_content(content)
        except Exception:
            pass


if __name__ == "__main__":
    app = App()
    app.mainloop()