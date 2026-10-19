from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class IssueEventPasswordsAdminActionTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin-password',
        )
        self.client.force_login(self.admin_user)

    def run_action(self, *users):
        return self.client.post(reverse('admin:auth_user_changelist'), {
            'action': 'issue_event_passwords',
            'index': '0',
            '_selected_action': [str(user.pk) for user in users],
        })

    def test_resets_passwords_and_sends_individual_html_emails(self):
        users = [
            User.objects.create_user(username='alice', email='alice@example.com', password='old-password'),
            User.objects.create_user(username='bob', email='bob@example.com', password='old-password'),
        ]

        response = self.run_action(*users)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 2)
        self.assertEqual(len(response.context['results'][0]['password']), 32)
        self.assertEqual(len(mail.outbox), 2)
        outbox = mail.outbox
        self.assertEqual([email.to for email in outbox], [[user.email] for user in users])
        for user, result, email in zip(users, response.context['results'], outbox):
            user.refresh_from_db()
            self.assertTrue(user.check_password(result['password']))
            self.assertEqual(email.alternatives[0][1], 'text/html')
            self.assertIn(user.username, email.alternatives[0][0])
            self.assertIn(result['password'], email.alternatives[0][0])
            self.assertIn('közelgő eseményhez', email.alternatives[0][0])
            self.assertIn('https://zsuri.szlg.info/', email.alternatives[0][0])
        self.assertIn('no-store', response['Cache-Control'])

    def test_user_without_email_is_not_reset(self):
        user = User.objects.create_user(username='no-email', password='old-password')

        response = self.run_action(user)

        user.refresh_from_db()
        self.assertTrue(user.check_password('old-password'))
        self.assertEqual(response.context['results'][0]['password'], None)
        self.assertIn('nincs email-cím', response.context['results'][0]['status'])
        self.assertEqual(len(mail.outbox), 0)
