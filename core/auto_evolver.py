# core/auto_evolver.py
import subprocess
import os
import datetime
import shutil
from utils.meta_logger import MetaLogger  # Przykład - zalecam taki logger do analizy meta
# import openai  # jeśli używasz GPT przez API

class AutoEvolver:
    def __init__(self, repo_path="."):
        self.repo_path = repo_path
        self.logger = MetaLogger(log_path=os.path.join(repo_path, "data/auto_evolver.log"))

    def evolve(self, prompt):
        """
        Automatycznie rozwija kod na podstawie promptu
        1. Tworzy branch
        2. Generuje nowy kod (tutaj podłącz LLM)
        3. Wdraża zmiany do repo (commit)
        4. Testuje (unit/integration)
        5. Merge lub rollback
        6. Loguje cały proces
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"auto_evolve_{timestamp}"

        self.logger.log(f"START AUTO-EVOLVE: {branch_name} | PROMPT: {prompt}")

        # 1. Tworzenie brancha
        try:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.repo_path, check=True)
        except Exception as e:
            self.logger.log(f"ERROR: nie można utworzyć brancha: {e}")
            return False

        # 2. Generowanie kodu (placeholder)
        try:
            # Tu podłącz generator kodu – np. OpenAI API, lokalny LLM, custom script:
            # generated_code = self.generate_code(prompt)
            generated_code = "# Przykładowy kod wygenerowany przez LLM\nprint('Hello AI Evolution!')\n"
            file_path = os.path.join(self.repo_path, "auto_evolve_gen.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(generated_code)
            self.logger.log(f"Kod wygenerowany i zapisany: {file_path}")
        except Exception as e:
            self.logger.log(f"ERROR generowania kodu: {e}")
            self.rollback(branch_name)
            return False

        # 3. Commit wygenerowanego kodu
        try:
            subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True)
            subprocess.run(["git", "commit", "-m", f"Auto-evolve: {prompt}"], cwd=self.repo_path, check=True)
        except Exception as e:
            self.logger.log(f"ERROR przy commit: {e}")
            self.rollback(branch_name)
            return False

        # 4. Testowanie kodu (tu możesz podpiąć pytest lub custom test runner)
        tests_passed = self.run_tests()
        if not tests_passed:
            self.logger.log(f"TESTS FAILED. Rollback!")
            self.rollback(branch_name)
            return False

        # 5. (Opcjonalnie) Merge do main/dev jeśli testy przeszły
        try:
            subprocess.run(["git", "checkout", "main"], cwd=self.repo_path, check=True)
            subprocess.run(["git", "merge", branch_name], cwd=self.repo_path, check=True)
            self.logger.log(f"SUCCESS: Zmiany zmergowane do main!")
        except Exception as e:
            self.logger.log(f"ERROR przy merge: {e}")
            return False

        self.logger.log(f"AUTO-EVOLVE zakończone sukcesem: {branch_name}")
        return True

    def generate_code(self, prompt):
        """
        Podłącz tutaj dowolny LLM lub inny system generujący kod.
        """
        # Przykład: OpenAI API
        # response = openai.Completion.create(...)
        # return response['choices'][0]['text']
        raise NotImplementedError("Podłącz generator kodu!")

    def run_tests(self):
        """
        Uruchamia testy automatyczne, zwraca True jeśli przeszły
        """
        try:
            result = subprocess.run(["pytest"], cwd=self.repo_path)
            return result.returncode == 0
        except Exception as e:
            self.logger.log(f"ERROR przy testach: {e}")
            return False

    def rollback(self, branch_name):
        """
        Usuwa nieudany branch, przywraca main
        """
        try:
            subprocess.run(["git", "checkout", "main"], cwd=self.repo_path, check=True)
            subprocess.run(["git", "branch", "-D", branch_name], cwd=self.repo_path, check=True)
            self.logger.log(f"Rollback wykonany: branch {branch_name} usunięty.")
        except Exception as e:
            self.logger.log(f"ERROR przy rollback: {e}")

