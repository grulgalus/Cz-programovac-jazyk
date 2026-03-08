# cz++ IDE

![cz++ Logo](czpp_logo.png)

Vítejte v **cz++ IDE**, jednoduchém vývojovém prostředí pro `cz++` – zjednodušený programovací jazyk s českou syntaxí, postavený na Pythonu. Tento projekt je navržen pro snadné a rychlé prototypování, výuku programování a experimentování.

## ✨ Klíčové vlastnosti

*   **Jednoduchá česká syntaxe:** Příkazy jako `vypis`, `funkce`, `pokud`, `dokud` jsou snadno čitelné a pochopitelné.
*   **Vestavěné IDE:** Vše, co potřebujete, je v jednom okně – editor kódu i konzole pro výstup.
*   **Tvorba grafického rozhraní (GUI):** Jednoduše vytvářejte okna, tlačítka, texty a obrázky.
*   **Podpora obrázků:** Díky knihovně Pillow můžete ve svých aplikacích zobrazovat obrázky v různých formátech (PNG, JPG...).
*   **Asynchronní programování:** Pomocí `asynchronni blok` můžete spouštět kód na pozadí, ideální pro Discord boty nebo jiné dlouhotrvající úlohy, aniž by zamrzla hlavní aplikace.
*   **Multiplatformní:** Běží na Linuxu a v prostředí Termux na Androidu.

## 🚀 Instalace a spuštění

Instalace je navržena tak, aby byla co nejjednodušší.

1.  **Naklonujte si repozitář:**
    ```bash
    git clone https://github.com/[vase_jmeno]/[nazev_repozitare].git
    cd [nazev_repozitare]
    ```

2.  **Spusťte instalační skript:** Tento skript se postará o instalaci všech potřebných závislostí (Python, Tkinter, Pillow).
    ```bash
    bash install.sh
    ```

3.  **Spusťte IDE:** Po úspěšné instalaci můžete IDE kdykoliv spustit.
    ```bash
    bash start.sh
    ```

## 📝 Příklady kódu

### Hello, World!

```cz++
// Toto je jednoduchý komentář
vypis "Ahoj, světe z cz++!"
```

### Vytvoření jednoduchého okna

```cz++
vytvor okno jmenem mojeApp
mojeApp.nazev "Moje první aplikace"
mojeApp.barva_pozadi "#e0e0e0"

mojeApp.vytvor_text "uvitani" s textem "Vítejte v mé aplikaci!"
mojeApp.umisti "uvitani" na x 20 y 20

mojeApp.vytvor_obrazek "logo" ze_souboru "czpp_logo.png"
mojeApp.umisti "logo" na x 20 y 60

mojeApp.zobraz
```

### Asynchronní blok pro Discord bota

```cz++
vypis "Hlavní program běží, bot se spouští na pozadí..."

asynchronni blok
    # Tento kód uvnitř je čistý Python!
    import discord
    
    bot = discord.Bot()

    @bot.event
    async def on_ready():
        print(f"Bot je online jako {bot.user}!")

    @bot.slash_command(description="Odpoví 'Pong!'")
    async def ping(ctx):
        await ctx.respond("Pong!")

    # Vložte svůj token
    bot.run("TVUJ_DISCORD_TOKEN")
konec

vypis "Hlavní program pokračuje a není blokován botem."
```

## 📄 Licence

Tento projekt je licencován pod **MIT licencí**. Více informací naleznete v souboru `LICENSE`.
