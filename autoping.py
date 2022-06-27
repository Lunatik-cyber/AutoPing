import os
import time

try:
    import requests
    import ping3
    from requests.auth import HTTPProxyAuth
    from rich import print as rprint
    from peewee import *
except ImportError:
    rprint('Начинаю процесс установки недостающих библеотек...')
    os.system('python -m pip install rich ping3 requests requests[socks] peewee')
    rprint('Установка завершена!')
    rprint('Перезапустите скрипт!')
    exit()

db = SqliteDatabase(r'database.db')


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def timeout():
    data = settings.select().where(settings.id == 1).get()
    num_of_secs = int(data.wait_time)
    while num_of_secs:
        m, s = divmod(num_of_secs, 60)
        min_sec_format = '{:02d}:{:02d}'.format(m, s)
        print('\r============== Таймаут: {} ==============='.format(min_sec_format),
              end='')
        time.sleep(1)
        num_of_secs -= 1
    rprint('\r=============================================')


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

class settings(Model):
    id = AutoField(primary_key=True)
    ping_retry = IntegerField(default=3)
    wait_time = CharField(null=True, default='60')
    token = CharField(null=True)
    chat_id = CharField(null=True)
    proxy_server = CharField(null=True)
    proxy_port = CharField(null=True)
    proxy_login = CharField(null=True)
    proxy_password = CharField(null=True)
    proxy_type = CharField(null=True)
    proxy_enabled = BooleanField(default=False)
    proxy_auth_enabled = BooleanField(default=False)

    class Meta:
        database = db


class servers(Model):
    id = AutoField(primary_key=True)
    server_address = CharField(null=True)

    class Meta:
        database = db


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


def clear_base():
    clear()
    try:
        for ip in servers.select():
            rprint('Удаляем сервер: ' + str(ip.server_address))
            ip.delete_instance()
        rprint('База очищена!')
        input('Нажмите Enter для продолжения...')
        main_menu()
    except Exception as e:
        rprint(e)


def delete_server():
    clear()
    for ip in servers.select():
        rprint(f'{ip}) {ip.ip}')
    rprint('Введите по нумерации в формате [ 1 | 1, 2 ]')
    ids = input('>>> ')
    try:
        for ids in ids.replace(' ', '').split(','):
            ip = servers.select().where(servers.id == ids).get()
            servers.get(servers.id == ids).delete_instance()
            rprint(f'{ids}) {ip.server_address} | Удален!')
    except DoesNotExist:
        rprint(f'Ошибка, такого сервера не существует!')
    input('Нажмите Enter для продолжения...')
    main_menu()


def add_server():
    clear()
    rprint('Разрешается вводить сразу нескольно через запятую.\n')
    ip = input('>>> ')
    for ip in ip.replace(' ', '').split(','):
        try:
            checkIP = servers.select().where(servers.server_address == ip).get()
        except DoesNotExist:
            checkIP = None
        if ip == checkIP:
            rprint(f'[bright_red]Такой уже существует![/bright_red]')
        else:
            servers.create(server_address=ip)
            rprint(f'{ip} | Добавлен!')
    input('Нажмите Enter для продолжения...')
    main_menu()


def send_ip(ip):
    try:
        data = settings.select().where(settings.id == 1).get()
        if data.proxy_enabled:
            proxies = {f"{data.proxy_type}": f"{data.proxy_server}:{data.proxy_port}"}
            if data.proxy_auth_enabled:
                auth = HTTPProxyAuth(data.proxy_login, data.proxy_password)
                URL = 'https://api.telegram.org/bot' + data.token + '/sendMessage'
                data = {'chat_id': data.chat_id, 'text': f'IP: <code>{ip}</code> не работает!\n',
                        'parse_mode': 'HTML'}
                requests.post(URL, proxies=proxies, data=data, auth=auth)
            else:
                URL = 'https://api.telegram.org/bot' + data.token + '/sendMessage'
                data = {'chat_id': data.chat_id, 'text': f'IP: <code>{ip}</code> не работает!\n',
                        'parse_mode': 'HTML'}
                requests.post(URL, proxies=proxies, data=data)
        else:
            URL = 'https://api.telegram.org/bot' + data.token + '/sendMessage'
            data = {'chat_id': data.chat_id, 'text': f'IP: <code>{ip}</code> не работает!\n',
                    'parse_mode': 'HTML'}
            requests.post(URL, data=data)
    except requests.exceptions.ConnectionError:
        rprint('[bright_red]Не удалось отправить оповещение![/bright_red]')


def checkPing(ip):
    result = 'None'
    for i in range(settings.select().where(settings.id == 1).get().ping_retry):
        result = ping3.ping(ip)
        result = f'{result}'
        if result == 'None':
            return False
        else:
            result = 'Work'
            return True
    if result == 'None':
        send_ip(ip)
        return False


