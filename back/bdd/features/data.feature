@data
Feature: Knowledge data

    Scenario: Shows an empty knowledge base list
        Given I am logged in
        When I am on the data page
        Then I should see the text "0 Knowledge Base"

    Scenario: Creates a knowledge base
        Given I am logged in
        When I am on the data page
        And I choose to add Knowledge Base
        And I enter "Policies" in name
        And I choose to save changes
        Then I should see the text "Policies"

    Scenario: Renames a knowledge base
        Given I am logged in
        And a knowledge base named "Handbook" exists
        When I am on the data page
        And I choose to edit Handbook
        And I enter "Handbook revised" in name
        And I choose to save changes
        Then I should see the text "Handbook revised"

    Scenario: Searches knowledge bases and opens their items
        Given I am logged in
        And a knowledge base named "Handbook" exists
        And that knowledge base has an item titled "Opening hours"
        When I am on the data page
        And I search for "Handbook"
        Then I should see the text "Handbook"
        When I search for "missing"
        Then I should not see the text "Handbook"
        When I search for "Handbook"
        And I choose to view knowledge items Handbook
        Then I should see the text "Opening hours"
