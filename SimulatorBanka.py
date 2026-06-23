import json
import os
import sys
from datetime import datetime

# Color codes for console output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'

def colored(text, color):
    return f"{color}{text}{Colors.RESET}"

def success(text):
    return colored(text, Colors.GREEN)

def error(text):
    return colored(text, Colors.RED)

def warn(text):
    return colored(text, Colors.YELLOW)

def info(text):
    return colored(text, Colors.CYAN)

def menu_header(text):
    border = colored("═" * 60, Colors.BLUE)
    title = colored(f"  {text.upper()}  ", Colors.BOLD + Colors.BLUE)
    print(f"\n{border}")
    print(title.center(64))
    print(f"{border}\n")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'SimulatorBanka.json')
ADMIN_PASSWORD = '123457'
DEFAULT_MICROLOAN_RATE = 15.0
DEFAULT_ACCOUNT = {
    'owner': 'Іванченко Олексій',
    'account_number': 'UA42-0001-0000-0000-0000',
    'opened': '01.01.2025',
    'status': 'Активний',
    'interest_rate': 12.0,
    'transactions': [
        {
            'date': '01.01.2025',
            'type': 'Поповнення',
            'description': 'Початковий внесок',
            'amount': 5000.00,
            'balance_before': 0.0,
            'balance_after': 5000.0,
        }
    ],
}

DATE_FORMATS = ('%d.%m.%Y', '%Y-%m-%d')


def parse_date(value):
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError('Неправильний формат дати. Використайте дд.мм.рррр або рррр-мм-дд.')


def format_date(date_obj):
    return date_obj.strftime('%d.%m.%Y')


def load_account_data():
    if not os.path.exists(DATA_FILE):
        return initialize_default_data()

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        print('Помилка зчитування файлу. Створюю новий файл даних.')
        return initialize_default_data()

    if isinstance(data, dict) and 'accounts' in data and isinstance(data['accounts'], list):
        pass
    elif isinstance(data, dict) and 'owner' in data:
        data = {'accounts': [data], 'microloan_rate': DEFAULT_MICROLOAN_RATE}
    else:
        print('Файл даних не відповідає очікуваному формату. Відновлюю стандартні дані.')
        return initialize_default_data()

    if 'microloan_rate' not in data:
        data['microloan_rate'] = DEFAULT_MICROLOAN_RATE

    for account in data['accounts']:
        if 'transactions' not in account or not isinstance(account['transactions'], list):
            account['transactions'] = []
        update_balances(account)
        update_account_status(account)

    save_account_data(data)
    return data


def initialize_default_data():
    account = DEFAULT_ACCOUNT.copy()
    account['transactions'] = [DEFAULT_ACCOUNT['transactions'][0].copy()]
    data = {
        'accounts': [account],
        'microloan_rate': DEFAULT_MICROLOAN_RATE,
    }
    update_balances(account)
    update_account_status(account)
    save_account_data(data)
    return data


def save_account_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        print('Не вдалося записати файл:', exc)


def get_current_balance(account):
    if account.get('transactions'):
        return account['transactions'][-1].get('balance_after', 0.0)
    return 0.0


def update_balances(account):
    balance = 0.0
    for tx in account['transactions']:
        amount = float(tx.get('amount', 0.0) or 0.0)
        tx['balance_before'] = round(balance, 2)
        if tx['type'] == 'Зняття':
            balance -= amount
        else:
            balance += amount
        tx['balance_after'] = round(balance, 2)
    return round(balance, 2)


def update_account_status(account):
    balance = get_current_balance(account)
    account['status'] = 'Заблоковано' if balance < 0 else 'Активний'


def generate_account_number(index):
    return f'UA42-{index:04d}-0000-0000-0000'


def add_transaction(data, account, tx_type, description, amount, date_text):
    amount = round(float(amount), 2)
    new_tx = {
        'date': date_text,
        'type': tx_type,
        'description': description,
        'amount': amount,
        'balance_before': 0.0,
        'balance_after': 0.0,
    }
    account['transactions'].append(new_tx)
    update_balances(account)
    update_account_status(account)
    save_account_data(data)


