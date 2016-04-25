import os
import shutil
from unittest import TestCase

from whylog.config import YamlConfigFactory


class TestBasic(TestCase):
    @classmethod
    def setUpClass(cls):
        #This change was caused by fails os.names() for new directories.
        #Renaming was necessary to avoid conflicts between test config directories
        #and orginal independent non tests config directories
        YamlConfigFactory.WHYLOG_DIR = '.whylog_test'

    @classmethod
    def validate_created_config(cls, config, predicted_dir_path):
        assert os.path.isdir(predicted_dir_path)
        assert config._parsers_path == os.path.join(predicted_dir_path, 'parsers.yaml')
        assert sorted(os.listdir(predicted_dir_path)) == [
            'config.yaml', 'log_types.yaml', 'parsers.yaml', 'rules.yaml'
        ]

    @classmethod
    def find_config_in_parent_dir(cls, path):
        YamlConfigFactory._create_new_config_dir(path)
        config, _ = YamlConfigFactory.get_config()
        expected_path = YamlConfigFactory._attach_whylog_dir(path)
        cls.validate_created_config(config, expected_path)

    def test_find_config_in_parent_dir(self):
        path = os.getcwd()
        self.find_config_in_parent_dir(path)
        shutil.rmtree(YamlConfigFactory._attach_whylog_dir(path))
        for i in range(2):
            path, _ = os.path.split(path)
            self.find_config_in_parent_dir(path)
            shutil.rmtree(YamlConfigFactory._attach_whylog_dir(path))

    def test_find_config_in_home_directory(self):
        self.find_config_in_parent_dir(YamlConfigFactory.HOME_DIR)
        shutil.rmtree(YamlConfigFactory._attach_whylog_dir(YamlConfigFactory.HOME_DIR))

    @classmethod
    def tearDownClass(cls):
        #Removed test config directories if test failed
        path = os.getcwd()
        cls.remove_config_dir(path)
        for i in range(2):
            path, _ = os.path.split(path)
            cls.remove_config_dir(path)
        cls.remove_config_dir(YamlConfigFactory.HOME_DIR)

    @classmethod
    def remove_config_dir(cls, path):
        config_dir = os.path.join(path, YamlConfigFactory.WHYLOG_DIR)
        if os.path.isdir(config_dir):
            shutil.rmtree(config_dir)