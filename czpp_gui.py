# czpp_gui.py (Finální verze s upraveným vzhledem tlačítek a konzole)

import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, simpledialog
import queue
import threading
import subprocess
import os

# Pokus o import knihovny Pillow
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Import jádra cz++
from czpp_core import *

class CzppIdeApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("cz++ IDE")
        self.root.geometry("600x700")
        self.current_file_path = None
        self.script_thread = None
        self.interpreter = None
        self.widgets = {}

        self.load_app_icon()

        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.input_queue = queue.Queue()
        self.input_event = threading.Event()

        self.setup_widgets()
        self.setup_menu()
        self.process_gui_commands()

    def load_app_icon(self):
        try:
            logo_path = os.path.join(os.path.dirname(__file__), 'czpp_logo.png')
            if os.path.exists(logo_path):
                logo_image = tk.PhotoImage(file=logo_path)
                self.root.iconphoto(True, logo_image)
        except tk.TclError as e:
            print(f"CHYBA: Nepodařilo se načíst logo: {e}")

    def setup_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- ZMĚNA ZDE: Finální lišta s tlačítky ---
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))

        self.convert_cz_to_py_button = tk.Button(button_frame, text=".czpp do .py", command=self.run_script_cz_to_py)
        self.convert_cz_to_py_button.pack(side=tk.LEFT, padx=2)

        self.convert_py_to_cz_button = tk.Button(button_frame, text=".py do .czpp", command=self.run_script_py_to_cz)
        self.convert_py_to_cz_button.pack(side=tk.LEFT, padx=2)

        self.stop_button = tk.Button(button_frame, text="STOP", command=self.stop_script, state=tk.DISABLED, bg='red', fg='white')
        self.stop_button.pack(side=tk.RIGHT, padx=2)

        self.run_button = tk.Button(button_frame, text="Spustit kód", command=self.run_script_czpp, bg='#4CAF50', fg='white')
        self.run_button.pack(side=tk.RIGHT, padx=2)
        # --- KONEC ZMĚNY ---

        editor_frame = tk.Frame(main_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        self.editor = scrolledtext.ScrolledText(editor_frame, wrap=tk.WORD, undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True)

        console_frame = tk.Frame(main_frame, height=200)
        console_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        console_frame.pack_propagate(False)
        # --- ZMĚNA ZDE: Bílá konzole ---
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, state=tk.DISABLED, bg='white', fg='black')
        self.console.pack(fill=tk.BOTH, expand=True)

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Soubor", menu=file_menu)
        file_menu.add_command(label="Nový soubor", command=self.new_file)
        file_menu.add_command(label="Otevřít", command=self.open_file)
        file_menu.add_command(label="Uložit", command=self.save_file)
        file_menu.add_command(label="Uložit jako...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Konec", command=self.root.quit)

    def new_file(self):
        self.editor.delete('1.0', tk.END)
        self.current_file_path = None
        self.root.title("Nový soubor - cz++ IDE")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("cz++ soubory", "*.czpp"), ("Python soubory", "*.py"), ("Všechny soubory", "*.*")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', f.read())
            self.current_file_path = path
            self.root.title(f"{os.path.basename(path)} - cz++ IDE")

    def save_file(self):
        if self.current_file_path:
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.get('1.0', tk.END))
        else:
            self.save_as_file()

    def save_as_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".czpp", filetypes=[("cz++ soubory", "*.czpp"), ("Python soubory", "*.py"), ("Všechny soubory", "*.*")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.editor.get('1.0', tk.END))
            self.current_file_path = path
            self.root.title(f"{os.path.basename(path)} - cz++ IDE")

    def _prepare_run(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.run_button.config(state=tk.DISABLED)
        self.convert_cz_to_py_button.config(state=tk.DISABLED)
        self.convert_py_to_cz_button.config(state=tk.DISABLED)

        for widget in self.widgets.values():
            widget.destroy()
        self.widgets.clear()

    def _finish_run(self):
        self.stop_button.config(state=tk.DISABLED)
        self.run_button.config(state=tk.NORMAL)
        self.convert_cz_to_py_button.config(state=tk.NORMAL)
        self.convert_py_to_cz_button.config(state=tk.NORMAL)
        self.script_thread = None
        self.interpreter = None

    def _write_to_console(self, message):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, message)
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def run_script_czpp(self):
        self._prepare_run()
        code = self.editor.get('1.0', tk.END)
        self.interpreter = CzPlusPlusInterpreter(self.command_queue, self.result_queue, self.provide_input)

        def target():
            original_print = __builtins__.print
            __builtins__.print = lambda *args, **kwargs: self._write_to_console(" ".join(map(str, args)) + "\n")

            self._write_to_console("--- Spouštím skript... ---\n")
            try:
                self.interpreter.run(code)
                self._write_to_console("\n--- Skript dokončen. ---\n")
            except StopExecution:
                self._write_to_console("\n--- Skript byl zastaven uživatelem. ---\n")
            except Exception as e:
                self._write_to_console(f"\n!!! CHYBA BĚHEM VYKONÁVÁNÍ SKRIPTU !!!\n{e}\n")
            finally:
                __builtins__.print = original_print
                self.root.after(0, self._finish_run)

        self.script_thread = threading.Thread(target=target, daemon=True)
        self.script_thread.start()

    def run_script_cz_to_py(self):
        messagebox.showinfo("Informace", "Převod z .czpp do .py zatím není implementován.")

    def run_script_py_to_cz(self):
        messagebox.showinfo("Informace", "Převod z .py do .czpp zatím není implementován.")

    def stop_script(self):
        if self.script_thread and self.script_thread.is_alive():
            if self.interpreter: self.interpreter.request_stop()
            self._write_to_console("\n--- Zastavuji skript... ---\n")

    def run_czpp_function(self, function_name):
        if self.interpreter and function_name in self.interpreter.functions:
            def target():
                original_print = __builtins__.print
                __builtins__.print = lambda *args, **kwargs: self._write_to_console(" ".join(map(str, args)) + "\n")
                try:
                    self._write_to_console(f"\n--- Volám funkci '{function_name}'... ---\n")
                    self.interpreter.call_function(function_name, [])
                except Exception as e:
                    self._write_to_console(f"\n!!! CHYBA BĚHEM VOLÁNÍ FUNKCE '{function_name}' !!!\n{e}\n")
                finally:
                    __builtins__.print = original_print
            threading.Thread(target=target, daemon=True).start()
        else:
            self._write_to_console(f"\nCHYBA: Funkce '{function_name}' nebyla nalezena nebo skript neběží.\n")

    def process_gui_commands(self):
        try:
            command, args = self.command_queue.get_nowait()
            parent = self.root

            if command == 'create_toplevel':
                self.result_queue.put(parent)
            elif command == 'set_title':
                win, title = args; win.title(f"{title} - cz++ IDE"); self.result_queue.put(None)
            elif command == 'config_widget':
                widget, config = args; widget.config(**config); self.result_queue.put(None)

            elif command == 'create_widget':
                win_id, widget_type, widget_name, config = args
                new_widget = None
                try:
                    if widget_type == 'label':
                        new_widget = tk.Label(parent, text=config.get('text', ''))
                    elif widget_type == 'button':
                        callback = lambda name=config.get('command'): self.run_czpp_function(name)
                        new_widget = tk.Button(parent, text=config.get('text', ''), command=callback)
                    elif widget_type == 'image':
                        if not PILLOW_AVAILABLE: raise RuntimeError("Knihovna Pillow není nainstalována (pip install Pillow)")
                        filepath = config.get('filepath')
                        if not filepath or not os.path.exists(filepath): raise FileNotFoundError(f"Soubor obrázku nenalezen: {filepath}")

                        image = Image.open(filepath)
                        photo = ImageTk.PhotoImage(image)
                        new_widget = tk.Label(parent, image=photo)
                        new_widget.image = photo

                    if new_widget:
                        self.widgets[widget_name] = new_widget
                        self.result_queue.put(None)
                    else:
                        raise ValueError(f"Neznámý typ widgetu: {widget_type}")
                except Exception as e:
                    self.result_queue.put(e)

            elif command == 'place_widget':
                win_id, widget_name, config = args
                widget = self.widgets.get(widget_name)
                if widget:
                    widget.place(x=config.get('x', 0), y=config.get('y', 0)); self.result_queue.put(None)
                else:
                    self.result_queue.put(NameError(f"Widget s názvem '{widget_name}' nebyl nalezen."))
            else:
                self.result_queue.put(NotImplementedError(f"Příkaz '{command}' není implementován v GUI."))

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_gui_commands)

    def provide_input(self, prompt):
        self.input_event.clear()
        self.root.after(0, self.ask_for_input, prompt)
        self.input_event.wait()
        return self.input_queue.get()

    def ask_for_input(self, prompt):
        user_input = simpledialog.askstring("Vstup od uživatele", prompt, parent=self.root)
        self.input_queue.put(user_input or "")
        self.input_event.set()

if __name__ == "__main__":
    if not PILLOW_AVAILABLE:
        print("VAROVÁNÍ: Knihovna Pillow není nainstalována.")
        print("Pro plnou funkčnost (zobrazování obrázků) ji nainstalujte příkazem:")
        print("pip install Pillow")
    app = CzppIdeApp()
    app.root.mainloop()