def create_account(data, owner, interest_rate, initial_deposit):
    index = len(data['accounts']) + 1
    account_number = generate_account_number(index)
    open_date = format_date(datetime.today().date())
    transaction_type = 'Поповнення' if initial_deposit > 0 else 'Створено рахунок'
    description = 'Початковий внесок' if initial_deposit > 0 else 'Створено рахунок'
    account = {
        'owner': owner,
        'account_number': account_number,
        'opened': open_date,
        'status': 'Активний',
        'interest_rate': round(float(interest_rate), 2),
        'transactions': [
            {
                'date': open_date,
                'type': transaction_type,
                'description': description,
                'amount': round(float(initial_deposit), 2),
                'balance_before': 0.0,
                'balance_after': round(float(initial_deposit), 2),
            }
        ],
    }
    update_balances(account)
    update_account_status(account)
    data['accounts'].append(account)
    save_account_data(data)
    return account


def input_float(prompt, allow_zero=False):
    while True:
        answer = input(info(prompt)).strip().replace(',', '.')
        try:
            value = float(answer)
            if value < 0 or (value == 0 and not allow_zero):
                msg = 'Введіть додатне число.' if not allow_zero else 'Введіть число більше або рівне нулю.'
                print(warn(msg))
                continue
            return round(value, 2)
        except ValueError:
            print(error('Некоректне число. Спробуйте ще раз.'))


def input_date(prompt):
    while True:
        answer = input(info(prompt)).strip()
        try:
            return parse_date(answer)
        except ValueError as exc:
            print(error(str(exc)))


def select_account(data):
    while True:
        if not data['accounts']:
            print(error('✗ Немає рахунків. Створіть новий рахунок.'))
            create_new_account(data)
            continue

        menu_header('Вибір рахунку')
        for idx, account in enumerate(data['accounts'], 1):
            balance = get_current_balance(account)
            status_color = Colors.GREEN if account['status'] == 'Активний' else Colors.RED
            print(f"  {info(str(idx))}. {account['owner']} — {info(account['account_number'])} | Баланс: {success(f'{balance:.2f} ₴')} | {colored(account['status'], status_color)}")
        choice = input(f"\n{colored('Виберіть рахунок: ', Colors.BOLD)}").strip()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(data['accounts']):
                return data['accounts'][index - 1]
        print(error('✗ Некоректний вибір. Спробуйте ще раз.'))


def deposit_cash(data, account):
    while True:
        if account['status'] == 'Заблоковано':
            print(warn('\n⚠ Рахунок заблоковано, але поповнення можливе для розблокування.'))
        amount = input_float('Сума поповнення (₴): ')
        description = input(info('Опис поповнення: ')).strip() or 'Поповнення'
        date_text = format_date(datetime.today().date())
        add_transaction(data, account, 'Поповнення', description, amount, date_text)
        print(success(f'✓ Готово. Поповнено {amount:.2f} ₴.'))
        if not prompt_repeat_action('поповнення'):
            break


def withdraw_cash(data, account):
    while True:
        if account['status'] == 'Заблоковано':
            print(error('✗ Рахунок заблоковано. Зняття неможливе, поки баланс від\'ємний.'))
            break
        amount = input_float('Сума зняття (₴): ')
        description = input(info('Опис зняття: ')).strip() or 'Зняття'
        date_text = format_date(datetime.today().date())
        add_transaction(data, account, 'Зняття', description, amount, date_text)
        balance = get_current_balance(account)
        status_color = Colors.GREEN if balance >= 0 else Colors.RED
        status = 'активний' if balance >= 0 else 'заблоковано'
        print(success(f'✓ Знято {amount:.2f} ₴.'))
        print(info(f'  Баланс: {balance:.2f} ₴') + f' | {colored(status.upper(), status_color)}')
        if not prompt_repeat_action('зняття'):
            break


