import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, ttk
from datetime import datetime

from SimulatorBanka import (
    add_transaction,
    get_current_balance,
    load_account_data,
    parse_date,
    format_date,
    create_account,
    save_account_data,
    ADMIN_PASSWORD,
)


def refresh_status():
    balance = get_current_balance(account)
    status_emoji = '✅' if account['status'] == 'Активний' else '❌'
    status_label.config(
        text=f"{status_emoji} {account['owner']} | {account['account_number']} | 💰 {balance:.2f} ₴ | Ставка: {account['interest_rate']:.2f}%"
    )


def append_log(text):
    log_text.config(state='normal')
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_text.insert(tk.END, f'[{timestamp}] {text}\n')
    log_text.see(tk.END)
    log_text.config(state='disabled')


def select_account(data):
    accounts = data.get('accounts', [])
    if not accounts:
        messagebox.showerror('Помилка', 'Немає доступних рахунків.')
        root.destroy()
        return None

    if len(accounts) == 1:
        return accounts[0]

    options = [f"{idx + 1}. {acc['owner']} — {acc['account_number']}" for idx, acc in enumerate(accounts)]
    option_text = 'Оберіть рахунок:\n' + '\n'.join(options)
    while True:
        choice = simpledialog.askinteger('Оберіть рахунок', option_text, minvalue=1, maxvalue=len(accounts))
        if choice is None:
            return None
        if 1 <= choice <= len(accounts):
            return accounts[choice - 1]
        messagebox.showwarning('Невірний вибір', 'Введіть правильний номер рахунку.')


def role_selection_dialog(data):
    dlg = tk.Toplevel()
    dlg.title('Симулятор Банку — Вибір ролі')
    dlg.geometry('400x220')
    dlg.resizable(False, False)
    dlg.configure(bg='#ecf0f1')
    role = {'value': None}

    # Header
    header_frame = tk.Frame(dlg, bg='#3498db', height=60)
    header_frame.pack(fill='x')
    header_label = tk.Label(header_frame, text='🏦 СИМУЛЯТОР БАНКУ', font=('Segoe UI', 14, 'bold'), fg='white', bg='#3498db', pady=10)
    header_label.pack()

    # Content frame
    content_frame = tk.Frame(dlg, bg='#ecf0f1')
    content_frame.pack(fill='both', expand=True, padx=20, pady=20)

    lbl = tk.Label(content_frame, text='Оберіть роль для входу:', font=('Segoe UI', 11), fg='#2c3e50', bg='#ecf0f1')
    lbl.pack(pady=(0, 16))

    def choose_user():
        role['value'] = 'user'
        dlg.destroy()

    def choose_admin():
        pwd = simpledialog.askstring('Адміністратор', 'Введіть пароль:', show='*', parent=dlg)
        if pwd is None:
            return
        if pwd == ADMIN_PASSWORD:
            role['value'] = 'admin'
            dlg.destroy()
        else:
            messagebox.showerror('Помилка', 'Невірний пароль!', parent=dlg)

    btn_user = tk.Button(content_frame, text='👤 Користувач', command=choose_user, font=('Segoe UI', 11, 'bold'), 
                         bg='#27ae60', fg='white', padx=20, pady=10, relief='flat', cursor='hand2', activebackground='#229954')
    btn_user.pack(fill='x', pady=6)

    btn_admin = tk.Button(content_frame, text='🔐 Адміністратор', command=choose_admin, font=('Segoe UI', 11, 'bold'), 
                         bg='#e74c3c', fg='white', padx=20, pady=10, relief='flat', cursor='hand2', activebackground='#c0392b')
    btn_admin.pack(fill='x', pady=6)

    dlg.transient(root)
    dlg.grab_set()
    root.wait_window(dlg)
    return role['value']


