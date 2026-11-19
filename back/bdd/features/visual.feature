@visual
Feature: Visual baselines

    Scenario: Login page
        When I am on the login page
        Then I should see the text "Welcome to ChatFAQ!"
        And the page should match the "login" snapshot

    Scenario: Empty dashboard
        Given I am logged in
        Then I should see "no sdks"
        And the page should match the "dashboard" snapshot

    Scenario: Knowledge base list
        Given I am logged in
        And a knowledge base named "Handbook" exists
        When I am on the data page
        Then I should see the text "Handbook"
        And the page should match the "data" snapshot
