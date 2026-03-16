import subprocess
import os

def get_git_diff():
    # get directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # change to the root of the repository (assuming the script is in .github/scripts/)
    repo_root = os.path.abspath(os.path.join(script_dir, "../../"))
    os.chdir(repo_root)
    # Creiamo una copia pulita dell'ambiente di sistema
    clean_env = os.environ.copy()
    
    # Rimuoviamo TUTTE le variabili che Git imposta durante gli hook
    # Queste sono le responsabili dell'errore "unknown option"
    git_vars = [
        'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 
        'GIT_PREFIX', 'GIT_QUARANTINE_PATH'
    ]
    for var in git_vars:
        clean_env.pop(var, None)

    try:
        # Usiamo '--staged' (sinonimo moderno di --cached) 
        # e forziamo l'esecuzione nella cartella corrente
        return subprocess.check_output(
            ["git", "diff", "--name-only", "--cached"], 
            env=clean_env,
            cwd=os.getcwd(),
            stderr=subprocess.STDOUT
        ).decode("utf-8")
    except subprocess.CalledProcessError as e:
        # Se il comando fallisce (es. primo commit del repo), restituiamo stringa vuota
        return ""

def main():
    diff = get_git_diff()
    if not diff:
        return

    # Usiamo la CLI di Copilot per decidere se il cambiamento è "significativo"
    # Il comando 'copilot chat' nel 2026 accetta input diretti per analisi veloci
    prompt = f"In base a questi file modificati: {diff}, "\
        "Se necessario, ossia se i cambiamenti sono significativi, genera un breve aggiornamento da inserire nel README.md. "\
        "Se i cambiamenti sono minori, restituisci una stringa vuota."

    try:
        # Usiamo un timeout per evitare che lo script resti appeso
        result = subprocess.run(
            ["copilot", "-p", prompt],
            capture_output=True,
            text=True,
            env=os.environ,
            timeout=30 # 30 secondi di tempo massimo
        )

        if result.returncode == 0:
            # Invece di sovrascrivere tutto, appendiamo o aggiorniamo una sezione
            with open("README.md", "a", encoding="utf-8") as f:
                f.write(f"\n\n## Update 2026\n{result.stdout.strip()}\n")
            
            subprocess.run(["git", "add", "README.md"])
            print("✅ README aggiornato (Append mode).")
            
    except subprocess.TimeoutExpired:
        print("⚠️ Copilot ci sta mettendo troppo. Salto l'aggiornamento per non bloccare il commit.")
    except Exception as e:
        print(f"❌ Errore API: {e}")

if __name__ == "__main__":
    main()