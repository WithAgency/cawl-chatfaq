@dashboard
Feature: Admin dashboard

    Scenario: Shows empty sections
        Given I am logged in
        Then I should see the text "Welcome, Ada"
        And I should see "no sdks"
        And I should see "no llms"
        And I should see "no widgets"

    Scenario: Shows seeded cards and opens their editor
        Given I am logged in
        And an LLM named "Answerer" exists
        And a widget named "Support" exists
        When I am on the dashboard page
        Then I should see the text "Answerer"
        And I should see the text "Support"
        When I choose to Answerer card
        Then I should see the text "AI Configuration"
        And I should be at a URL with "ai_config"

    Scenario: Opens the widget editor from its card
        Given I am logged in
        And a widget named "Support" exists
        When I am on the dashboard page
        And I choose to Support card
        Then I should see the text "Widget Config"
        And I should be at a URL with "widget_config"

    Scenario: Turns an LLM off
        Given I am logged in
        And an LLM named "Answerer" exists
        When I am on the dashboard page
        And I toggle "enable Answerer"
        And I am on the dashboard page
        Then "enable Answerer" should be off
