# czpp_core.py (s podporou pro asynchronní bloky)

import re
import time
import subprocess
import threading
import asyncio

# --- VÝJIMKY ---
class ReturnException(Exception):
    def __init__(self, value): self.value = value
class BreakException(Exception): pass
class ContinueException(Exception): pass
class StopExecution(Exception): pass

# --- ASYNC EXECUTION HELPER ---
def _run_async_task(code_string, global_vars, local_vars):
    """
    Spustí řetězec asynchronního Python kódu v nové smyčce událostí.
    Tato funkce je určena ke spuštění v samostatném vlákně.
    """
    indented_code = "\n".join(["    " + line for line in code_string.splitlines()])
    wrapper_code = f"async def __async_wrapper():\n{indented_code}"
    try:
        exec(wrapper_code, global_vars, local_vars)
        coro = local_vars['__async_wrapper']()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
    except Exception as e:
        print(f"\n!!! CHYBA V ASYNCHRONNÍM BLOKU !!!\n-> {type(e).__name__}: {e}\n")

# --- PROXY TŘÍDY ---
class GuiObjectProxy:
    def __init__(self, interpreter, obj_id):
        self._interpreter = interpreter
        self._id = obj_id
    def zrus(self):
        self._interpreter.sync_gui_call('destroy_widget', self._id)

class WindowProxy(GuiObjectProxy):
    def nazev(self, title):
        self._interpreter.sync_gui_call('set_title', self._id, title)
    def barva_pozadi(self, color):
        self._interpreter.sync_gui_call('config_widget', self._id, {'background': color})
    def zobraz(self):
        self._interpreter.sync_gui_call('window_show', self._id)
    def skryj(self):
        self._interpreter.sync_gui_call('window_hide', self._id)
    def vytvor_text(self, widget_name, text):
        self._interpreter.sync_gui_call('create_widget', self._id, 'label', widget_name, {'text': text})
    def vytvor_tlacitko(self, widget_name, text, command_func_name):
        self._interpreter.sync_gui_call('create_widget', self._id, 'button', widget_name, {'text': text, 'command': command_func_name})
    def vytvor_obrazek(self, widget_name, filepath):
        self._interpreter.sync_gui_call('create_widget', self._id, 'image', widget_name, {'filepath': filepath})
    def umisti(self, widget_name, x, y):
        self._interpreter.sync_gui_call('place_widget', self._id, widget_name, {'x': int(x), 'y': int(y)})

class BrowserProxy(GuiObjectProxy):
    def jdi_na(self, url):
        if not url.startswith('http'): url = 'http://' + url
        print(f"Otevírám {url}...")
        try:
            subprocess.run(['termux-open-url', url], check=True, capture_output=True)
        except Exception as e:
            print(f"CHYBA při otevírání URL: {e}")

