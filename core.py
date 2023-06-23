from datetime import datetime
import vk_api
from config import acces_token
from vk_api.exceptions import ApiError


class VkTools():
    def __init__(self, acces_token):
        self.api = vk_api.VkApi(token=acces_token)

    def bdate_to_yaer(self, bdate):
        user_year = bdate.split(".")[-1]
        year_now = datetime.now().year
        result = year_now - int(user_year)
        return result

    def get_profile_info(self, user_id):
        try:
            info, = self.api.method('users.get', {
                            'user_id': user_id,
                            'fields': 'city,bdate,sex,relation'
                        }
                                )
        except ApiError as error:
            info = {}
            print(f"Error = {error}")

        user_info = {'name': info['first_name'] + ' ' + info['last_name'],
                     'id':  info['id'],
                     'bdate': info['bdate'] if 'bdate' in info else None,
                     'sex': info['sex'],
                     'city': info['city']['title'] if 'city' in info else None,
                     "year": self.bdate_to_yaer(info["bdate"])
                     }
        return user_info

    def serch_users(self, params, offset):
        try:
            users = self.api.method("users.search", {
                                    "count": 50,
                                    "offset": offset,
                                    "hometown": params["city"],
                                    "sex": 1 if params["sex"] == 2 else 2,
                                    "has_photo": 1,
                                    "age_from": params["year"] - 3,
                                    "age_to": params["year"] + 3,
                                    "status": 6
                                    }
                                    )

        except ApiError as error:
            users = []
            print(f"Error = {error}")

        result = [
            {
                "name": item["first_name"] + " " + item["last_name"],
                "id": item["id"]
            } for item in users['items'] if item["is_closed"] is False
        ]

        return result

    def get_photos(self, user_id):
        photos = self.api.method('photos.get', {
                                    'user_id': user_id,
                                    'album_id': 'profile',
                                    'extended': 1
                                })
        try:
            photos = photos['items']
        except KeyError:
            return []

        res = []

        for photo in photos:
            res.append({'owner_id': photo['owner_id'],
                        'id': photo['id'],
                        'likes': photo['likes']['count'],
                        'comments': photo['comments']['count'],
                        })

        res.sort(key=lambda x: x['likes']+x['comments']*10, reverse=True)

        return res[:3]


if __name__ == '__main__':
    bot = VkTools(acces_token)
    params = bot.get_profile_info(182139455)
    users = bot.serch_users(params, 5)
    print(params)
    # print(bot.get_photos(users[2]['id']))
