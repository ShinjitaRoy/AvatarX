import unittest
from src.avatar.avatar_controller import AvatarController
from src.avatar.animation_handler import AnimationHandler

class TestAvatarController(unittest.TestCase):

    def setUp(self):
        self.avatar_controller = AvatarController()
        self.animation_handler = AnimationHandler()

    def test_join_meeting(self):
        result = self.avatar_controller.join_meeting("test_meeting_id")
        self.assertTrue(result)

    def test_exit_meeting(self):
        self.avatar_controller.join_meeting("test_meeting_id")
        result = self.avatar_controller.exit_meeting()
        self.assertTrue(result)

    def test_animation_start(self):
        result = self.animation_handler.start_animation("wave")
        self.assertTrue(result)

    def test_animation_stop(self):
        self.animation_handler.start_animation("wave")
        result = self.animation_handler.stop_animation()
        self.assertTrue(result)

    def test_activate_deactivate(self):
        a = AvatarController()
        a.activate()
        self.assertTrue(a.active)
        a.deactivate()
        self.assertFalse(a.active)

if __name__ == '__main__':
    unittest.main()