# tests/test_realityscan_interface.py
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from core.realityscan_interface import RealityScanInterface
from models.config_models import RealityScanConfig

class TestRealityScanInterface(unittest.TestCase):
    def setUp(self):
        # Mock config
        self.mock_config = RealityScanConfig(executable_path="/path/to/realityscan.exe")

        # We need to patch the logger before instantiating the class
        with patch('logging.getLogger') as mock_get_logger:
            self.interface = RealityScanInterface(self.mock_config)

        # Override temp_dir for predictability
        self.temp_dir = Path(tempfile.gettempdir()) / 'video_3dgs_temp_test'
        self.interface.temp_dir = self.temp_dir
        self.interface.instance_name = "test_instance"

    def test_build_alignment_commands_format(self):
        """Test if the alignment commands are formatted correctly."""
        image_dir = self.temp_dir / "test_instance" / "images"
        quality = "high"

        expected_commands = [
            '-headless',
            '-set', 'instanceName=test_instance',
            '-addFolder', str(image_dir),
            '-set', 'alignQuality=high',
            '-align',
            '-exportXMP', str(self.temp_dir / "test_instance" / "alignment_result.xml"),
            '-exportLatestComponents', str(self.temp_dir / "test_instance" / "components")
        ]

        generated_commands = self.interface._build_alignment_commands(image_dir, quality)

        self.assertEqual(generated_commands, expected_commands)

if __name__ == '__main__':
    unittest.main()
