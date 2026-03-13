# czpp_run.py
import sys
from czpp_core import *

def run_script_from_file(filepath):
    """
    Načte, spustí a ošetří chyby pro zadaný cz++ skript.
    """
    try:
        # Pokusíme se otevřít a přečíst soubor
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"CHYBA: Soubor '{filepath}' nebyl nalezen.")
        return
    except Exception as e:
        print(f"CHYBA při čtení souboru: {e}")
        return

    # Vytvoříme novou instanci interpreteru pro každý běh
    interpreter = CzPlusPlusInterpreter()

    print(f"--- Spouštím skript: {filepath} ---")
    try:
        # Spustíme interpretaci kódu ze souboru
        interpreter.run(code)
        print("\n--- Skript úspěšně dokončen ---")

    except StopExecution:
        # Zachytíme, pokud byl skript ukončen příkazem 'zastav'
        print("\n--- Běh skriptu byl zastaven příkazem 'zastav' ---")

    except Exception as e:
        # Zachytíme a vypíšeme jakoukoliv jinou chybu, která nastala během běhu
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! CHYBA BĚHEM VYKONÁVÁNÍ SKRIPTU !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"Typ chyby: {type(e).__name__}: {e}")

def main():
    """
    Hlavní funkce, která zpracuje argumenty z příkazové řádky.
    """
    # Zkontrolujeme, zda byl zadán název souboru jako argument
    if len(sys.argv) != 2:
        print("Chyba: Nebyl zadán soubor ke spuštění.")
        print("Použití: python czpp_run.py <název_souboru.czpp>")
        sys.exit(1)  # Ukončíme program s chybovým kódem

    # Získáme název souboru z argumentů
    script_to_run = sys.argv[1]
    run_script_from_file(script_to_run)


# Tento standardní blok zajistí, že se funkce main() spustí,
# když je soubor volán přímo z terminálu.
if __name__ == "__main__":
    main()
