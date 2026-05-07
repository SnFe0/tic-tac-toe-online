import telebot
from telebot import types
from nhlpy import player, stats
import datetime

bot = telebot.TeleBot('ВАШ_ТОКЕН')

# ID Сергея Бобровского
BOBROVSKY_ID = 8471695

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🧤 Текущий сезон')
    btn2 = types.KeyboardButton('📊 Вся карьера')
    btn3 = types.KeyboardButton('🏆 Достижения')
    btn4 = types.KeyboardButton('📈 Последняя игра')
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    
    welcome_text = """
🏒 *Статистика Сергея Бобровского*

Выберите нужный раздел:

• *Текущий сезон* - актуальная статистика
• *Вся карьера* - суммарные показатели
• *Достижения* - награды и рекорды
• *Последняя игра* - детали последнего матча
"""
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: m.text == '🧤 Текущий сезон')
def current_season(message):
    try:
        # Получаем данные игрока
        player_data = player.PlayerData(BOBROVSKY_ID)
        
        # Получаем статистику текущего сезона
        season_stats = player_data.season_stats()
        
        # Форматируем ответ
        response = f"""
🧤 *Сергей Бобровский | Текущий сезон*

*Основные показатели:*
• Команда: {player_data.current_team}
• Игр: {season_stats.get('games', 'N/A')}
• Побед: {season_stats.get('wins', 'N/A')}
• Поражений: {season_stats.get('losses', 'N/A')}
• Время на льду: {season_stats.get('timeOnIcePerGame', 'N/A')}

*Вратарская статистика:*
• % отраженных бросков: {season_stats.get('savePercentage', 'N/A')}%
• Коэфф. надежности: {season_stats.get('goalAgainstAverage', 'N/A')}
• Сухих игр: {season_stats.get('shutouts', 'N/A')}
• Отраженных бросков: {season_stats.get('saves', 'N/A')}
"""
        
        # Добавляем кнопки для детальной информации
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('📈 Подробнее', callback_data='detailed_current')
        btn2 = types.InlineKeyboardButton('📊 По играм', callback_data='game_by_game')
        markup.add(btn1, btn2)
        
        bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка получения данных: {str(e)}"
        )

@bot.message_handler(func=lambda m: m.text == '📊 Вся карьера')
def career_stats(message):
    try:
        # Получаем статистику за всю карьеру
        player_data = player.PlayerData(BOBROVSKY_ID)
        career = player_data.career_stats()
        
        response = f"""
🏆 *Сергей Бобровский | Вся карьера*

*Регулярный чемпионат:*
• Сезонов: {career.get('seasons', 'N/A')}
• Игр: {career.get('games', 'N/A')}
• Побед: {career.get('wins', 'N/A')}
• Поражений: {career.get('losses', 'N/A')}
• Сухих игр: {career.get('shutouts', 'N/A')}
• % отраженных бросков: {career.get('savePercentage', 'N/A')}%
• Коэфф. надежности: {career.get('goalAgainstAverage', 'N/A')}

*Плей-офф:*
• Игр: {career.get('playoffGames', 'N/A')}
• Побед: {career.get('playoffWins', 'N/A')}
• Сухих игр: {career.get('playoffShutouts', 'N/A')}
"""
        
        bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка получения данных: {str(e)}"
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'detailed_current':
        # Детальная статистика текущего сезона
        try:
            player_data = player.PlayerData(BOBROVSKY_ID)
            detailed = player_data.season_stats(detailed=True)
            
            response = f"""
📈 *Детальная статистика текущего сезона*

*Показатели за игру:*
• Бросков за игру: {detailed.get('shotsAgainstPerGame', 'N/A')}
• Шайб за игру: {detailed.get('goalsAgainstPerGame', 'N/A')}
• Штрафных минут: {detailed.get('penaltyMinutes', 'N/A')}

*В ситуациях:*
• В большинстве: {detailed.get('powerPlaySavePercentage', 'N/A')}%
• В меньшинстве: {detailed.get('shortHandedSavePercentage', 'N/A')}%
• В равных составах: {detailed.get('evenStrengthSavePercentage', 'N/A')}%
"""
            
            bot.edit_message_text(
                response,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            bot.answer_callback_query(
                call.id,
                f"Ошибка: {str(e)}",
                show_alert=True
            )

if __name__ == '__main__':
    print("Бот с NHL API запущен...")
    bot.polling(none_stop=True)