def admin_window(data):
    aw = tk.Toplevel(root)
    aw.title('Симулятор Банку — Адміністраторська панель')
    aw.geometry('520x360')
    aw.resizable(False, False)
    aw.configure(bg='#ecf0f1')

    # Header
    header_frame = tk.Frame(aw, bg='#c0392b', height=60)
    header_frame.pack(fill='x')
    header_label = tk.Label(header_frame, text='🔐 АДМІНІСТРАТОРСЬКА ПАНЕЛЬ', font=('Segoe UI', 13, 'bold'), fg='white', bg='#c0392b', pady=10)
    header_label.pack()

    # Content frame
    content_frame = tk.Frame(aw, bg='#ecf0f1')
    content_frame.pack(fill='both', expand=True, padx=20, pady=20)

    def gui_create_account():
        owner = simpledialog.askstring('Новий рахунок', "Ім'я власника:", parent=aw)
        if not owner:
            return
        rate = simpledialog.askfloat('Новий рахунок', 'Річна ставка (%):', minvalue=0.0, parent=aw)
        if rate is None:
            return
        deposit = simpledialog.askfloat('Новий рахунок', 'Початковий внесок (₴):', minvalue=0.0, parent=aw)
        if deposit is None:
            return
        create_account(data, owner, rate, deposit)
        messagebox.showinfo('Готово', f'✓ Рахунок створено для {owner}', parent=aw)

    def gui_set_microloan():
        rate = simpledialog.askfloat('Ставка мікрозайму', 'Процентна ставка (%):', minvalue=0.0, parent=aw)
        if rate is None:
            return
        data['microloan_rate'] = round(rate, 2)
        save_account_data(data)
        messagebox.showinfo('Готово', f'✓ Ставка для мікрозайму встановлена на {data["microloan_rate"]:.2f}%', parent=aw)

    def gui_list_accounts():
        lines = []
        for idx, acc in enumerate(data.get('accounts', []), 1):
            bal = get_current_balance(acc)
            lines.append(f"{idx}. {acc['owner']} — {acc['account_number']} | {bal:.2f} ₴ | {acc.get('status')}")
        messagebox.showinfo('Список рахунків', '\n'.join(lines) if lines else 'Рахунків немає', parent=aw)

    label = tk.Label(content_frame, text='Оберіть дію:', font=('Segoe UI', 11, 'bold'), fg='#2c3e50', bg='#ecf0f1')
    label.pack(pady=(0, 12))

    btn1 = tk.Button(content_frame, text='➕ Додати нового користувача', command=gui_create_account, 
                     font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='white', padx=20, pady=10, relief='flat', cursor='hand2', activebackground='#229954')
    btn1.pack(fill='x', pady=6)

    btn2 = tk.Button(content_frame, text='📊 Встановити ставку мікрозайму', command=gui_set_microloan, 
                     font=('Segoe UI', 11, 'bold'), bg='#f39c12', fg='white', padx=20, pady=10, relief='flat', cursor='hand2', activebackground='#d68910')
    btn2.pack(fill='x', pady=6)

    btn3 = tk.Button(content_frame, text='📋 Переглянути всі рахунки', command=gui_list_accounts, 
                     font=('Segoe UI', 11, 'bold'), bg='#3498db', fg='white', padx=20, pady=10, relief='flat', cursor='hand2', activebackground='#2980b9')
    btn3.pack(fill='x', pady=6)

    btn_close = tk.Button(content_frame, text='❌ Закрити', command=aw.destroy, 
                         font=('Segoe UI', 11, 'bold'), bg='#e74c3c', fg='white', padx=20, pady=10, relief='flat', cursor='hand2', activebackground='#c0392b')
    btn_close.pack(fill='x', pady=12)

    aw.transient(root)
    aw.grab_set()
    root.wait_window(aw)


def deposit():
    if account['status'] == 'Заблоковано':
        messagebox.showinfo('Поповнення', '⚠️ Рахунок заблоковано, але поповнення розблокує його.')
    amount = simpledialog.askfloat('Поповнення', 'Сума поповнення (₴):', minvalue=0.01)
    if amount is None:
        return
    description = simpledialog.askstring('Поповнення', 'Опис поповнення:', initialvalue='Поповнення')
    if description is None:
        return
    add_transaction(data, account, 'Поповнення', description.strip() or 'Поповнення', round(amount, 2), format_date(datetime.today().date()))
    append_log(f'✅ Поповнено: {amount:.2f} ₴ — {description.strip() or "Поповнення"}')
    refresh_status()


