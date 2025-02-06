import requests
import json
import os
from datetime import datetime
from tqdm import tqdm  # Для прогресс-бара
from urllib.parse import urlencode

# Константы
VK_API_VERSION = "5.131"
YANDEX_DISK_UPLOAD_URL = "https://cloud-api.yandex.net/v1/disk/resources/upload"
YANDEX_DISK_CREATE_FOLDER_URL = "https://cloud-api.yandex.net/v1/disk/resources"


class VK:
    def __init__(self, access_token):
        self.token = access_token
        self.params = {"access_token": self.token, "v": VK_API_VERSION}

    def get_profile_photos(self, user_id, album_id="profile", count=5):
        url = "https://api.vk.com/method/photos.get"
        params = {
            "owner_id": user_id,
            "album_id": album_id,
            "extended": 1,
            "photo_sizes": 1,
            "count": count,
        }
        response = requests.get(url, params={**self.params, **params})
        return response.json()


class YandexDisk:
    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": f"OAuth {self.token}"}

    def create_folder(self, folder_name):
        params = {"path": folder_name}
        response = requests.put(
            YANDEX_DISK_CREATE_FOLDER_URL, headers=self.headers, params=params
        )
        return response.status_code == 201

    def upload_file(self, file_url, file_name, folder_name):
        params = {"url": file_url, "path": f"{folder_name}/{file_name}"}
        response = requests.post(
            YANDEX_DISK_UPLOAD_URL, headers=self.headers, params=params
        )
        return response.status_code == 202


def save_photos_to_disk(
    vk_token, vk_user_id, yandex_token, folder_name="VK_Photos", photo_count=5
):
    vk = VK(vk_token)
    yandex = YandexDisk(yandex_token)

    # Создаем папку на Яндекс.Диске
    if not yandex.create_folder(folder_name):
        print("Ошибка при создании папки на Яндекс.Диске.")
        return

    # Получаем фотографии с профиля VK
    photos = vk.get_profile_photos(vk_user_id, count=photo_count)
    if "error" in photos:
        print(f"Ошибка при получении фотографий: {photos['error']['error_msg']}")
        return

    photos_info = []
    for photo in tqdm(photos["response"]["items"], desc="Загрузка фотографий"):
        # Выбираем фото максимального размера
        max_size_photo = max(photo["sizes"], key=lambda x: x["width"] * x["height"])
        photo_url = max_size_photo["url"]
        photo_likes = photo["likes"]["count"]
        photo_date = datetime.fromtimestamp(photo["date"]).strftime("%Y-%m-%d")

        # Формируем имя файла
        file_name = f"{photo_likes}.jpg"
        if any(p["file_name"] == file_name for p in photos_info):
            file_name = f"{photo_likes}_{photo_date}.jpg"

        # Загружаем фото на Яндекс.Диск
        if yandex.upload_file(photo_url, file_name, folder_name):
            photos_info.append({"file_name": file_name, "size": max_size_photo["type"]})

    # Сохраняем информацию о фотографиях в JSON
    with open("photos_info.json", "w") as f:
        json.dump(photos_info, f, indent=4)

    print("Фотографии успешно загружены на Яндекс.Диск.")


if __name__ == "__main__":
    vk_token = input("Введите токен VK: ")
    vk_user_id = input("Введите ID пользователя VK: ")
    yandex_token = input("Введите токен Яндекс.Диска: ")

    save_photos_to_disk(vk_token, vk_user_id, yandex_token)
