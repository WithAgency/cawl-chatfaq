@menu
Feature: Admin menu and session

    Scenario: Opens each section from the menu
        Given I am logged in
        When I choose to labeling
        Then I should see the text "Labeling"
        And I should be at a URL with "labeling"
        When I choose to data
        Then I should see the text "Data"
        And I should be at a URL with "data"
        When I choose to AI config
        Then I should see the text "AI Configuration"
        And I should be at a URL with "ai_config"
        When I choose to widget config
        Then I should see the text "Widget Config"
        And I should be at a URL with "widget_config"
        When I choose to stats
        Then I should see the text "Stats"
        And I should be at a URL with "stats"
        When I choose to user management
        Then I should see the text "User Management"
        And I should be at a URL with "user_management"
        And I should not see the text "Task History"

    Scenario: Switches the interface language
        Given I am logged in
        When I choose the language "fr"
        Then I should see the text "Tableau de bord"
        When I choose the language "en"
        Then I should see the text "Dashboard"

    Scenario: Logs out
        Given I am logged in
        When I choose to log out
        Then I should see the text "Welcome to ChatFAQ!"
        And I should be at a URL with "login"

    @ray
    Scenario: Shows task history when Ray is available
        Given Ray is available
        And I am logged in
        Then I should see "task history"
