@labeling
Feature: Conversation labeling

    Scenario: Filters the list and opens a conversation
        Given I am logged in
        And a conversation named "Billing question" from "visitor-42" exists
        When I am on the labeling page
        Then I should see the text "visitor-42"
        And I should see "filter Reviewed"
        And I should see the text "With User Feedback"
        When I search for "Billing question"
        Then I should see the text "visitor-42"
        When I search for "nobody"
        Then I should not see the text "visitor-42"
        When I search for "Billing"
        And I choose to view Billing question
        Then I should see the text "Billing question"
        When I choose to back
        Then I should see the text "visitor-42"