def calculate_interest(data, account):
    while True:
        balance = get_current_balance(account)
        if balance <= 0:
            print(error('✗ Відсотки нараховуються лише на додатний баланс.'))
            print(info('  Виконайте поповнення, щоб отримати відсотки.'))
            break
        days = input_float('Кількість днів для нарахування відсотків: ')
        rate = account.get('interest_rate', DEFAULT_ACCOUNT['interest_rate'])
        interest = round(balance * rate / 100 * days / 365, 2)
        if interest == 0:
            print(warn('⚠ Нараховані відсотки = 0.0. Баланс або дні недостатні для нарахування.'))
            break
        description = f'Нараховані {rate:.2f}% за {int(days)} днів'
        date_text = format_date(datetime.today().date())
        add_transaction(data, account, 'Відсотки', description, interest, date_text)
        print(success(f'✓ Нараховано {interest:.2f} ₴ відсотків.'))
        if not prompt_repeat_action('нарахування відсотків'):
            break


def microloan_menu(data, account):
    menu_header('Мікрозайм')
    print(info('  1. • 100 ₴'))
    print(info('  2. • 500 ₴'))
    print(info('  3. • 1000 ₴'))
    print(colored('  0. • Скасувати', Colors.RED))
    while True:
        choice = input(f"\n{colored('Виберіть суму: ', Colors.BOLD)}").strip()
        if choice == '1':
            amount = 100
            break
        if choice == '2':
            amount = 500
            break
        if choice == '3':
            amount = 1000
            break
        if choice == '0':
            return
        print(error('✗ Некоректний вибір. Введіть 1, 2 або 3.'))

    rate = data.get('microloan_rate', DEFAULT_MICROLOAN_RATE)
    description = f'Мікрозайм {amount} ₴ під {rate:.2f}%'
    date_text = format_date(datetime.today().date())
    add_transaction(data, account, 'Мікрозайм', description, amount, date_text)
    print(success(f'✓ Надано мікрозайм {amount} ₴ під ставку {rate:.2f}%.'))


def print_statement(account):
    while True:
        menu_header('Виписка транзакцій')
        start_date = input_date('Початкова дата (дд.мм.рррр): ')
        end_date = input_date('Кінцева дата (дд.мм.рррр): ')
        if start_date > end_date:
            print(error('✗ Початкова дата не може бути пізнішою за кінцеву.'))
            continue

        filtered = []
        for tx in account['transactions']:
            try:
                tx_date = parse_date(tx['date'])
            except ValueError:
                continue
            if start_date <= tx_date <= end_date:
                filtered.append(tx)

        if not filtered:
            print(warn('⚠ Транзакцій за вказаний період не знайдено.'))
        else:
            print(info('\n  Виписка за період:'))
            print(colored('  ' + '─' * 80, Colors.BLUE))
            print(f"  {colored('Дата', Colors.BOLD):<12}{colored('Тип', Colors.BOLD):<14}{colored('Опис', Colors.BOLD):<24}{colored('Сума', Colors.BOLD):>10}{colored('Баланс до', Colors.BOLD):>14}{colored('Баланс після', Colors.BOLD):>16}")
            print(colored('  ' + '─' * 80, Colors.BLUE))
            for tx in filtered:
                description = tx.get('description', '')[:22]
                print(f"  {tx['date']:<12}{tx['type']:<14}{description:<24}{tx['amount']:>10.2f}{tx['balance_before']:>14.2f}{tx['balance_after']:>16.2f}")
            print(colored('  ' + '─' * 80, Colors.BLUE))
            total_in = sum(tx['amount'] for tx in filtered if tx['type'] == 'Поповнення')
            total_out = sum(tx['amount'] for tx in filtered if tx['type'] == 'Зняття')
            total_interest = sum(tx['amount'] for tx in filtered if tx['type'] == 'Відсотки')
            print(success(f'  Всього поповнень: {total_in:.2f} ₴'))
            print(colored(f'  Всього зняттів:    {total_out:.2f} ₴', Colors.MAGENTA))
            print(colored(f'  Всього відсотків:  {total_interest:.2f} ₴', Colors.YELLOW))

        input(info('\n  Натисніть Enter, щоб повернутися до меню...'))
        if not prompt_repeat_action('виписку транзакцій'):
            break