def check_selected_servers():
    try:
        rprint('Вывожу список серверов:')
        for ip in servers.select():
            rprint(f'{ip}) {ip.ip}')
        rprint('Введите по нумерации в формате [ 1 | 1, 2 ]')
        ids = input('>>> ')
        while True:
            clear()
            rprint('Вывожу список выбранных серверов:\n')
            for ids in ids.replace(' ', '').split(','):
                ip = servers.select().where(servers.id == ids).get()
                rprint(f'{ip.id}) {ip.server_address}')
                rprint('=============================================')
                if checkPing(ip.server_address):
                    rprint(f'{ip.id}) {ip.server_address} | Работает!')
                else:
                    rprint(f'{ip.id}) {ip.server_address} | Не работает!')
                time.sleep(3)
            rprint('=============================================')
            timeout()
    except KeyboardInterrupt:
        pass
    rprint('\nПроверка остановлена!')
    input('Нажмите Enter для продолжения...')
    main_menu()


def check_servers():
    try:
        while True:
            clear()
            rprint('Вывожу список серверов:')
            for ip in servers.select():
                rprint(f'{ip}) {ip.server_address}')
            rprint('Начинаю проверку всех серверов...')
            rprint('=============================================')
            for ip in servers.select():
                if checkPing(ip.server_address):
                    rprint(f'{ip.id}) {ip.server_address} | Работает!')
                else:
                    rprint(f'{ip.id}) {ip.server_address} | Не работает!')
                time.sleep(3)
            rprint('=============================================')
            data = settings.select().where(settings.id == 1).get()
            timeout()
    except KeyboardInterrupt:
        pass
    rprint('\nПроверка остановлена!')
    input('Нажмите Enter для продолжения...')
    main_menu()


