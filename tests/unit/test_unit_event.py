import cloudpassage
import datetime
import json
import os
import pytest

config_file_name = "portal.yaml.local"
tests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
config_file = os.path.join(tests_dir, "configs/", config_file_name)

session_info = cloudpassage.ApiKeyManager(config_file=config_file)
key_id = session_info.key_id
secret_key = session_info.secret_key
api_hostname = session_info.api_hostname


class TestUnitEvent:
    def test_create_event_obj(self):
        session = cloudpassage.Event(None)
        assert session

    def test_too_big(self):
        rejected = False
        event = cloudpassage.Event(None)
        try:
            event.list_all(101)
        except cloudpassage.CloudPassageValidation:
            rejected = True
        assert rejected
