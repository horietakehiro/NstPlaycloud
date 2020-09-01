from ..common.base import BaseTestCase

class LoginTestCase(BaseTestCase):

    def test_login_1(self):
        """
        test_login_1 : log out from image_list page.
        once logged out, redirect to login home
        """
        self.setUp_driver()

        self.driver.get(self.live_server_url)

        logout = self.get_element("link_text", "Log out")
        logout.click()

        self.assertEqual(
            self.driver.current_url, 
            self.live_server_url + "/admin/login/?next=/image_list/",
        )

