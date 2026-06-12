"""
Comprehensive QA Suite - Shared Fixtures & Configuration
Integrates Selenium, Pytest, and Allure for unified testing
"""

import pytest
import allure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from datetime import datetime


@pytest.fixture(scope="session")
def allure_report_config():
    """Configure Allure reporting"""
    allure.environment(
        python_version=os.popen("python --version").read().strip(),
        os=os.name,
        timestamp=datetime.now().isoformat(),
    )
    return {
        "results_dir": "allure-results",
        "report_dir": "allure-report",
    }


@pytest.fixture(scope="session")
def chrome_options():
    """Configure Chrome browser options for Selenium"""
    options = Options()

    # Headless mode for CI/CD
    if os.getenv("CI") or os.getenv("HEADLESS"):
        options.add_argument("--headless=new")

    # Standard options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    return options


@pytest.fixture
def selenium_driver(chrome_options):
    """Selenium WebDriver instance with Chrome"""
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)

    yield driver

    # Cleanup
    driver.quit()


@pytest.fixture
def wait(selenium_driver):
    """WebDriverWait helper for explicit waits"""
    return WebDriverWait(selenium_driver, 10)


@pytest.fixture
def base_url():
    """Base URL for application under test"""
    return os.getenv("BASE_URL", "http://localhost:5173")


@pytest.fixture(autouse=True)
def track_test_execution(request, allure_report_config):
    """
    Automatically track test execution in Allure
    Adds test metadata and captures results
    """
    test_name = request.node.name

    # Add test markers as Allure labels
    if request.node.get_closest_marker("e2e"):
        allure.label("type", "e2e")
    elif request.node.get_closest_marker("selenium"):
        allure.label("type", "selenium")
    elif request.node.get_closest_marker("unit"):
        allure.label("type", "unit")

    if request.node.get_closest_marker("smoke"):
        allure.label("severity", "blocker")
    elif request.node.get_closest_marker("regression"):
        allure.label("severity", "critical")

    allure.title(test_name)

    yield

    # Record test result
    if request.node.rep_call.failed:
        allure.attach(
            f"Test failed: {request.node.rep_call.longrepr}",
            name="failure_details",
            attachment_type=allure.attachment_type.TEXT,
        )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test outcomes for Allure"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


class PageObject:
    """Base Page Object Model for UI testing"""

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def navigate(self, path=""):
        """Navigate to page"""
        url = f"{self.base_url}{path}"
        self.driver.get(url)
        allure.step(f"Navigated to {url}")

    def find(self, by, value):
        """Find element with explicit wait"""
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def click(self, by, value):
        """Click element"""
        element = self.wait.until(EC.element_to_be_clickable((by, value)))
        element.click()
        allure.step(f"Clicked element: {by}={value}")

    def type_text(self, by, value, text):
        """Type text into element"""
        element = self.find(by, value)
        element.clear()
        element.send_keys(text)
        allure.step(f"Typed '{text}' into {by}={value}")

    def get_text(self, by, value):
        """Get element text"""
        return self.find(by, value).text

    def wait_for_text(self, by, value, text, timeout=10):
        """Wait for element to contain text"""
        self.wait = WebDriverWait(self.driver, timeout)
        self.wait.until(
            EC.text_to_be_present_in_element((by, value), text)
        )
        allure.step(f"Waited for text '{text}' in {by}={value}")


@pytest.fixture
def page_object(selenium_driver, base_url):
    """Page Object Model base fixture"""
    return PageObject(selenium_driver, base_url)