def withdraw():
    if account['status'] == 'Заблоковано':
        messagebox.showwarning('Зняття', '❌ Рахунок заблоковано. Зняття неможливе, доки баланс від\'ємний.')
        return
    amount = simpledialog.askfloat('Зняття', 'Сума зняття (₴):', minvalue=0.01)
    if amount is None:
        return
    description = simpledialog.askstring('Зняття', 'Опис зняття:', initialvalue='Зняття')
    if description is None:
        return
    add_transaction(data, account, 'Зняття', description.strip() or 'Зняття', round(amount, 2), format_date(datetime.today().date()))
    balance = get_current_balance(account)
    append_log(f'❌ Знято: {amount:.2f} ₴ — {description.strip() or "Зняття"} | Баланс: {balance:.2f} ₴')
    refresh_status()


def calculate_interest_gui():
    balance = get_current_balance(account)
    if balance <= 0:
        messagebox.showinfo('Відсотки', '❌ Відсотки нараховуються лише на додатний баланс.')
        return
    days = simpledialog.askinteger('Нарахування відсотків', 'Кількість днів для нарахування:', minvalue=1)
    if days is None:
        return
    rate = account.get('interest_rate', 0.0)
    interest = round(balance * rate / 100 * days / 365, 2)
    if interest <= 0:
        messagebox.showinfo('Відсотки', '⚠️ Нараховані відсотки = 0. Спробуйте інший період.')
        return
    description = f'Нараховані {rate:.2f}% за {days} днів'
    add_transaction(data, account, 'Відсотки', description, interest, format_date(datetime.today().date()))
    append_log(f'📈 Нараховано відсотків: {interest:.2f} ₴ ({rate:.2f}% за {days} днів)')
    refresh_status()


def microloan():
    rate = data.get('microloan_rate', 0.0)
    choice = simpledialog.askinteger('Мікрозайм', 'Оберіть суму мікрозайму:\n1. 100 ₴\n2. 500 ₴\n3. 1000 ₴', minvalue=1, maxvalue=3)
    if choice is None:
        return
    amount = {1: 100, 2: 500, 3: 1000}.get(choice)
    if amount is None:
        messagebox.showwarning('Невірний вибір', 'Оберіть 1, 2 або 3.')
        return
    description = f'Мікрозайм {amount} ₴ під {rate:.2f}%'
    add_transaction(data, account, 'Мікрозайм', description, amount, format_date(datetime.today().date()))
    append_log(f'💳 Взято мікрозайм: {amount:.2f} ₴ під {rate:.2f}%')
    refresh_status()


def show_balance():
    balance = get_current_balance(account)
    status_emoji = '✅' if account.get('status') == 'Активний' else '❌'
    messagebox.showinfo('💵 Баланс', f'💰 Поточний баланс: {balance:.2f} ₴\n{status_emoji} Статус: {account.get("status")}')
    append_log(f'📊 Перевірена інформація про баланс: {balance:.2f} ₴')


def show_info():
    balance = get_current_balance(account)
    status_emoji = '✅' if account.get('status') == 'Активний' else '❌'
    info_text = (
        f"👤 Власник: {account.get('owner')}\n"
        f"🔢 Номер рахунку: {account.get('account_number')}\n"
        f"📅 Відкрито: {account.get('opened')}\n"
        f"{status_emoji} Статус: {account.get('status')}\n"
        f"💰 Поточний баланс: {balance:.2f} ₴\n"
        f"📈 Річна ставка: {account.get('interest_rate'):.2f}%\n"
        f"📋 Транзакцій: {len(account.get('transactions', []))}\n"
        f"💳 Ставка мікрозайму: {data.get('microloan_rate', 0.0):.2f}%"
    )
    messagebox.showinfo('ℹ️ Інформація про рахунок', info_text)
    append_log('📌 Переглянута детальна інформація про рахунок')


