import subprocess
import os

def get_git_diff():
    # Ottiene i cambiamenti pronti per il commit (staged)
    return subprocess.check_output(["git", "diff", "--cached"]).decode("utf-8")

def main():
    diff = get_git_diff()
    if not diff:
        return

    # Usiamo la CLI di Copilot per decidere se il cambiamento è "significativo"
    # Il comando 'copilot chat' nel 2026 accetta input diretti per analisi veloci
    prompt = f"Analizza questo diff e rispondi solo 'SI' se modifica le API, l'installazione o le feature principali, altrimenti 'NO':\n{diff}"
    
    significance = subprocess.check_output(["copilot", "chat", prompt]).decode("utf-8").strip()

    if "SI" in significance.upper():
        print("🚀 Cambiamento significativo rilevato. Aggiornamento README in corso...")
        
        # Chiediamo a Copilot di aggiornare il file
        subprocess.run([
            "copilot", "run", 
            "Aggiorna il file README.md basandoti su questi cambiamenti nel codebase: " + diff,
            "--file", "README.md"
        ])
        
        # Aggiungiamo il README aggiornato al commit corrente
        subprocess.run(["git", "add", "README.md"])
    else:
        print("✅ Modifiche minori, il README rimane invariato.")

if __name__ == "__main__":
    main()