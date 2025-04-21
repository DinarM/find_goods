import asyncio
import time
from collections import deque
from pyrogram import Client, filters, idle

# Настройки аккаунта
from dotenv import load_dotenv
import os

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
group_ids = [int(g) for g in os.getenv("GROUP_IDS").split(",")]
my_user_id = int(os.getenv("MY_USER_ID"))

# Ключевые слова
keywords = ["кресло", "стул"]

# Интервал отправки отчета (в секундах)
report_interval_seconds = 60
# Очередь ссылок
links_queue = deque()

# Файл для логов
log_file = "found_links.log"

# Создаем клиент для личного аккаунта
app = Client("my_account", api_id=api_id, api_hash=api_hash)



# Отладочный хэндлер, который ловит все сообщения и посты в каналах
# @app.on_message()
# async def debug_all(client, message):
#     print(f"[DEBUG] Получено сообщение: {message}")

# @app.on_raw_update()
# async def raw_update(client, update, users, chats):
#     # This will print every raw update, including channel posts
#     print(f"[RAW UPDATE] {update}")

# Проверка наличия ключевого слова в тексте
def contains_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

# Запись ссылки в лог-файл
def log_link(link: str):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {link}\n")

# Обработчик сообщений из нужных групп
@app.on_message(filters.chat(group_ids))
async def find_and_queue(client, message):
    text_to_check = message.text or message.caption
    print(f"Получено сообщение: {text_to_check}")
    print(f"Проверяем сообщение: {text_to_check}")
    print(f"Ищем ключевые слова: {keywords}")

    if not text_to_check:
        print("Сообщение без текста/подписи, пропускаем.")
        return

    if contains_keyword(text_to_check):
        print(f"✅ Найдено ключевое слово: {text_to_check}")
        if getattr(message.chat, "username", None):
            link = f"https://t.me/{message.chat.username}/{message.id}"
        else:
            link = f"tg://privatepost?channel={abs(message.chat.id)}&post={message.id}"

        links_queue.append(link)
        log_link(link)
        print(f"Ссылка добавлена в очередь: {link}")
    else:
        print("❌ Ключевые слова не найдены.")

# Периодическая отправка отчета
async def send_report():
    print("Запущен процесс отправки отчетов.")
    while True:
        if links_queue:
            links_to_send = list(links_queue)
            print(f"✉️ Подготовка отчета: {len(links_to_send)} ссылок.")
            links_queue.clear()

            # Формируем нумерованный список ссылок
            text_report = "\n".join(f"{idx+1}. {link}" for idx, link in enumerate(links_to_send))
            try:
                await app.send_message(my_user_id, f"🪑 Найденные посты:\n\n{text_report}")
                print("✅ Отчет отправлен.")
            except Exception as e:
                print(f"❗ Ошибка при отправке отчета: {e}")
        else:
            print("⏳ Нет новых ссылок для отправки.")
        await asyncio.sleep(report_interval_seconds)

# Вывод списка групп при старте
async def show_monitored_groups():
    print("\n📋 Слушаем группы:")
    for group in group_ids:
        try:
            chat = await app.get_chat(group)
            title = chat.title or chat.username or "No Title"
            print(f"  - {title} (ID: {chat.id})")
        except Exception as e:
            print(f"  ❗ Не удалось получить информацию по {group}: {e}")
    print("\n✅ Мониторинг запущен!\n")

# Главная функция
async def main():
    # Запускаем клиент
    await app.start()
    print("✅ Клиент запущен.")
    # Показываем группы
    await show_monitored_groups()
    # Запускаем фоновой таск по отправке отчетов
    asyncio.create_task(send_report())
    # Держим соединение открытым для обработки обновлений
    await idle()
    # Останавливаем клиент по завершению
    await app.stop()

if __name__ == "__main__":
    app.run(main())