def statement():
    start_text = simpledialog.askstring('Виписка', 'Початкова дата (дд.мм.рррр):')
    if start_text is None:
        return
    end_text = simpledialog.askstring('Виписка', 'Кінцева дата (дд.мм.рррр):')
    if end_text is None:
        return
    try:
        start_date = parse_date(start_text)
        end_date = parse_date(end_text)
    except ValueError as exc:
        messagebox.showerror('Помилка дати', str(exc))
        return
    if start_date > end_date:
        messagebox.showerror('Помилка', 'Початкова дата не може бути пізнішою за кінцеву.')
        return
    filtered = [tx for tx in account['transactions'] if start_date <= parse_date(tx['date']) <= end_date]
    if not filtered:
        messagebox.showinfo('Виписка', 'Транзакцій за вказаний період не знайдено.')
        return
    lines = [
        'Дата | Тип | Опис | Сума | Баланс до | Баланс після',
        '-' * 72,
    ]
    for tx in filtered:
        lines.append(
            f"{tx['date']} | {tx['type']} | {tx.get('description','')[:20]} | {tx['amount']:.2f} | {tx['balance_before']:.2f} | {tx['balance_after']:.2f}"
        )
    summary = (
        f"\nВсього поповнень: {sum(tx['amount'] for tx in filtered if tx['type'] == 'Поповнення'):.2f} ₴\n"
        f"Всього зняттів: {sum(tx['amount'] for tx in filtered if tx['type'] == 'Зняття'):.2f} ₴\n"
        f"Всього відсотків: {sum(tx['amount'] for tx in filtered if tx['type'] == 'Відсотки'):.2f} ₴"
    )
    messagebox.showinfo('Виписка транзакцій', '\n'.join(lines) + summary)


def on_close():
    root.destroy()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def back_to_role_selection():
    script = os.path.join(BASE_DIR, 'startup.pyw')
    try:
        subprocess.Popen(['py', '-3', script])
    except Exception:
        try:
            subprocess.Popen([sys.executable, script])
        except Exception as exc:
            messagebox.showerror('Помилка', f'Не вдалось запустити вибір ролі: {exc}')
            return
    root.destroy()
    sys.exit(0)


data = load_account_data()

root = tk.Tk()
root.title('💰 Симулятор Банківського Рахунку')
root.geometry('900x820')
root.resizable(False, False)
root.configure(bg='#f0f0f0')

role = role_selection_dialog(data)
if role is None:
    root.destroy()
    sys.exit(0)
if role == 'admin':
    # open admin window and then exit
    admin_window(data)
    root.destroy()
    sys.exit(0)

account = select_account(data)
if account is None:
    root.destroy()
    sys.exit(0)

style = ttk.Style(root)
style.theme_use('clam')

# Define color palette
BG_COLOR = '#f0f0f0'
FG_COLOR = '#2c3e50'
PRIMARY_COLOR = '#3498db'
SUCCESS_COLOR = '#27ae60'
WARNING_COLOR = '#f39c12'
DANGER_COLOR = '#e74c3c'
INFO_COLOR = '#16a085'

# Configure theme colors
style.configure('TButton', font=('Segoe UI', 10), padding=8)
style.configure('TLabel', font=('Segoe UI', 10), background=BG_COLOR, foreground=FG_COLOR)
style.configure('Header.TLabel', font=('Segoe UI', 13, 'bold'), background=BG_COLOR, foreground=PRIMARY_COLOR)
style.configure('Section.TLabel', font=('Segoe UI', 10, 'bold'), background=BG_COLOR, foreground=INFO_COLOR)
style.configure('TFrame', background=BG_COLOR)
style.configure('TLabelframe', background=BG_COLOR, foreground=FG_COLOR)
style.configure('TLabelframe.Label', background=BG_COLOR, foreground=FG_COLOR)

