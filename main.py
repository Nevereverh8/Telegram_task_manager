import threading


def bot_thread():
    import tg_bot.bot


def scheduler_thread():
    import reminders


thread1 = threading.Thread(target=bot_thread)
thread2 = threading.Thread(target=scheduler_thread)

thread1.start()
thread2.start()
