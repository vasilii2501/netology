import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import VkTools

from database import engine, add_user, check_user


class BotInterface():

    def __init__(self, comunity_token, acces_token):
        self.interface = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.interface)
        self.api = VkTools(acces_token)
        self.params = None
        self.users = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.interface.method('messages.send', {
                    'user_id': user_id,
                    'message': message,
                    'attachment': attachment,
                    'random_id': get_random_id()
                }
            )

    def check_user_in_db(self, event):
        user = self.users.pop()
        while check_user(engine, event.user_id, user["id"]):
            if self.users:
                user = self.users.pop()
            else:
                self.offset += 50
                self.users = self.api.serch_users(self.params, self.offset)
                user = self.users.pop()
        return user

    def user_photo_string(self, user):
        photos = self.api.get_photos(user['id'])
        photo_string = ''
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
        return photo_string

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()

                if command == 'привет':
                    self.params = self.api.get_profile_info(event.user_id)
                    self.message_send(event.user_id,
                                      f'здравствуй {self.params["name"]}')
                    if self.params.get('city') is None:
                        self.params['city'] = self.ask_city(event.user_id)
                        self.message_send(event.user_id,
                                          'напишите "поиск"')

                elif command == 'поиск':
                    if self.users:
                        user = self.check_user_in_db(event)
                        attachment = self.user_photo_string(user)
                    else:
                        self.users = self.api.serch_users(self.params,
                                                          self.offset)
                        user = self.check_user_in_db(event)
                        attachment = self.user_photo_string(user)
                        self.offset += 50

                    self.message_send(
                        event.user_id,
                        f' {user["name"]} ссылка: vk.com/id{user["id"]}',
                        attachment=attachment
                        )

                    add_user(engine, event.user_id, user['id'])

                elif command == 'пока':
                    self.message_send(event.user_id, 'пока')

                else:
                    self.message_send(event.user_id, 'команда не опознана')

    def ask_city(self, user_id):
        self.message_send(user_id, 'Введите город в котором искать пару ')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()
                city = command
                self.params["city"] = city
                return event.text.title()


if __name__ == '__main__':
    bot = BotInterface(comunity_token, acces_token)
    bot.event_handler()