# Custom button styles
style.configure('Deposit.TButton', font=('Segoe UI', 10, 'bold'), foreground=SUCCESS_COLOR)
style.configure('Withdraw.TButton', font=('Segoe UI', 10, 'bold'), foreground=DANGER_COLOR)
style.configure('Info.TButton', font=('Segoe UI', 10, 'bold'), foreground=PRIMARY_COLOR)
style.configure('Warning.TButton', font=('Segoe UI', 10, 'bold'), foreground=WARNING_COLOR)
style.configure('Close.TButton', font=('Segoe UI', 10, 'bold'), foreground=DANGER_COLOR)

frame = ttk.Frame(root, padding=16)
frame.pack(fill='both', expand=True)

status_label = ttk.Label(frame, text='', style='Header.TLabel', anchor='center')
status_label.pack(fill='x', pady=(0, 16))

# Operation buttons frame
operations_frame = ttk.LabelFrame(frame, text='💰 Операції з рахунком', padding=10)
operations_frame.pack(fill='x', pady=(0, 10))

btn_deposit = ttk.Button(operations_frame, text='➕ Поповнення', command=deposit, style='Deposit.TButton')
btn_deposit.grid(row=0, column=0, padx=6, pady=6, sticky='ew')

btn_withdraw = ttk.Button(operations_frame, text='➖ Зняття', command=withdraw, style='Withdraw.TButton')
btn_withdraw.grid(row=0, column=1, padx=6, pady=6, sticky='ew')

btn_interest = ttk.Button(operations_frame, text='📈 Відсотки', command=calculate_interest_gui, style='Warning.TButton')
btn_interest.grid(row=0, column=2, padx=6, pady=6, sticky='ew')

for i in range(3):
    operations_frame.columnconfigure(i, weight=1)

# Information buttons frame
info_frame = ttk.LabelFrame(frame, text='ℹ️ Інформація', padding=10)
info_frame.pack(fill='x', pady=(0, 10))

btn_balance = ttk.Button(info_frame, text='💵 Баланс', command=show_balance, style='Info.TButton')
btn_balance.grid(row=0, column=0, padx=6, pady=6, sticky='ew')

btn_statement = ttk.Button(info_frame, text='📋 Виписка', command=statement, style='Info.TButton')
btn_statement.grid(row=0, column=1, padx=6, pady=6, sticky='ew')

btn_info = ttk.Button(info_frame, text='📌 Інформація', command=show_info, style='Info.TButton')
btn_info.grid(row=0, column=2, padx=6, pady=6, sticky='ew')

for i in range(3):
    info_frame.columnconfigure(i, weight=1)

# Microloan frame
loan_frame = ttk.LabelFrame(frame, text='🏦 Мікрозайм', padding=10)
loan_frame.pack(fill='x', pady=(0, 10))

btn_microloan = ttk.Button(loan_frame, text='💳 Отримати мікрозайм', command=microloan, style='Warning.TButton')
btn_microloan.pack(fill='x', padx=6, pady=6)

separator = ttk.Separator(frame, orient='horizontal')
separator.pack(fill='x', pady=8)

log_label = ttk.Label(frame, text='📝 Журнал дій:', style='Section.TLabel', anchor='w')
log_label.pack(fill='x', pady=(4, 4))

log_text = scrolledtext.ScrolledText(frame, state='disabled', width=110, height=14, wrap='word', font=('Segoe UI', 9), bg='#f9f9f9', fg=FG_COLOR)
log_text.pack(fill='both', expand=True, pady=(0, 10))

# Bottom buttons frame
button_frame = ttk.Frame(frame)
button_frame.pack(fill='x', padx=0, pady=8)

back_button = ttk.Button(button_frame, text='↩️ Вибір ролі', command=back_to_role_selection, style='Info.TButton')
back_button.pack(side='left', padx=(0, 10), fill='x', expand=True)

close_button = ttk.Button(button_frame, text='❌ Вихід', command=on_close, style='Close.TButton')
close_button.pack(side='right', fill='x', expand=True)

refresh_status()
append_log('✅ Симулятор готовий. Натисніть кнопку для виконання дії.')
append_log('📌 Виберіть операцію з меню вище.')
root.protocol('WM_DELETE_WINDOW', on_close)
root.mainloop()