def edit_settings():
    clear()
    try:
        data = settings.select().get()
    except DoesNotExist:
        settings.create(id=1,
                        token=None,
                        chat_id=None,
                        proxy_server=None,
                        proxy_port=None,
                        proxy_login=None,
                        proxy_password=None,
                        proxy_type=None,
                        proxy_enabled=False,
                        proxy_auth_enabled=False)
        data = settings.select().get()
    rprint('Текущие данные и настройки:')
    rprint(f'Время ожидания: [bold bright_magenta]'
           f'{"Не настроено" if data.wait_time is None else data.wait_time}[/bold bright_magenta]')
    rprint(f'Кол-во попыток: [bold bright_magenta]'
           f'{"Не настроено" if data.ping_retry is None else data.ping_retry}[/bold bright_magenta]')
    rprint(f'Токен: [bold bright_magenta]'
           f'{"Не настроен" if data.token is None else data.token}[/bold bright_magenta]')
    rprint(f'User ID: [bold bright_magenta]'
           f'{"Не настроен" if data.chat_id is None else data.chat_id}[/bold bright_magenta]')
    rprint(f'Прокси сервер: [bold bright_magenta]'
           f'{"Не настроен" if data.proxy_server is None else data.proxy_server}[/bold bright_magenta]')
    rprint(f'Прокси порт: [bold bright_magenta]'
           f'{"Не настроен" if data.proxy_port is None else data.proxy_port}[/bold bright_magenta]')
    rprint(f'Прокси логин: [bold bright_magenta]'
           f'{"Не настроен" if data.proxy_login is None else data.proxy_login}[/bold bright_magenta]')
    rprint(f'Прокси пароль: [bold bright_magenta]'
           f'{"Не настроен" if data.proxy_password is None else data.proxy_password}[/bold bright_magenta]')
    rprint(f'Прокси тип: [bold bright_magenta]'
           f'{"Не настроен" if data.proxy_type is None else data.proxy_type}[/bold bright_magenta]')
    rprint(f'Прокси: [bold bright_magenta]'
           f'{"Включен" if data.proxy_enabled else "Отключен"}[/bold bright_magenta]')
    rprint(f'Прокси авторизация: [bold bright_magenta]'
           f'{"Включена" if data.proxy_auth_enabled else "Отключена"}[/bold bright_magenta]')
    rprint('=================================================')
    rprint('[bold bright_green]Меню настроек:[/bold bright_green]\n')
    rprint('  1) Изменить время ожидания')
    rprint('  2) Изменить кол-во попыток пинга')
    rprint('  3) Изменить токен')
    rprint('  4) Изменить User ID')
    rprint('  5) Изменить прокси сервер')
    rprint('  6) Изменить прокси порт')
    rprint('  7) Изменить прокси логин')
    rprint('  8) Изменить прокси пароль')
    rprint('  9) Изменить прокси тип')
    rprint('  10) Переключить использование прокси')
    rprint('  11) Переключить прокси авторизацию')
    rprint('  12) Сменить прокси')
    rprint('  13) Вернуться в главное меню')
    rprint('  14) Выйти из скрипта\n')
    choice = input('>>> ')
    if choice == '1':
        clear()
        rprint('Введите новое время ожидания в секундах')
        wait_time = input('>>> ')
        settings.update(wait_time=wait_time).where(settings.id == 1).execute()
        rprint('Время ожидания изменено!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '2':
        clear()
        rprint('Введите новое кол-во попыток пинга')
        ping_retry = input('>>> ')
        settings.update(ping_retry=ping_retry).where(settings.id == 1).execute()
        rprint('Кол-во попыток пинга изменено!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '3':
        clear()
        rprint('Введите новый токен')
        token = input('>>> ')
        settings.update(token=token).where(settings.id == 1).execute()
        rprint('Токен изменен!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '4':
        clear()
        rprint('Введите новый User ID')
        chat_id = input('>>> ')
        settings.update(chat_id=chat_id).where(settings.id == 1).execute()
        rprint('User ID изменен!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '5':
        clear()
        rprint('Введите новый прокси сервер')
        proxy_server = input('>>> ')
        settings.update(proxy_server=proxy_server).where(settings.id == 1).execute()
        rprint('Прокси сервер изменен!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '6':
        clear()
        rprint('Введите новый прокси порт')
        proxy_port = input('>>> ')
        settings.update(proxy_port=proxy_port).where(settings.id == 1).execute()
        rprint('Прокси порт изменен!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '7':
        clear()
        rprint('Введите новый прокси логин')
        proxy_login = input('>>> ')
        settings.update(proxy_login=proxy_login).where(settings.id == 1).execute()
        rprint('Прокси логин изменен!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '8':
        clear()
        rprint('Введите новый прокси пароль')
        proxy_password = input('>>> ')
        settings.update(proxy_password=proxy_password).where(settings.id == 1).execute()
        rprint('Прокси пароль изменен!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '9':
        clear()
        rprint('Введите новый прокси тип (http|https|socks5)')
        proxy_type = input('>>> ')
        settings.update(proxy_type=proxy_type).where(settings.id == 1).execute()
        rprint('Прокси тип изменен!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '10':
        clear()
        data = settings.select().where(settings.id == 1).get()
        if data.proxy_enabled:
            settings.update(proxy_enabled=False).where(settings.id == 1).execute()
            rprint('Прокси отключен!')
        else:
            settings.update(proxy_enabled=True).where(settings.id == 1).execute()
            rprint('Прокси включен!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '11':
        clear()
        data = settings.select().where(settings.id == 1).get()
        if data.proxy_auth_enabled:
            settings.update(proxy_auth_enabled=False).where(settings.id == 1).execute()
            rprint('Прокси авторизация отключена!')
        else:
            settings.update(proxy_auth_enabled=True).where(settings.id == 1).execute()
            rprint('Прокси авторизация включена!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '12':
        rprint('Введите новый прокси сервер')
        proxy_server = input('>>> ')
        rprint('Введите новый прокси порт')
        proxy_port = input('>>> ')
        rprint('Введите новый прокси логин, если нету то пропустите')
        proxy_login = input('>>> ')
        rprint('Введите новый прокси пароль, если нету то пропустите')
        proxy_password = input('>>> ')
        rprint('Введите новый прокси тип (http|https|socks5)')
        proxy_type = input('>>> ')
        settings.update(proxy_server=proxy_server,
                        proxy_port=proxy_port,
                        proxy_login=proxy_login,
                        proxy_password=proxy_password,
                        proxy_type=proxy_type).where(settings.id == 1).execute()
        rprint('Прокси изменен!')
        input('Нажмите Enter для продолжения...')
        edit_settings()
    elif choice == '13':
        clear()
        main_menu()
    elif choice == '14':
        clear()
        rprint('Выход...')
        exit()
    else:
        edit_settings()


def main_menu():
    clear()
    try:
        data = servers.select(servers.id).order_by(servers.id.desc()).limit(1).get()
    except DoesNotExist:
        data = '[bright_red]Сервера отсуствуют[/bright_red]'
    rprint('[bold bright_yellow]Скрипт автоматического пинга серверов от 夢遊者[/bold bright_yellow]')
    rprint('Версия: [magenta]v1.0[/magenta]')
    rprint('TG: [blue]@ShellRok[/blue] | GitHub: [blue]github.com/Lunatik-Cyber[/blue]')
    rprint('=================================================')
    rprint('Всего серверов в базе: ' + str(data))
    rprint('=================================================')
    rprint('[bold bright_yellow]Главное меню:[/bold bright_yellow]\n')
    rprint('  1) Запустить проверку серверов')
    rprint('  2) Запустить проверку выбранных серверов')
    rprint('  3) Добавить сервер в базу')
    rprint('  4) Удалить сервер из базы')
    rprint('  5) Очистить базу')
    rprint('  6) Настройки')
    rprint('  7) Выход\n')
    option = input('>>> ')
    if option == '1':
        check_servers()
    elif option == '2':
        check_selected_servers()
    elif option == '3':
        add_server()
    elif option == '4':
        delete_server()
    elif option == '5':
        clear_base()
    elif option == '6':
        edit_settings()
    elif option == '7':
        exit()
    else:
        main_menu()


if __name__ == '__main__':
    db.create_tables([settings, servers])
    main_menu()
