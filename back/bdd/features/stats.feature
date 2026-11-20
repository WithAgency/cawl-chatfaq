@stats
Feature: Statistics

    Scenario: Shows zero conversations
        Given I am logged in
        When I am on the stats page
        Then the stat "Total Conversations" should show "0"

    Scenario: Counts a seeded conversation
        Given I am logged in
        And a conversation named "Billing question" from "visitor-42" exists
        When I am on the stats page
        Then the stat "Total Conversations" should show "1"
