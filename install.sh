#!/bin/bash

# =================================================
# == Instalační skript pro cz++ IDE (Finální oprava) ==
# =================================================
# Tento skript:
# 1. Vytvoří 'start.sh', který provádí údržbu jednou za 3 dny.
# 2. Správně dosadí cestu k aplikaci do 'start.sh'.
# 3. Správně detekuje typ shellu a zapíše do správného souboru.
# 4. Přidá příkaz 'cz++' do vašeho shellu.

echo "--- Spouštím instalátor pro cz++ IDE ---"

# Zjistíme absolutní cestu ke složce s aplikací.
APP_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
START_SCRIPT_PATH="$HOME/start.sh"

echo "Složka aplikace je: $APP_DIR"
echo "Cílová cesta pro spouštěč: $START_SCRIPT_PATH"

# --- KROK 1: Vytvoření spouštěcího skriptu 'start.sh' v $HOME ---
cat > "$START_SCRIPT_PATH" << EOF
#!/bin/bash
# Tento skript byl automaticky vygenerován instalátorem.

cd "$APP_DIR"

echo "-------------------------------------"
echo "--- Kontrola a spuštění cz++ IDE ---"
echo "-------------------------------------"

# --- KROK 1: Rychlá kontrola základních závislostí (vždy) ---
echo "--- Rychlá kontrola základních závislostí ---"
if ! command -v python &> /dev/null || ! command -v pip &> /dev/null; then echo "CHYBA: Python nebo Pip není nainstalován."; exit 1; fi
python -c "import tkinter" &> /dev/null
if [ \$? -ne 0 ]; then echo "INFO: GUI knihovna (tkinter) není nalezena. Probíhá instalace..."; pkg install python-tkinter -y; fi
if ! command -v termux-open-url &> /dev/null; then echo "INFO: Balíček Termux API není nalezen. Probíhá instalace..."; pkg install termux-api -y; fi
pip show "Pillow" &> /dev/null
if [ \$? -ne 0 ]; then echo "INFO: Knihovna 'Pillow' není nalezena. Probíhá instalace..."; pip install "Pillow"; fi
echo "[OK] Základní závislosti jsou připraveny."
echo ""

# --- KROK 2: Časově omezená kontrola aktualizací ---
TIMESTAMP_FILE="\$HOME/.czpp_last_check"
SHOULD_CHECK_UPDATES=false
CHECK_INTERVAL=259200 # 3 dny v sekundách

echo "--- Kontrola potřeby aktualizací ---"
if [ ! -f "\$TIMESTAMP_FILE" ]; then
    echo "[INFO] První spuštění, provádím úvodní hloubkovou kontrolu aktualizací."
    SHOULD_CHECK_UPDATES=true
else
    LAST_CHECK=\$(cat "\$TIMESTAMP_FILE")
    CURRENT_TIME=\$(date +%s)
    if [ \$((\$CURRENT_TIME - \$LAST_CHECK)) -gt \$CHECK_INTERVAL ]; then
        echo "[INFO] Uplynuly více než 3 dny od poslední kontroly, hledám aktualizace."
        SHOULD_CHECK_UPDATES=true
    else
        echo "[INFO] Poslední hloubková kontrola proběhla nedávno. Přeskakuji."
    fi
fi

if [ "\$SHOULD_CHECK_UPDATES" = true ]; then
    if command -v pkg &> /dev/null; then
        echo "Provádím 'pkg update' a 'pkg upgrade'..."
        pkg update -y && pkg upgrade -y
    elif command -v apt &> /dev/null; then
        echo "Provádím 'apt update' a 'apt upgrade'..."
        apt update -y && apt upgrade -y
    fi

    echo "Kontroluji a aktualizuji všechny Python (pip) balíčky..."
    OUTDATED_PACKAGES=\$(pip list --outdated | tail -n +3)
    if [ -n "\$OUTDATED_PACKAGES" ]; then
        echo "\$OUTDATED_PACKAGES" | awk '{print \$1}' | xargs -n1 pip install --upgrade
        echo "[OK] Všechny pip balíčky byly aktualizovány."
    else
        echo "[OK] Všechny pip balíčky jsou již aktuální."
    fi

    echo \$(date +%s) > "\$TIMESTAMP_FILE"
    echo "[OK] Hloubková kontrola dokončena."
fi

echo ""
echo "Všechny kontroly dokončeny. Spouštím cz++ IDE..."
echo "-------------------------------------"

python czpp_gui.py "\$@"

echo "-------------------------------------"
echo "Editor byl ukončen."
EOF

chmod +x "$START_SCRIPT_PATH"
echo "Spouštěcí skript '$START_SCRIPT_PATH' byl úspěšně vytvořen."

# --- KROK 2: Přidání příkazu 'cz++' do shellu ---
SHELL_TYPE=$(basename "$SHELL")
RC_FILE=""

if [ "$SHELL_TYPE" = "bash" ]; then
    RC_FILE="$HOME/.bashrc"
elif [ "$SHELL_TYPE" = "zsh" ]; then
    RC_FILE="$HOME/.zshrc"
else
    echo "CHYBA: Váš shell ($SHELL_TYPE) není automaticky podporován."
    exit 1
fi

echo "Konfigurační soubor shellu je: $RC_FILE"

CZPP_COMMAND="
# Přidáno instalátorem cz++ IDE
cz++() {
    bash \"$START_SCRIPT_PATH\" \"\$@\"
}
"

if grep -q "# Přidáno instalátorem cz++ IDE" "$RC_FILE"; then
    echo "INFO: Příkaz 'cz++' se zdá být již nainstalován. Přeskakuji."
else
    echo "Přidávám příkaz 'cz++' do $RC_FILE..."
    echo "$CZPP_COMMAND" >> "$RC_FILE"
    echo "[OK] Příkaz 'cz++' byl přidán."
    echo "Restartujte prosím terminál nebo spusťte 'source $RC_FILE' pro aktivaci."
fi

echo "--- Instalace dokončena ---"
