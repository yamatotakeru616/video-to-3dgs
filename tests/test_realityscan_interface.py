import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import sys
import subprocess

# Add project root to path to allow importing from 'core'
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.realityscan_interface import RealityScanInterface

class TestRealityScanInterface(unittest.TestCase):

    def setUp(self):
        """Set up a test environment before each test."""
        # Create a temporary directory for all test artifacts
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_rs_"))

        # Mock config to be passed to the interface
        self.mock_config = {
            'realityscan_executable': 'dummy_rs.exe'
        }

        # Patch tempfile.gettempdir to control where RealityScanInterface creates its temp folder
        self.patcher = patch('tempfile.gettempdir', return_value=str(self.test_dir))
        self.mock_gettempdir = self.patcher.start()

        # Instantiate the class under test
        self.rs_interface = RealityScanInterface(self.mock_config)
        # The instance's temp_dir will now be inside our self.test_dir

    def tearDown(self):
        """Clean up the test environment after each test."""
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test that the class initializes correctly."""
        self.assertIsNotNone(self.rs_interface)
        expected_temp_dir = self.test_dir / 'video_3dgs_temp'
        self.assertEqual(self.rs_interface.temp_dir, expected_temp_dir)
        self.assertTrue(expected_temp_dir.exists())

    def test_parse_alignment_result_from_mock_file(self):
        """Test parsing a mock XML result file. This test will drive implementation."""
        # Path to the mock XML file we created
        mock_xml_path = Path(__file__).parent / 'mock_alignment_result.xml'
        self.assertTrue(mock_xml_path.exists(), "Mock XML file should exist")

        # The method under test, _parse_alignment_result, expects to find the XML
        # at a specific path inside its temporary directory.
        expected_xml_location = self.rs_interface.temp_dir / "alignment_result.xml"

        # In a real run, RealityScan would create this. For our test, we copy our mock file there.
        shutil.copy(mock_xml_path, expected_xml_location)

        # The method takes a subprocess.CompletedProcess object, which we can mock
        # as it's not used by the current placeholder implementation.
        mock_process_result = MagicMock(spec=subprocess.CompletedProcess)

        # Call the method to be tested
        # This currently returns a hardcoded empty result, so the asserts below will fail.
        parsed_data = self.rs_interface._parse_alignment_result(mock_process_result)

        # --- Assertions ---
        # These assertions define what we EXPECT the function to do.
        # They will fail until we implement the parsing logic in the next step.

        self.assertIsNotNone(parsed_data, "Parsed data should not be None")
        self.assertEqual(len(parsed_data['components']), 2, "Should parse 2 components")
        self.assertEqual(parsed_data['total_images'], 3, "Should parse total images stat")
        self.assertAlmostEqual(parsed_data['alignment_ratio'], 1.0, "Alignment ratio should be 1.0")
        self.assertAlmostEqual(parsed_data['mean_reprojection_error'], 0.9876, "Should take the first component's reprojection error")
        self.assertIn('image_001.jpg', parsed_data['components'][0]['images'], "Component 0 should contain image_001.jpg")
        self.assertIn('image_003.jpg', parsed_data['components'][0]['images'], "Component 0 should contain image_003.jpg")
        self.assertIn('image_002.jpg', parsed_data['components'][1]['images'], "Component 1 should contain image_002.jpg")

    @patch('core.realityscan_interface.subprocess.Popen')
    def test_run_alignment_integration(self, mock_popen):
        """Test the full run_alignment workflow with mocks."""
        # --- Setup ---
        # 1. Mock the subprocess call to simulate RealityScan running successfully
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('stdout', 'stderr')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # 2. Create dummy source images
        source_image_dir = self.test_dir / "source_images"
        source_image_dir.mkdir()
        image_paths = []
        for i in range(3):
            p = source_image_dir / f"image_{i:03d}.jpg"
            p.touch() # Create empty files
            image_paths.append({'path': str(p)})

        # 3. Place the mock XML result where the application expects to find it
        mock_xml_path = Path(__file__).parent / 'mock_alignment_result.xml'
        expected_xml_location = self.rs_interface.temp_dir / "alignment_result.xml"
        expected_xml_location.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(mock_xml_path, expected_xml_location)

        # --- Execution ---
        # Call the main method
        result_data = self.rs_interface.run_alignment(images=image_paths, quality='high')

        # --- Assertions ---
        # 1. Assert that RealityScan was "called" with the correct command
        mock_popen.assert_called_once()
        args, _ = mock_popen.call_args
        command_list = args[0]
        self.assertIn('-set alignQuality=high', command_list)

        # 2. Assert that the images were copied
        temp_image_dir = self.rs_interface.temp_dir / self.rs_interface.instance_name / 'images'
        self.assertEqual(len(list(temp_image_dir.glob('*.jpg'))), 3)

        # 3. Assert that the final parsed data is correct
        self.assertEqual(len(result_data['components']), 2)
        self.assertEqual(result_data['total_images'], 3)
        self.assertAlmostEqual(result_data['mean_reprojection_error'], 0.9876)


if __name__ == '__main__':
    unittest.main()