def prompt_repeat_action(action_name):
    while True:
        answer = input(f'\nБажаєте повторити {action_name}? (Д/Н): ').strip().lower()
        if answer in ('д', 'да', 'y', 'yes'):
            return True
        if answer in ('н', 'ні', 'n', 'no'):
            return False
        print('Введіть Д для повтору або Н для повернення до меню.')


def show_balance_info(account):
    balance = get_current_balance(account)
    rate = account.get('interest_rate', DEFAULT_ACCOUNT['interest_rate'])
    projected = round(balance * rate / 100 * 30 / 365, 2) if balance > 0 else 0.0
    menu_header('Перевірка балансу')
    print(info(f"  Поточний баланс: {success(f'{balance:.2f} ₴')}"))
    status_color = Colors.GREEN if account.get('status') == 'Активний' else Colors.RED
    print(info(f"  Статус рахунку: {colored(account.get('status'), status_color)}"))
    print(info(f"  Річна ставка: {colored(f'{rate:.2f}%', Colors.YELLOW)}"))
    print(info(f"  Прогнозні відсотки за 30 днів: {colored(f'{projected:.2f} ₴', Colors.MAGENTA)}"))
    input(info('\n  Натисніть Enter, щоб повернутися до меню...'))


def show_account_info(account):
    balance = get_current_balance(account)
    menu_header('Інформація про рахунок')
    print(info(f"  Власник: {colored(account.get('owner'), Colors.BOLD)}"))
    print(info(f"  Номер рахунку: {colored(account.get('account_number'), Colors.CYAN)}"))
    print(info(f"  Відкрито: {colored(account.get('opened'), Colors.YELLOW)}"))
    status_color = Colors.GREEN if account.get('status') == 'Активний' else Colors.RED
    print(info(f"  Статус: {colored(account.get('status'), status_color)}"))
    print(info(f"  Поточний баланс: {success(f'{balance:.2f} ₴')}"))
    rate = account.get('interest_rate')
    print(info(f"  Річна ставка: {colored(f'{rate:.2f}%', Colors.YELLOW)}"))
    print(info(f"  Кількість транзакцій: {colored(str(len(account.get('transactions', []))), Colors.MAGENTA)}"))
    input(info('\n  Натисніть Enter, щоб повернутися до меню...'))


def create_new_account(data):
    menu_header('Створення нового рахунку')
    while True:
        owner = input(info('Ім\'я власника рахунку: ')).strip()
        if owner:
            break
        print(error('✗ Ім\'я не може бути порожнім.'))
    interest_rate = input_float('Річна ставка рахунку (%): ')
    initial_deposit = input_float('Початковий внесок (₴): ', allow_zero=True)
    account = create_account(data, owner, interest_rate, initial_deposit)
    print(success(f'✓ Рахунок створено: {colored(account["account_number"], Colors.CYAN)}'))
    print(info(f'  Власник: {account["owner"]} | Баланс: {success(f"{initial_deposit:.2f} ₴")}'))


def list_accounts(data):
    menu_header('Список усіх рахунків')
    for idx, account in enumerate(data['accounts'], 1):
        balance = get_current_balance(account)
        status_color = Colors.GREEN if account['status'] == 'Активний' else Colors.RED
        rate = account.get('interest_rate')
        print(f"  {info(str(idx))}. {account['owner']} — {colored(account['account_number'], Colors.CYAN)} | Баланс: {success(f'{balance:.2f} ₴')} | {colored(account['status'], status_color)} | Ставка: {colored(f'{rate:.2f}%', Colors.YELLOW)}")


