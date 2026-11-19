@smoke
Feature: Admin login

    Scenario: Signs in with valid credentials
        Given the admin user exists
        When I am on the login page
        And I enter "ada@chatfaq.test" in email
        And I enter "correct" in password
        And I choose to login
        Then I should see the text "Welcome, Ada"
        And I should not be at a URL with "login"
        And there should be no console errors

    Scenario: Rejects a wrong password
        Given the admin user exists
        When I am on the login page
        And I enter "ada@chatfaq.test" in email
        And I enter "wrong-password" in password
        And I choose to login
        Then I should see the text "Invalid email or password"
        And I should be at a URL with "login"

    Scenario: Sends anonymous visitors to the login page
        When I am on the dashboard page
        Then I should see the text "Welcome to ChatFAQ!"
        And I should be at a URL with "login"
