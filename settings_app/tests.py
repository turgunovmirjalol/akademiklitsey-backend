"""
settings_app endpoint testlari.

Ishga tushirish:
    python manage.py test settings_app.tests --verbosity=2
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from .models import SiteSettings


SETTINGS_URL = '/settings/'


def make_admin(username='admin_test', password='Admin1234!'):
    user = User.objects.create_user(
        username=username, password=password, role=User.ROLE_ADMIN
    )
    return user


def make_user(username='plain_user', password='User1234!'):
    return User.objects.create_user(
        username=username, password=password, role=User.ROLE_USER
    )


VALID_PAYLOAD = {
    'short_name_uz':      'Akademik Litsey',
    'short_name_uz_cyrl': 'Академик Литсей',
    'short_name_ru':      'Академический Лицей',
    'short_name_en':      'Academic Lyceum',
    'full_name_uz':       'Akademik Litsey TDTU',
    'full_name_uz_cyrl':  'Академик Литсей ТДТУ',
    'full_name_ru':       'Академический Лицей ТГТУ',
    'full_name_en':       'Academic Lyceum TSTU',
    'address_uz':         'Toshkent sh., Chilonzor tumani',
    'address_uz_cyrl':    'Тошкент ш., Чилонзор тумани',
    'address_ru':         'г. Ташкент, Чиланзарский район',
    'address_en':         'Tashkent city, Chilanzar district',
    'established_year':   2005,
    'phone':              '+998712345678',
    'email':              'info@lyceum.uz',
    'website':            'https://lyceum.uz',
    'telegram':           'https://t.me/lyceum',
    'instagram':          'https://instagram.com/lyceum',
    'facebook':           'https://facebook.com/lyceum',
    'youtube':            'https://youtube.com/lyceum',
}


class SiteSettingsGetTest(TestCase):
    """GET endpoint testlari"""

    def setUp(self):
        self.client = APIClient()

    def test_get_404_when_no_settings(self):
        """Sozlamalar yo'q bo'lganda 404 qaytishi kerak"""
        res = self.client.get(SETTINGS_URL)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_returns_settings(self):
        """Sozlamalar mavjud bo'lganda 200 va to'g'ri data qaytishi kerak"""
        SiteSettings.objects.create(**{k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'})
        res = self.client.get(SETTINGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('translations', res.data)
        self.assertIn('uz', res.data['translations'])
        self.assertIn('ru', res.data['translations'])
        self.assertIn('en', res.data['translations'])
        self.assertIn('uz_cyrl', res.data['translations'])

    def test_get_with_lang_filter_uz(self):
        """?lang=uz faqat uz tarjimasini qaytarishi kerak"""
        SiteSettings.objects.create(**{k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'})
        res = self.client.get(SETTINGS_URL + '?lang=uz')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('uz', res.data['translations'])
        self.assertNotIn('ru', res.data['translations'])
        self.assertEqual(res.data['translations']['uz']['short_name'], 'Akademik Litsey')

    def test_get_with_lang_filter_ru(self):
        """?lang=ru faqat ru tarjimasini qaytarishi kerak"""
        SiteSettings.objects.create(**{k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'})
        res = self.client.get(SETTINGS_URL + '?lang=ru')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('ru', res.data['translations'])
        self.assertEqual(res.data['translations']['ru']['short_name'], 'Академический Лицей')

    def test_get_with_lang_filter_en(self):
        """?lang=en faqat en tarjimasini qaytarishi kerak"""
        SiteSettings.objects.create(**{k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'})
        res = self.client.get(SETTINGS_URL + '?lang=en')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('en', res.data['translations'])
        self.assertEqual(res.data['translations']['en']['short_name'], 'Academic Lyceum')

    def test_get_with_lang_filter_uz_cyrl(self):
        """?lang=uz_cyrl faqat uz_cyrl tarjimasini qaytarishi kerak"""
        SiteSettings.objects.create(**{k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'})
        res = self.client.get(SETTINGS_URL + '?lang=uz_cyrl')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('uz_cyrl', res.data['translations'])
        self.assertEqual(res.data['translations']['uz_cyrl']['short_name'], 'Академик Литсей')

    def test_get_anonymous_allowed(self):
        """Autentifikatsiyasiz ham GET ishlashi kerak"""
        SiteSettings.objects.create(**{k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'})
        res = self.client.get(SETTINGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_translations_all_fields_present(self):
        """Har bir tilda short_name, full_name, address mavjud bo'lishi kerak"""
        SiteSettings.objects.create(**{k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'})
        res = self.client.get(SETTINGS_URL)
        for lang in ['uz', 'uz_cyrl', 'ru', 'en']:
            self.assertIn('short_name', res.data['translations'][lang])
            self.assertIn('full_name', res.data['translations'][lang])
            self.assertIn('address', res.data['translations'][lang])


class SiteSettingsPostTest(TestCase):
    """POST endpoint testlari"""

    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)

    def test_post_creates_settings(self):
        """Admin POST bilan sozlamalar yarata olishi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_post_returns_all_translations(self):
        """POST javobida barcha 4 til tarjimasi bo'lishi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for lang in ['uz', 'uz_cyrl', 'ru', 'en']:
            self.assertIn(lang, res.data['translations'])

    def test_post_saves_uz_cyrl(self):
        """uz_cyrl maydonlari to'g'ri saqlanishi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            res.data['translations']['uz_cyrl']['short_name'],
            'Академик Литсей'
        )

    def test_post_saves_en(self):
        """en maydonlari to'g'ri saqlanishi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            res.data['translations']['en']['full_name'],
            'Academic Lyceum TSTU'
        )

    def test_post_saves_address_all_langs(self):
        """Barcha tillarda address saqlanishi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['translations']['en']['address'], 'Tashkent city, Chilanzar district')
        self.assertEqual(res.data['translations']['uz_cyrl']['address'], 'Тошкент ш., Чилонзор тумани')

    def test_post_saves_social_links(self):
        """Ijtimoiy tarmoq linklari saqlanishi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['facebook'], 'https://facebook.com/lyceum')
        self.assertEqual(res.data['youtube'], 'https://youtube.com/lyceum')

    def test_post_duplicate_returns_400(self):
        """Ikkinchi POST 400 qaytarishi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        self.client.post(SETTINGS_URL, payload, format='multipart')
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_without_short_name_fails(self):
        """short_name bo'lmasa validatsiya xatosi"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        for key in ['short_name_uz', 'short_name_ru', 'short_name_en', 'short_name_uz_cyrl']:
            payload.pop(key, None)
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_without_full_name_fails(self):
        """full_name bo'lmasa validatsiya xatosi"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        for key in ['full_name_uz', 'full_name_ru', 'full_name_en', 'full_name_uz_cyrl']:
            payload.pop(key, None)
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_anonymous_forbidden(self):
        """Autentifikatsiyasiz POST 401 yoki 403 qaytarishi kerak"""
        self.client.force_authenticate(user=None)
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_post_plain_user_forbidden(self):
        """Oddiy user POST qila olmasligi kerak"""
        plain = make_user()
        self.client.force_authenticate(user=plain)
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.post(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class SiteSettingsPutTest(TestCase):
    """PUT endpoint testlari"""

    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        # Avval sozlamalar yaratib qo'yamiz
        SiteSettings.objects.create(**{k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'})

    def test_put_updates_all_fields(self):
        """PUT barcha maydonlarni yangilashi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        payload['short_name_uz'] = 'Yangi Litsey'
        payload['short_name_en'] = 'New Lyceum'
        res = self.client.put(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['translations']['uz']['short_name'], 'Yangi Litsey')
        self.assertEqual(res.data['translations']['en']['short_name'], 'New Lyceum')

    def test_put_updates_uz_cyrl(self):
        """PUT uz_cyrl maydonlarini yangilashi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        payload['short_name_uz_cyrl'] = 'Янги Литсей'
        res = self.client.put(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['translations']['uz_cyrl']['short_name'], 'Янги Литсей')

    def test_put_updates_address_en(self):
        """PUT address_en maydonini yangilashi kerak"""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        payload['address_en'] = 'New address EN'
        res = self.client.put(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['translations']['en']['address'], 'New address EN')

    def test_put_404_when_no_settings(self):
        """Sozlamalar yo'q bo'lganda PUT 404 qaytarishi kerak"""
        SiteSettings.objects.all().delete()
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.put(SETTINGS_URL, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_anonymous_forbidden(self):
        """Autentifikatsiyasiz PUT 401 yoki 403 qaytarishi kerak"""
        self.client.force_authenticate(user=None)
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'}
        res = self.client.put(SETTINGS_URL, payload, format='multipart')
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class SiteSettingsPatchTest(TestCase):
    """PATCH endpoint testlari"""

    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        SiteSettings.objects.create(**{k: v for k, v in VALID_PAYLOAD.items() if k != 'logo'})

    def test_patch_partial_update(self):
        """PATCH faqat yuborilgan maydonlarni yangilashi kerak"""
        res = self.client.patch(SETTINGS_URL, {'short_name_uz': 'Patch Litsey'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['translations']['uz']['short_name'], 'Patch Litsey')

    def test_patch_uz_cyrl(self):
        """PATCH uz_cyrl maydonini yangilashi kerak"""
        res = self.client.patch(SETTINGS_URL, {'short_name_uz_cyrl': 'Патч Литсей'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['translations']['uz_cyrl']['short_name'], 'Патч Литсей')

    def test_patch_en_fields(self):
        """PATCH en maydonlarini yangilashi kerak"""
        res = self.client.patch(SETTINGS_URL, {
            'short_name_en': 'Patched EN',
            'full_name_en': 'Patched Full EN',
            'address_en': 'Patched Address EN',
        }, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['translations']['en']['short_name'], 'Patched EN')
        self.assertEqual(res.data['translations']['en']['full_name'], 'Patched Full EN')
        self.assertEqual(res.data['translations']['en']['address'], 'Patched Address EN')

    def test_patch_social_links(self):
        """PATCH ijtimoiy tarmoq linkini yangilashi kerak"""
        res = self.client.patch(SETTINGS_URL, {
            'facebook': 'https://facebook.com/new',
            'youtube': 'https://youtube.com/new',
        }, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['facebook'], 'https://facebook.com/new')
        self.assertEqual(res.data['youtube'], 'https://youtube.com/new')

    def test_patch_phone_and_email(self):
        """PATCH phone va email yangilashi kerak"""
        res = self.client.patch(SETTINGS_URL, {
            'phone': '+998991234567',
            'email': 'new@lyceum.uz',
        }, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['phone'], '+998991234567')
        self.assertEqual(res.data['email'], 'new@lyceum.uz')

    def test_patch_does_not_clear_other_fields(self):
        """PATCH boshqa maydonlarni o'chirmasligi kerak"""
        res = self.client.patch(SETTINGS_URL, {'phone': '+998001234567'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Boshqa maydonlar o'zgarmasligi kerak
        self.assertEqual(res.data['translations']['ru']['short_name'], 'Академический Лицей')

    def test_patch_404_when_no_settings(self):
        """Sozlamalar yo'q bo'lganda PATCH 404 qaytarishi kerak"""
        SiteSettings.objects.all().delete()
        res = self.client.patch(SETTINGS_URL, {'phone': '+998001234567'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_anonymous_forbidden(self):
        """Autentifikatsiyasiz PATCH 401 yoki 403 qaytarishi kerak"""
        self.client.force_authenticate(user=None)
        res = self.client.patch(SETTINGS_URL, {'phone': '+998001234567'}, format='multipart')
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class SiteSettingsModelTest(TestCase):
    """Model singleton xatti-harakati testlari"""

    def test_singleton_save(self):
        """Ikkinchi save yangi yozuv yaratmasligi kerak"""
        s1 = SiteSettings.objects.create(short_name_uz='Birinchi')
        s2 = SiteSettings(short_name_uz='Ikkinchi')
        s2.save()
        self.assertEqual(SiteSettings.objects.count(), 1)
        self.assertEqual(SiteSettings.objects.first().short_name_uz, 'Ikkinchi')

    def test_get_instance_returns_none_when_empty(self):
        """Bo'sh DB da get_instance None qaytarishi kerak"""
        self.assertIsNone(SiteSettings.get_instance())

    def test_get_instance_returns_object(self):
        """Yozuv bo'lganda get_instance uni qaytarishi kerak"""
        SiteSettings.objects.create(short_name_uz='Test')
        self.assertIsNotNone(SiteSettings.get_instance())
