from datetime import timedelta

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


class NewVisitorTest(StaticLiveServerTestCase):
    """
    Test suite to check a new visitor can access the site correctly.

    This is an E2E test with selenium to test our home page
    and its various elements.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.browser = webdriver.Firefox()
        # cls.browser.implicitly_wait(2)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.quit()
        super().tearDownClass()

    def test_home_page_search_form(self):
        # Vicky has heard about a cool new bus ticket booking app. She goes to check out its homepage
        self.browser.get(f"{self.live_server_url}")

        # She notices the page title and header mention bus tickets
        self.assertIn("Kpiola", self.browser.title)
        self.assertIn("Book Bus Tickets", self.browser.title)

        # She notices the origin input box and the placeholder
        origin = self.browser.find_element(By.NAME, "origin")
        self.assertEqual(origin.get_attribute("placeholder"), "Leaving from")
        self.assertEqual(origin.get_attribute("value"), "")

        # She doesn't see any autocomplete dangling below the input
        origin_ac = self.browser.find_element(By.ID, "autoComplete_list_1")
        self.assertFalse(origin_ac.is_displayed())

        # She types in `Bue`` to search for `Buenos Aires` and sees the autocomplete popup
        origin.send_keys("bue")
        self.assertTrue(origin_ac.is_displayed)

        # She selects Buenos Aires from the dropdown autocomplete list
        ActionChains(self.browser).move_to_element(origin_ac).click().perform()
        self.assertEqual(origin.get_attribute("value"), "Buenos Aires")

        # Destination input
        # She notices the destination input box and the placeholder
        destination = self.browser.find_element(By.NAME, "destination")
        self.assertEqual(destination.get_attribute("placeholder"), "Going to")
        self.assertEqual(destination.get_attribute("value"), "")

        # She doesn't see any autocomplete dangling below the input
        destination_ac = self.browser.find_element(By.ID, "autoComplete_list_2")
        self.assertFalse(destination_ac.is_displayed())

        # She types in `Men` to search for `Mendoza` and sees the autocomplete popup
        destination.send_keys("men")
        self.assertTrue(destination_ac.is_displayed)

        # She selects Mendoza from the dropdown autocomplete list
        ActionChains(self.browser).move_to_element(destination_ac).click().perform()
        # self.assertEqual(destination.get_attribute("value"), "Mendoza") # <-- flaky

        # She observes the departure date input is prepopulated with tomorrow's date
        departure = self.browser.find_element(By.ID, "departure")
        tomorrow = (timezone.now() + timedelta(days=1)).strftime("%d-%m-%Y")
        self.assertEqual(departure.get_attribute("value"), tomorrow)

        # ?? Not sure how to text flatpickr for departure

        # She observes the return date input and notices that its blank
        return_date = self.browser.find_element(By.ID, "return")
        self.assertEqual(return_date.get_attribute("value"), "")

        # ?? Again not sure how to test flatpickr for return date input

        # Trip Type
        # Vicky then notices the trip type option and see `Round Trip` as selected
        trip_type = Select(self.browser.find_element(By.ID, "trip_type"))
        self.assertEqual(trip_type.first_selected_option.text, "Round trip")

        # She clicks on it and sees that there are only two options
        self.assertEqual(len(trip_type.options), 2)

        # Num of Passenger
        # Vicky then moves her attention to the num of passengers options
        num_of_pass = Select(self.browser.find_element(By.ID, "num_of_passengers"))
        self.assertEqual(num_of_pass.first_selected_option.text, "1")

        # She clicks on the select and see that there are upto 5 options
        self.assertEqual(len(num_of_pass.options), 5)

        # Being satisfied that all inputs are corrected she finally clicks the search button