# --- HLAVNÍ TŘÍDA INTERPRETERU ---
class CzPlusPlusInterpreter:
    def __init__(self, command_queue=None, result_queue=None, input_handler=None):
        self.variables = {}
        self.functions = {}
        self.output_lines = []
        self.call_stack = []
        self.loop_stack = []
        self._stop_flag = False
        self.command_queue = command_queue
        self.result_queue = result_queue
        self.input_handler = input_handler or input
        self.background_threads = []
        self.safe_globals = {
            "abs": abs, "min": min, "max": max, "len": len,
            "int": int, "float": float, "retezec": str, "bool": bool,
            "range": range, "pravda": True, "nepravda": False,
            "print": print, "spani": time.sleep,
        }

    def sync_gui_call(self, command, *args):
        if not self.command_queue or not self.result_queue:
            print("CHYBA: GUI není dostupné v tomto režimu.")
            return None
        self.command_queue.put((command, args))
        result = self.result_queue.get()
        if isinstance(result, Exception): raise result
        return result

    def request_stop(self): self._stop_flag = True
    def _check_stop(self):
        if self._stop_flag: raise StopExecution()

    def eval_expr(self, expr: str):
        self._check_stop()
        expr = expr.strip()
        expr = re.sub(r"\bpravda\b", "True", expr, flags=re.IGNORECASE)
        expr = re.sub(r"\bnepravda\b", "False", expr, flags=re.IGNORECASE)
        eval_context = {**self.safe_globals, **self.variables}
        return eval(expr, {"__builtins__": None}, eval_context)

    def _strip_inline_comment(self, line: str) -> str:
        if "//" in line: line = line.split("//", 1)[0]
        return line.rstrip()

    def parse_stmt(self, line: str):
        self._check_stop()
        line = self._strip_inline_comment(line).strip()
        if not line: return
        if line.endswith(";"): line = line[:-1].rstrip()
        if line == "konec": raise SyntaxError("'konec' nalezeno mimo definici funkce.")

        if line.startswith("importuj "):
            parts = line.split()
            if len(parts) == 2:
                lib_name = parts[1]
                alias = lib_name
            elif len(parts) == 4 and parts[2] == "jako":
                lib_name = parts[1]
                alias = parts[3]
            else:
                raise SyntaxError("Chybná syntaxe importu.")
            try:
                self.variables[alias] = __import__(lib_name)
                print(f"Knihovna '{lib_name}' importována jako '{alias}'.")
            except ImportError:
                raise ImportError(f"Knihovnu '{lib_name}' se nepodařilo najít.")
            return

        if line.startswith("ziskej "):
            m = re.match(r"ziskej\s+([A-Za-z_]\w*)\s*=\s*vstup\s*$(.*)$", line)
            if m:
                var_name, prompt_expr = m.groups()
                prompt = self.eval_expr(prompt_expr.strip()) if prompt_expr.strip() else ""
                self.variables[var_name] = self.input_handler(prompt)
                return

        if line.startswith("vytvor "):
            m = re.match(r"vytvor\s+(\w+)\s+jmenem\s+([A-Za-z_]\w*)", line)
            if m:
                obj_type, obj_name = m.groups()
                if obj_type == "okno":
                    win_id = self.sync_gui_call('create_toplevel')
                    self.variables[obj_name] = WindowProxy(self, win_id)
                elif obj_type == "prohlizec":
                    self.variables[obj_name] = BrowserProxy(self, None)
                else: raise SyntaxError(f"Neznamy typ objektu: {obj_type}")
                return
            else: raise SyntaxError("Chybna syntaxe vytvor")

        m = re.match(r"([A-Za-z_]\w*)\.([\w_]+)\s*(.*)", line)
        if m:
            obj_name, action, params_str = m.groups()
            if obj_name not in self.variables or not isinstance(self.variables[obj_name], (GuiObjectProxy, BrowserProxy)):
                raise SyntaxError(f"Objekt '{obj_name}' neexistuje.")
            obj_proxy = self.variables[obj_name]
            params_str = params_str.strip()
            parts = re.split(r'\s+s textem\s+|\s+a prikazem\s+|\s+ze_souboru\s+|\s+na x\s+|\s+y\s+', params_str)
            args = [self.eval_expr(p) for p in parts if p]
            if hasattr(obj_proxy, action):
                method_to_call = getattr(obj_proxy, action)
                method_to_call(*args)
                return
            else:
                raise SyntaxError(f"Objekt '{obj_name}' nemá metodu '{action}'.")

        if line.startswith("vypis "):
            expr = line[len("vypis "):].strip(); val = self.eval_expr(expr)
            print(val); self.output_lines.append(str(val))
            return

        m = re.match(r"(\w+)\s*$(.*)$", line)
        if m:
            fname, args_str = m.groups()
            args = [self.eval_expr(a.strip()) for a in self._split_args(args_str)] if args_str else []
            if fname in self.functions: self.call_function(fname, args); return
            else: raise SyntaxError(f"Neznama funkce: {fname}")

        raise SyntaxError(f"Neznamy prikaz: {line}")

    def _split_args(self, args_str):
        args, current, depth, in_str, str_ch = [], '', 0, False, None
        for c in args_str:
            if in_str:
                current += c
                if c == str_ch: in_str = False
                continue
            if c in ("'", '"'):
                in_str, str_ch, current = True, c, current + c
                continue
            if c == ',' and depth == 0:
                args.append(current); current = ''
            else:
                if c == '(': depth += 1
                elif c == ')': depth -= 1
                current += c
        if current.strip(): args.append(current)
        return args

    def call_function(self, fname, args):
        self._check_stop(); func = self.functions[fname]
        if len(args) != len(func['params']):
            raise TypeError(f"Funkce {fname} ocekava {len(func['params'])} argumentu, dostala {len(args)}")
        local_vars = dict(zip(func['params'], args))
        self.call_stack.append(self.variables)
        self.variables = {**self.variables, **local_vars}
        try:
            self.run('\n'.join(func['body']))
        except ReturnException as ret:
            self.variables = self.call_stack.pop(); return ret.value
        finally:
            if self.call_stack: self.variables = self.call_stack.pop()

    def run(self, code: str):
        self._check_stop(); lines = code.splitlines(); i = 0
        while i < len(lines):
            self._check_stop()
            line = self._strip_inline_comment(lines[i]).strip()
            try:
                if not line:
                    i += 1
                    continue

                if line.startswith("asynchronni blok"):
                    body, j = [], i + 1
                    found_konec = False
                    while j < len(lines):
                        end_line = self._strip_inline_comment(lines[j]).strip()
                        if end_line == "konec":
                            found_konec = True
                            break
                        body.append(lines[j])
                        j += 1
                    if not found_konec: raise SyntaxError("Asynchronní blok nebyl správně ukončen slovem 'konec'.")
                    async_code_string = "\n".join(body)
                    thread_globals = self.safe_globals.copy()
                    thread_locals = self.variables.copy()
                    thread = threading.Thread(target=_run_async_task, args=(async_code_string, thread_globals, thread_locals))
                    thread.daemon = True
                    self.background_threads.append(thread)
                    thread.start()
                    print("[INFO] Asynchronní blok spuštěn na pozadí.")
                    i = j + 1
                    continue

                if line.startswith("funkce "):
                    m = re.match(r"funkce\s+(\w+)\s*$(.*?)$\s*$", line)
                    if not m: raise SyntaxError("Chybná syntaxe definice funkce.")
                    fname, params_str = m.groups()
                    params = [p.strip() for p in params_str.split(",")] if params_str else []
                    body, j = [], i + 1
                    found_konec = False
                    while j < len(lines):
                        end_line = self._strip_inline_comment(lines[j]).strip()
                        if end_line == "konec":
                            found_konec = True
                            break
                        body.append(lines[j])
                        j += 1
                    if not found_konec: raise SyntaxError(f"Funkce '{fname}' nebyla správně ukončena.")
                    self.functions[fname] = {'params': params, 'body': body}
                    i = j + 1
                    continue
                self.parse_stmt(line)
                i += 1
            except Exception as e:
                error_line_content = lines[i].strip()
                error_message = f"Chyba na řádku {i + 1}: '{error_line_content}'\n-> {type(e).__name__}: {e}"
                raise Exception(error_message) from e

