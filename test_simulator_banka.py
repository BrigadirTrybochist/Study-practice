import io
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from unittest.mock import patch

import SimulatorBanka as sb


class SimulatorBankaConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_data_file = os.path.join(self.temp_dir.name, 'SimulatorBanka.json')
        self.original_data_file = sb.DATA_FILE
        self.addCleanup(setattr, sb, 'DATA_FILE', self.original_data_file)
        sb.DATA_FILE = self.temp_data_file

    def test_завантаження_даних_за_замовчуванням(self):
        if os.path.exists(self.temp_data_file):
            os.remove(self.temp_data_file)

        data = sb.load_account_data()

        self.assertIn('accounts', data)
        self.assertEqual(len(data['accounts']), 1)
        self.assertEqual(data['microloan_rate'], sb.DEFAULT_MICROLOAN_RATE)
        self.assertEqual(data['accounts'][0]['status'], 'Активний')

    def test_створення_рахунку(self):
        data = {'accounts': [], 'microloan_rate': 12.5}

        account = sb.create_account(data, 'Олена', 10.0, 2500.0)

        self.assertEqual(len(data['accounts']), 1)
        self.assertEqual(account['owner'], 'Олена')
        self.assertEqual(account['transactions'][0]['amount'], 2500.0)
        self.assertEqual(sb.get_current_balance(account), 2500.0)
        self.assertEqual(account['status'], 'Активний')

    def test_поповнення_і_зняття(self):
        data = {'accounts': [], 'microloan_rate': 15.0}
        account = sb.create_account(data, 'Петро', 8.0, 200.0)

        sb.add_transaction(data, account, 'Зняття', 'Комуналка', 300.0, '25.06.2026')

        self.assertEqual(sb.get_current_balance(account), -100.0)
        self.assertEqual(account['status'], 'Заблоковано')
        self.assertEqual(len(account['transactions']), 2)

    def test_робота_з_датами(self):
        parsed = sb.parse_date('25.06.2026')
        self.assertEqual(parsed, date(2026, 6, 25))
        self.assertEqual(sb.format_date(parsed), '25.06.2026')

    def test_виписка_транзакцій(self):
        data = {'accounts': [], 'microloan_rate': 15.0}
        account = sb.create_account(data, 'Ігор', 12.0, 1000.0)
        sb.add_transaction(data, account, 'Поповнення', 'Премія', 300.0, '26.06.2026')
        sb.add_transaction(data, account, 'Зняття', 'Каву', 200.0, '27.06.2026')

        buffer = io.StringIO()
        with patch('builtins.input', side_effect=['01.01.2025', '30.06.2026', '', 'н']), redirect_stdout(buffer):
            sb.print_statement(account)

        output = re.sub(r'\x1b\[[0-9;]*m', '', buffer.getvalue()).upper()
        self.assertIn('ВИПИСКА ТРАНЗАКЦІЙ', output)
        self.assertIn('ВСЬОГО ПОПОВНЕНЬ', output)
        self.assertIn('ВСЬОГО ЗНЯТТІВ', output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