def set_microloan_rate(data):
    menu_header('Установка ставки мікрозайму')
    rate = input_float('Встановіть процентну ставку для мікрозайму (%): ')
    data['microloan_rate'] = round(rate, 2)
    save_account_data(data)
    print(success(f'✓ Ставка для мікрозайму встановлена на {colored(f"{data["microloan_rate"]:.2f}%", Colors.YELLOW)}'))


def select_user_or_admin(data):
    while True:
        menu_header('Вибір ролі')
        print(info('  1. • Користувач'))
        print(warn('  2. • Адміністратор'))
        print(colored('  0. • Вихід', Colors.RED))
        choice = input(f"\n{colored('Виберіть роль: ', Colors.BOLD)}").strip()
        if choice == '1':
            return 'user', select_account(data)
        if choice == '2':
            password = input(info('Введіть пароль адміністратора: ')).strip()
            if password == ADMIN_PASSWORD:
                return 'admin', None
            print(error('✗ Невірний пароль. Спробуйте ще раз.'))
            continue
        if choice == '0':
            return None, None
        print(error('✗ Некоректний вибір. Введіть 0, 1 або 2.'))


def user_menu(data, account):
    while True:
        balance = get_current_balance(account)
        status_color = Colors.GREEN if account.get('status') == 'Активний' else Colors.RED
        menu_header(f"Меню користувача: {account['owner']}")
        print(f"  {account['account_number']} | {success(f'{balance:.2f} ₴')} | {colored(account.get('status'), status_color)}\n")
        print(success('  1. • Поповнення рахунку'))
        print(colored('  2. • Зняття коштів', Colors.MAGENTA))
        print(info('  3. • Перевірка балансу'))
        print(colored('  4. • Нарахування відсотків', Colors.YELLOW))
        print(warn('  5. • Мікрозайм'))
        print(info('  6. • Виписка транзакцій'))
        print(info('  7. • Інформація про рахунок'))
        print(colored('  0. • Повернутися до вибору ролі', Colors.RED))
        choice = input(f"\n{colored('Виберіть дію: ', Colors.BOLD)}").strip()
        if choice == '1':
            deposit_cash(data, account)
        elif choice == '2':
            withdraw_cash(data, account)
        elif choice == '3':
            show_balance_info(account)
        elif choice == '4':
            calculate_interest(data, account)
        elif choice == '5':
            microloan_menu(data, account)
        elif choice == '6':
            print_statement(account)
        elif choice == '7':
            show_account_info(account)
        elif choice == '0':
            break
        else:
            print(error('✗ Некоректний вибір. Введіть число від 0 до 7.'))


def admin_menu(data):
    while True:
        menu_header('Меню адміністратора')
        print(warn('  1. • Додати нового користувача'))
        print(colored('  2. • Встановити ставку мікрозайму', Colors.YELLOW))
        print(info('  3. • Переглянути всі рахунки'))
        print(colored('  0. • Повернутися до вибору ролі', Colors.RED))
        choice = input(f"\n{colored('Виберіть дію: ', Colors.BOLD)}").strip()
        if choice == '1':
            create_new_account(data)
        elif choice == '2':
            set_microloan_rate(data)
        elif choice == '3':
            list_accounts(data)
        elif choice == '0':
            break
        else:
            print(error('✗ Некоректний вибір. Введіть число від 0 до 3.'))


def main():
    data = load_account_data()
    print(colored(f"\n{'═' * 60}", Colors.BLUE))
    print(colored("  ПРИВІТ! ЦЕ СИМУЛЯТОР БАНКУ  ".upper(), Colors.BOLD + Colors.BLUE).center(64))
    print(colored(f"{'═' * 60}\n", Colors.BLUE))
    while True:
        role, account = select_user_or_admin(data)
        if role is None:
            print(success('\n✓ Дякуємо за відвідування!'))
            print(info(f'  Дані збережено у файлі: {DATA_FILE}'))
            break
        if role == 'admin':
            admin_menu(data)
        else:
            user_menu(data, account)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nРоботу перервано користувачем. Дані збережено.')
        sys.exit(0)
