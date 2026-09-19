import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

class InstallerTests(unittest.TestCase):
    def test_opt_in_preserves_and_repeated_install_backs_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            agents = home / 'AGENTS.md'
            agents.write_text('Existing instructions.\n')
            installer.install(home)
            self.assertEqual(agents.read_text(), 'Existing instructions.\n')
            target = home / 'skills/codex-usage-budget'
            (target / 'personal-note.txt').write_text('Keep me')
            installer.install(home, True)
            first = agents.read_text()
            installer.install(home, True)
            self.assertEqual(first, agents.read_text())
            self.assertTrue(first.startswith('Existing instructions.'))
            self.assertEqual(first.count(installer.START), 1)
            self.assertTrue(list((home / 'usage-budget-backups').glob('*/codex-usage-budget/personal-note.txt')))

    def test_malformed_instruction_block_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / 'AGENTS.md').write_text(installer.START)
            with self.assertRaises(ValueError):
                installer.install(home, True)
            self.assertFalse((home / 'skills').exists())

if __name__ == '__main__':
    unittest.main()
