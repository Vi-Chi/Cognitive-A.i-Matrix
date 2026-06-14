import unittest

from ai_chi.orbi.safe_shell import SafeShellValidator

class TestSafeShellValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = SafeShellValidator()

    def test_blocks_shell_metacharacters(self):
        result = self.validator.validate("df -h && rm -rf /")
        self.assertFalse(result.allowed)
        self.assertIn("blocked shell token", result.reason)

    def test_blocks_sudo(self):
        result = self.validator.validate("sudo systemctl restart nginx")
        self.assertFalse(result.allowed)
        self.assertIn("blocked command", result.reason)

    def test_blocks_docker_mutation_by_default(self):
        result = self.validator.validate("docker stop anythingllm")
        self.assertFalse(result.allowed)
        self.assertIn("docker mutation", result.reason)

    def test_allows_readonly_command(self):
        result = self.validator.validate("df -h")
        self.assertTrue(result.allowed)
        self.assertIn("allowed read-only", result.reason)

    def test_blocks_apt_install(self):
        result = self.validator.validate("apt install nginx")
        self.assertFalse(result.allowed)
        self.assertIn("apt mutation", result.reason)
