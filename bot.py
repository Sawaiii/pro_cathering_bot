from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import db
import datetime

TOKEN = 'hide'

# Разрешенные Telegram ID для доступа к команде /admin
allowed_admins = [897335890, 9876543210]

def start(update, context):
    if update.message:
        user = update.message.from_user
        chat_id = update.message.chat_id
    else:
        user = update.callback_query.from_user
        chat_id = update.callback_query.message.chat_id
    
    db.save_user(user.id, user.username)
    keyboard = [['Сделать заказ', 'Мои заказы', 'Главное меню']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    context.bot.send_message(chat_id=chat_id, text='Добро пожаловать! \nНажмите кнопку "Сделать заказ" ниже для начала. \nА что бы посмотреть существующие заказы, нажмите "Мои заказы".', reply_markup=reply_markup)


def make_order(update, context):
    menus = db.get_all_menus()
    if menus:
        keyboard = [[InlineKeyboardButton(menu[1], callback_data=f'select_date_{menu[1]}')] for menu in menus]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Выберите дату:', reply_markup=reply_markup)
    else:
        update.message.reply_text('В настоящее время нет доступных дат для заказа.')

def select_date(update, context):
    query = update.callback_query
    query.answer()
    date = query.data.split('_')[2]
    context.user_data['order_date'] = date

    menu = db.get_menu_by_date(date)

    if menu:
        query.edit_message_text(text=f'Вы выбрали дату {date}.\nМеню на этот день:\n{menu[2]}. \nВведите количество порций:\n Если вы передумали, введите ноль (0) для отмены.')
    else:
        query.edit_message_text(text=f'Вы выбрали дату {date}, но для этого дня меню пока что отсутствует. Введите количество порций:\n Если вы передумали, введите ноль (0) для отмены.')

def handle_message(update, context):
    user_input = update.message.text
    if 'order_date' in context.user_data:
        if user_input.isdigit():
            portions = int(user_input)
            if portions > 0:
                user = db.get_user(update.message.from_user.id)
                db.save_order(user[0], context.user_data['order_date'], portions)
                update.message.reply_text('Спасибо за заказ!', reply_markup=ReplyKeyboardMarkup([['Сделать заказ', 'Мои заказы', 'Главное меню']], resize_keyboard=True))
                del context.user_data['order_date']
            elif portions == 0:
                update.message.reply_text('Вы отменили заказ.', reply_markup=ReplyKeyboardMarkup([['Сделать заказ', 'Мои заказы', 'Главное меню']], resize_keyboard=True))
                del context.user_data['order_date']
            else:
                update.message.reply_text('Некорректное значение. Введите количество порций больше нуля:')
        else:
            update.message.reply_text('Некорректное значение. Введите количество порций числом:')
    elif 'admin_step' in context.user_data and context.user_data['admin_step'] == 'add_menu_date':
        handle_add_menu_date(update, context)
    elif 'admin_step' in context.user_data and context.user_data['admin_step'] == 'add_menu_text':
        save_admin_menu(update, context)
    elif 'admin_step' in context.user_data and context.user_data['admin_step'] == 'edit_menu_text':
        save_edited_menu(update, context)
    elif user_input == 'Сделать заказ':
        make_order(update, context)
    elif user_input == 'Мои заказы':
        show_orders(update, context)
    elif user_input == 'Главное меню':
        start(update, context)

def show_orders(update, context):
    user = db.get_user(update.message.from_user.id)
    orders = db.get_user_orders(user[0])
    if not orders:
        update.message.reply_text('У вас нет заказов.', reply_markup=ReplyKeyboardMarkup([['Сделать заказ', 'Мои заказы', 'Главное меню']], resize_keyboard=True))
    else:
        response = ''
        for order in orders:
            response += f"Дата: {order[2]}, Пользователь: {user[2]} ({user[1]}), Порции: {order[3]}\n"
        update.message.reply_text(response, reply_markup=ReplyKeyboardMarkup([['Сделать заказ', 'Мои заказы', 'Главное меню']], resize_keyboard=True))

def admin_panel(update, context):
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    if user_id in allowed_admins:
        keyboard = [
            [InlineKeyboardButton('Добавить меню', callback_data='add_menu')],
            [InlineKeyboardButton('Редактировать меню', callback_data='edit_menu')],
            [InlineKeyboardButton('Удалить меню', callback_data='delete_menu')],
            [InlineKeyboardButton('Все заказы', callback_data='all_orders')],
            [InlineKeyboardButton('Главное меню', callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Панель администратора:', reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='У вас нет доступа к админской панели.')

def add_menu(update, context):
    query = update.callback_query
    query.answer()
    context.user_data['admin_step'] = 'add_menu_date'
    query.edit_message_text(text='Введите дату для добавления меню в формате дд-мм-гггг:')

def handle_add_menu_date(update, context):
    menu_date = update.message.text
    context.user_data['menu_date'] = menu_date
    context.user_data['admin_step'] = 'add_menu_text'
    update.message.reply_text(f'Введите меню для даты {menu_date}:')

def add_menu_text(update, context):
    query = update.callback_query
    query.answer()
    date = query.data.split('_')[2]
    context.user_data['menu_date'] = date
    query.edit_message_text(text=f'Введите меню для даты\n {date}:')
    
def edit_menu(update, context):
    query = update.callback_query
    query.answer()
    menus = db.get_all_menus()
    if not menus:
        query.edit_message_text(text='Нет меню для редактирования.')
    else:
        keyboard = [[InlineKeyboardButton(menu[1], callback_data=f'edit_menu_{menu[1]}')] for menu in menus]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text='На какую дату редактировать меню?', reply_markup=reply_markup)

def edit_menu_text(update, context):
    query = update.callback_query
    query.answer()
    date = query.data.split('_')[2]
    context.user_data['menu_date'] = date
    context.user_data['admin_step'] = 'edit_menu_text'
    menu = db.get_menu_by_date(date)
    query.edit_message_text(text=f'Текущее меню:\n {menu[2]}\nВведите новое меню:')

def save_admin_menu(update, context):
    menu_text = update.message.text
    if 'menu_date' in context.user_data:
        db.save_menu(context.user_data['menu_date'], menu_text)
        update.message.reply_text('Меню успешно сохранено.', reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
        del context.user_data['menu_date']
        del context.user_data['admin_step']
    else:
        update.message.reply_text('Ошибка: дата меню не найдена. Пожалуйста, попробуйте снова.')

def save_edited_menu(update, context):
    new_menu_text = update.message.text
    if 'menu_date' in context.user_data:
        db.save_menu(context.user_data['menu_date'], new_menu_text)
        update.message.reply_text('Меню успешно обновлено.', reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
        del context.user_data['menu_date']
        del context.user_data['admin_step']
    else:
        update.message.reply_text('Ошибка: дата меню не найдена. Пожалуйста, попробуйте снова.')

def all_orders(update, context):
    query = update.callback_query
    query.answer()
    
    orders = db.get_all_orders()
    total_portions_per_day = {}
    
    for order in orders:
        order_date = order[3]
        portions = order[4]
        
        if order_date in total_portions_per_day:
            total_portions_per_day[order_date] += portions
        else:
            total_portions_per_day[order_date] = portions
    
    response = ''
    for order_date, total_portions in total_portions_per_day.items():
        response += f"Дата: {order_date}, Общее количество порций: {total_portions}\n"
    
    response += "\nСписок всех заказов:\n"
    for order in orders:
        response += f"Дата: {order[3]}, Пользователь: {order[2]} ({order[1]}), Порции: {order[4]}\n"
    
    query.edit_message_text(text=response)

def delete_menu(update, context):
    query = update.callback_query
    query.answer()
    menus = db.get_all_menus()
    if not menus:
        query.edit_message_text(text='Нет меню для удаления.')
    else:
        keyboard = [[InlineKeyboardButton(menu[1], callback_data=f'delete_menu_{menu[1]}')] for menu in menus]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text='Выберите дату для удаления меню:', reply_markup=reply_markup)

def delete_menu_date(update, context):
    query = update.callback_query
    query.answer()
    date = query.data.split('_')[2]
    db.delete_menu(date)
    query.edit_message_text(text=f'Меню и заказы на дату {date} были удалены.')

def button(update, context):
    query = update.callback_query
    if query.data.startswith('select_date_'):
        select_date(update, context)
    elif query.data.startswith('add_menu_'):
        add_menu_text(update, context)
    elif query.data.startswith('edit_menu_'):
        edit_menu_text(update, context)
    elif query.data.startswith('delete_menu_'):
        delete_menu_date(update, context)
    elif query.data == 'add_menu':
        add_menu(update, context)
    elif query.data == 'edit_menu':
        edit_menu(update, context)
    elif query.data == 'delete_menu':
        delete_menu(update, context)
    elif query.data == 'all_orders':
        all_orders(update, context)
    elif query.data == 'main_menu':
        start(update, context)

def start_bot():
    db.init_db()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    start_bot()
