"""
Selenium UI Test Suite - DevForge Frontend
Tests button interactions, form inputs, and component rendering
"""

import pytest
try:
    import allure
except ImportError:
    allure = None
from selenium.webdriver.common.by import By
from contextlib import contextmanager

@contextmanager
def allure_step(description):
    """Context manager for allure steps that works with or without allure"""
    if allure:
        with allure_step(description):
            yield
    else:
        yield

def allure_feature(name):
    """Decorator for allure feature that works with or without allure"""
    def decorator(cls):
        if allure:
            return allure.feature(name)(cls)
        return cls
    return decorator

def allure_story(name):
    """Decorator for allure story that works with or without allure"""
    def decorator(cls):
        if allure:
            return allure.story(name)(cls)
        return cls
    return decorator


@allure_feature("UI Components")
@allure_story("Button Component")
class TestButtonComponent:
    """Button component tests using Selenium"""

    @pytest.mark.selenium
    @pytest.mark.smoke
    def test_button_renders(self, selenium_driver, base_url):
        """Verify button component renders on page"""
        with allure_step("Navigate to app"):
            selenium_driver.get(base_url)

        with allure_step("Verify button exists"):
            button = selenium_driver.find_element(By.ID, "btn-primary")
            assert button.is_displayed(), "Primary button should be visible"

    @pytest.mark.selenium
    @pytest.mark.smoke
    def test_button_click_handler(self, selenium_driver, base_url):
        """Verify button click handler works"""
        with allure_step("Navigate to app"):
            selenium_driver.get(base_url)

        with allure_step("Click primary button"):
            button = selenium_driver.find_element(By.ID, "btn-primary")
            button.click()

        with allure_step("Verify click was registered"):
            clicked = selenium_driver.execute_script(
                "return window.lastClickedButton;"
            )
            assert clicked == "Click me", f"Expected 'Click me', got {clicked}"

    @pytest.mark.selenium
    def test_button_styles(self, selenium_driver, base_url):
        """Verify button styling"""
        with allure_step("Navigate to app"):
            selenium_driver.get(base_url)

        with allure_step("Check primary button background color"):
            button = selenium_driver.find_element(By.ID, "btn-primary")
            bg_color = button.value_of_css_property("background-color")
            assert bg_color, "Button should have background color"

    @pytest.mark.selenium
    @pytest.mark.regression
    def test_button_hover_effect(self, selenium_driver, base_url):
        """Verify button hover effect"""
        with allure_step("Navigate to app"):
            selenium_driver.get(base_url)

        with allure_step("Get button and hover"):
            button = selenium_driver.find_element(By.ID, "btn-primary")
            selenium_driver.execute_script(
                "arguments[0].dispatchEvent(new MouseEvent('mouseenter'));",
                button,
            )

        with allure_step("Verify hover opacity"):
            opacity = button.value_of_css_property("opacity")
            assert opacity == "0.8", f"Hover opacity should be 0.8, got {opacity}"


@allure.feature("UI Components")
@allure.story("Input Component")
class TestInputComponent:
    """Input component tests"""

    @pytest.mark.selenium
    @pytest.mark.smoke
    def test_input_renders(self, selenium_driver, base_url):
        """Verify input component renders"""
        with allure_step("Navigate to app"):
            selenium_driver.get(base_url)

        with allure_step("Find input field"):
            input_field = selenium_driver.find_element(By.ID, "input-text")
            assert input_field.is_displayed(), "Input field should be visible"

    @pytest.mark.selenium
    def test_input_accepts_text(self, selenium_driver, base_url):
        """Verify input accepts text"""
        with allure_step("Navigate to app"):
            selenium_driver.get(base_url)

        with allure_step("Type into input"):
            input_field = selenium_driver.find_element(By.ID, "input-text")
            test_text = "Hello DevForge"
            input_field.send_keys(test_text)

        with allure_step("Verify text was entered"):
            value = input_field.get_attribute("value")
            assert value == test_text, f"Expected '{test_text}', got '{value}'"

    @pytest.mark.selenium
    @pytest.mark.regression
    def test_input_password_type(self, selenium_driver, base_url):
        """Verify password input type"""
        with allure_step("Navigate to app"):
            selenium_driver.get(base_url)

        with allure_step("Check password input type"):
            password_input = selenium_driver.find_element(By.ID, "input-password")
            input_type = password_input.get_attribute("type")
            assert input_type == "password", f"Expected type 'password', got '{input_type}'"


@allure.feature("UI Interactions")
class TestFormInteractions:
    """Form and input interaction tests"""

    @pytest.mark.selenium
    def test_multiple_inputs_interaction(self, selenium_driver, base_url):
        """Test interaction with multiple inputs"""
        with allure_step("Navigate to app"):
            selenium_driver.get(base_url)

        with allure_step("Fill text input"):
            text_input = selenium_driver.find_element(By.ID, "input-text")
            text_input.send_keys("Test User")

        with allure_step("Fill password input"):
            password_input = selenium_driver.find_element(By.ID, "input-password")
            password_input.send_keys("SecurePass123")

        with allure_step("Verify both inputs"):
            text_value = text_input.get_attribute("value")
            password_value = password_input.get_attribute("value")
            assert text_value == "Test User"
            assert password_value == "SecurePass123"

    @pytest.mark.selenium
    @pytest.mark.smoke
    def test_disabled_input(self, selenium_driver, base_url):
        """Test disabled input field"""
        with allure_step("Navigate to app"):
            selenium_driver.get(base_url)

        with allure_step("Check disabled input"):
            disabled_input = selenium_driver.find_element(By.ID, "input-disabled")
            is_disabled = disabled_input.get_attribute("disabled")
            assert is_disabled is not None, "Input should be disabled"
