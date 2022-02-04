# coding: utf-8

from datetime import timedelta as td
from unittest.mock import patch

from django.utils.timezone import now
from hc.api.models import Channel, Check, Notification
from hc.test import BaseTestCase


class NotifyPushbulletTestCase(BaseTestCase):
    def _setup_data(self, value, status="down", email_verified=True):
        self.check = Check(project=self.project)
        self.check.name = "Foo"
        self.check.status = status
        self.check.last_ping = now() - td(minutes=61)
        self.check.save()

        self.channel = Channel(project=self.project)
        self.channel.kind = "pushbullet"
        self.channel.value = value
        self.channel.email_verified = email_verified
        self.channel.save()
        self.channel.checks.add(self.check)

    @patch("hc.api.transports.requests.request")
    def test_it_works(self, mock_post):
        self._setup_data("fake-token", status="up")
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)
        assert Notification.objects.count() == 1

        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["type"], "note")
        self.assertEqual(
            kwargs["json"]["body"], 'The check "Foo" received a ping and is now UP.'
        )
        self.assertEqual(kwargs["headers"]["Access-Token"], "fake-token")

    @patch("hc.api.transports.requests.request")
    def test_it_escapes_body(self, mock_post):
        self._setup_data("fake-token", status="up")
        self.check.name = "Foo & Bar"
        self.check.save()
        mock_post.return_value.status_code = 200

        self.channel.notify(self.check)

        _, kwargs = mock_post.call_args
        self.assertEqual(
            kwargs["json"]["body"],
            'The check "Foo & Bar" received a ping and is now UP.',
        )