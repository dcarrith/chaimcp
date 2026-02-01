import unittest
import subprocess
import os
import sys

class TestNpxLaunch(unittest.TestCase):
    def setUp(self):
        # Locate the bin/server.js script relative to this test file
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.bin_script = os.path.join(self.project_root, "bin", "server.js")

    def test_npx_launch_help(self):
        """Test that the Node.js wrapper launches successfully with --help."""
        
        # Ensure we use the current python environment for the subprocess if possible, 
        # or rely on the wrapper's default behavior.
        # The wrapper spawns 'python3', so we need to make sure 'python3' is available 
        # and has dependencies. Since we are running tests, we assume dependencies are there.
        
        # We also need 'node' available.
        
        try:
            # Activate the virtual environment if we are in one so the wrapper finds deps
            env = os.environ.copy()
            
            # Ensure the python executable used by node matches ours by prepending its dir to PATH
            python_dir = os.path.dirname(sys.executable)
            env["PATH"] = python_dir + os.pathsep + env.get("PATH", "")
            
            # Propagate current sys.path to PYTHONPATH to ensure all libs are found
            # Filter out empty strings which might be current dir
            valid_paths = [p for p in sys.path if p and os.path.isdir(p)]
            env["PYTHONPATH"] = os.pathsep.join(valid_paths) + os.pathsep + env.get("PYTHONPATH", "")

            # Run: node bin/server.js --help
            result = subprocess.run(
                ["node", self.bin_script, "--help"],
                capture_output=True,
                text=True,
                env=env,
                check=False # Check manually
            )
            
            # Check exit code
            self.assertEqual(result.returncode, 0, f"Script failed with stderr: {result.stderr}")
            
            # Check for expected output identifying it's our server
            # The FastMCP server usually prints usage info or "options" on --help
            self.assertIn("usage", result.stdout.lower())
            self.assertIn("chaimcp", result.stdout.lower() + result.stderr.lower()) # check both just in case

        except FileNotFoundError:
            self.skipTest("node executable not found")

if __name__ == "__main__":
    unittest.main()
