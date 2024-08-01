import telebot
import time
import random
import threading

# Bot token'ınızı buraya ekleyin
TOKEN = '6479347372:AAFqT9tIicWJu5RR0OICs_V7XfQPxTHlYKc'
bot = telebot.TeleBot(TOKEN)

# Kullanıcı kredilerini saklamak için bir sözlük
user_credits = {}

# Aktif oyunları saklamak için bir sözlük
active_games = {}


@bot.message_handler(commands=['oyunubaslat'])
def start_game(message):
    user_id = message.from_user.id
    if user_id not in user_credits:
        user_credits[user_id] = 0
    threading.Thread(target=credit_increment, args=(user_id,)).start()
    bot.reply_to(message, "Hoş geldiniz! Her 30 saniyede bir kredi kazanacaksınız. "
                          "Oyun oynamak için 'oyna' yazarak cevap verin.")


@bot.message_handler(func=lambda message: message.text.lower() == 'kredi' and
                                          message.reply_to_message and message.reply_to_message.from_user.is_bot)
def check_credit(message):
    user_id = message.from_user.id
    credit = user_credits.get(user_id, 0)
    bot.reply_to(message, f"Mevcut krediniz: {credit}")


@bot.message_handler(func=lambda message: message.text.lower().startswith('oyna') and
                                          message.reply_to_message and message.reply_to_message.from_user.is_bot)
def play_game(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    try:
        bet = int(message.text.split()[1])
        if bet <= user_credits.get(user_id, 0):
            user_credits[user_id] -= bet
            active_games[user_id] = {'bet': bet, 'multiplier': 1.0}
            game_thread = threading.Thread(target=run_game,
                                           args=(user_id, message.chat.id, user_name))
            game_thread.start()
        else:
            bot.reply_to(message, "Yetersiz kredi!")
    except (IndexError, ValueError):
        bot.reply_to(message, "Lütfen geçerli bir bahis miktarı girin. Örnek: oyna 100")


def run_game(user_id, chat_id, user_name):
    game = active_games[user_id]
    game_message = bot.send_message(chat_id, f"{user_name} oyunu başlattı! Çarpan: 1.0x")
    end_time = time.time() + random.uniform(1, 20)

    while time.time() < end_time and user_id in active_games:
        time.sleep(0.1)
        game['multiplier'] += 0.1
        bot.edit_message_text(
            f"{user_name} için oyun devam ediyor! Çarpan: {game['multiplier']:.1f}x",
            chat_id, game_message.message_id
        )

    if user_id in active_games:
        bot.edit_message_text(f"{user_name} için oyun patladı!", chat_id, game_message.message_id)
        lost_amount = game['bet']
        bot.send_message(chat_id, f"{user_name}, oyun patladı! "
                                  f"Kaybettiğiniz miktar: {lost_amount} kredi.")
        del active_games[user_id]


@bot.message_handler(func=lambda message: message.text.lower() == 'çek' and
                                          message.reply_to_message and message.reply_to_message.from_user.is_bot)
def cash_out(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if user_id in active_games:
        game = active_games[user_id]
        winnings = int(game['bet'] * game['multiplier'])
        user_credits[user_id] += winnings
        bot.reply_to(message, f"{user_name}, tebrikler! Kazancınız: {winnings} kredi. "
                              f"Güncel bakiyeniz: {user_credits[user_id]}")
        del active_games[user_id]
    else:
        bot.reply_to(message, f"{user_name}, aktif oyununuz yok.")


def credit_increment(user_id):
    while True:
        time.sleep(30)
        user_credits[user_id] += 1


if __name__ == '__main__':
    bot.polling(none_stop=True)
