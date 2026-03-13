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
            ["git", "diff", "--staged"], 
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
    prompt = f"Analizza questo diff e rispondi solo 'SI' se modifica le API, l'installazione o le feature principali, altrimenti 'NO':\n{diff}"
    
    significance = subprocess.check_output(["copilot", "-p", prompt]).decode("utf-8").strip()

    if "SI" in significance.upper():
        print("🚀 Cambiamento significativo rilevato. Aggiornamento README in corso...")
        
        # Chiediamo a Copilot di aggiornare il file
        subprocess.run([
            "copilot", "run", 
            "Aggiorna il file README.md basandoti su questi cambiamenti nel codebase: " + diff,
            "-y"
        ])
        
        # Aggiungiamo il README aggiornato al commit corrente
        subprocess.run(["git", "add", "README.md"])
    else:
        print("✅ Modifiche minori, il README rimane invariato.")

if __name__ == "__main__":
    main()