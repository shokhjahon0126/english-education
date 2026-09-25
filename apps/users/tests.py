from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User, Role


class UserAuthAndPermissionTests(APITestCase):
    def setUp(self):
        # SuperAdmin user (odatda adminkadan yaratiladi)
        self.superadmin = User.objects.create_user(
            username='superadmin',
            phone='+998901111111',
            password='password123',
            role=Role.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True
        )

        # Admin user
        self.admin = User.objects.create_user(
            username='admin_user',
            phone='+998902222222',
            password='password123',
            role=Role.ADMIN,
            is_staff=True
        )

        # Teacher user
        self.teacher = User.objects.create_user(
            username='teacher_user',
            phone='+998903333333',
            password='password123',
            role=Role.TEACHER
        )

        # Student user
        self.student = User.objects.create_user(
            username='student_user',
            phone='+998904444444',
            password='password123',
            role=Role.STUDENT
        )

    def test_login_returns_jwt_id_and_role(self):
        """
        1. Login JWT da ishlashi va javobda id, role qaytishi kerak.
        """
        # Username orqali login
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'username': 'admin_user',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('schema_name', response.data)
        self.assertEqual(response.data['id'], self.admin.id)
        self.assertEqual(response.data['role'], Role.ADMIN)

        # Phone orqali ham login qilib ko'ramiz
        response_phone = self.client.post(url, {
            'username': '+998902222222',
            'password': 'password123'
        })
        self.assertEqual(response_phone.status_code, status.HTTP_200_OK)
        self.assertEqual(response_phone.data['id'], self.admin.id)

    def test_change_password(self):
        """
        2. Passwordni o'zgartirish API (new_password va new_password_confirm).
        """
        self.client.force_authenticate(user=self.student)
        url = reverse('change_password')

        # Parollar mos kelmaganda xatolik
        resp_mismatch = self.client.post(url, {
            'new_password': 'newpassword1234',
            'new_password_confirm': 'otherpassword'
        })
        self.assertEqual(resp_mismatch.status_code, status.HTTP_400_BAD_REQUEST)

        # Muvaffaqiyatli parol o'zgartirish
        resp_success = self.client.post(url, {
            'new_password': 'newpassword1234',
            'new_password_confirm': 'newpassword1234'
        })
        self.assertEqual(resp_success.status_code, status.HTTP_200_OK)

        # Yangi parol bilan tizimga kirish tekshiruvi
        login_url = reverse('token_obtain_pair')
        resp_login = self.client.post(login_url, {
            'username': 'student_user',
            'password': 'newpassword1234'
        })
        self.assertEqual(resp_login.status_code, status.HTTP_200_OK)

    def test_put_method_not_allowed(self):
        """
        3. PUT methodi taqiqlangan, faqat PATCH ruxsat berilgan.
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-detail', kwargs={'pk': self.student.id})

        # PUT method yuborilganda 405 Method Not Allowed qaytishi kerak
        resp_put = self.client.put(url, {
            'username': 'student_updated',
            'first_name': 'Updated'
        })
        self.assertEqual(resp_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # PATCH method esa ishlashi kerak
        resp_patch = self.client.patch(url, {
            'first_name': 'UpdatedName'
        })
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'UpdatedName')

    def test_nobody_can_create_superadmin_via_api(self):
        """
        4. SuperAdmin rolini hech qaysi user create qila olmaydi.
        """
        # Hatto superadmin ham API orqali superadmin yarata olmaydi
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('user-list')

        resp = self.client.post(url, {
            'username': 'new_superadmin',
            'phone': '+998909999999',
            'password': 'password123',
            'role': Role.SUPER_ADMIN
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', resp.data)

    def test_admin_can_only_create_teacher_and_student(self):
        """
        5. Admin faqat Teacher va Studentlarni yaratishi mumkin (Admin yoki Superadmin emas).
        """
        self.client.force_authenticate(user=self.admin)
        url = reverse('user-list')

        # Admin boshqa ADMIN yaratishga urinsa: rad etilishi kerak
        resp_admin = self.client.post(url, {
            'username': 'another_admin',
            'phone': '+998905555555',
            'password': 'password123',
            'role': Role.ADMIN
        })
        self.assertEqual(resp_admin.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', resp_admin.data)

        # Admin TEACHER yarata olishi kerak
        resp_teacher = self.client.post(url, {
            'username': 'new_teacher',
            'phone': '+998906666666',
            'password': 'password123',
            'role': Role.TEACHER
        })
        self.assertEqual(resp_teacher.status_code, status.HTTP_201_CREATED)

        # Admin STUDENT yarata olishi kerak
        resp_student = self.client.post(url, {
            'username': 'new_student',
            'phone': '+998907777777',
            'password': 'password123',
            'role': Role.STUDENT
        })
        self.assertEqual(resp_student.status_code, status.HTTP_201_CREATED)

    def test_superadmin_can_create_admin(self):
        """
        SuperAdmin Admin yaratish huquqiga ega.
        """
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('user-list')

        resp = self.client.post(url, {
            'username': 'admin_by_super',
            'phone': '+998908888888',
            'password': 'password123',
            'role': Role.ADMIN
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_teacher_and_student_cannot_create_users(self):
        """
        Teacher va Student foydalanuvchi yarata olmaydi.
        """
        url = reverse('user-list')

        # Teacher create qilmoqchi bo'lsa: 403 Forbidden
        self.client.force_authenticate(user=self.teacher)
        resp_teacher = self.client.post(url, {
            'username': 'try_student',
            'phone': '+998909876543',
            'password': 'password123',
            'role': Role.STUDENT
        })
        self.assertEqual(resp_teacher.status_code, status.HTTP_403_FORBIDDEN)

        # Student create qilmoqchi bo'lsa: 403 Forbidden
        self.client.force_authenticate(user=self.student)
        resp_student = self.client.post(url, {
            'username': 'try_student2',
            'phone': '+998909876544',
            'password': 'password123',
            'role': Role.STUDENT
        })
        self.assertEqual(resp_student.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_edit_or_delete_another_admin(self):
        """
        Admin boshqa Adminni yoki SuperAdminni o'chira yoki tahrirlay olmasligi kerak.
        """
        another_admin = User.objects.create_user(
            username='another_admin_user',
            phone='+998909990001',
            password='password123',
            role=Role.ADMIN,
            is_staff=True
        )

        self.client.force_authenticate(user=self.admin)
        detail_url = reverse('user-detail', kwargs={'pk': another_admin.id})

        # Boshqa adminni PATCH qilish taqiqlanadi (403 Forbidden)
        resp_patch = self.client.patch(detail_url, {'first_name': 'Hacked'})
        self.assertEqual(resp_patch.status_code, status.HTTP_403_FORBIDDEN)

        # Boshqa adminni DELETE qilish taqiqlanadi (403 Forbidden)
        resp_delete = self.client.delete(detail_url)
        self.assertEqual(resp_delete.status_code, status.HTTP_403_FORBIDDEN)

