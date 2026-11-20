@users
Feature: User management

    Scenario: Lists the signed-in user and creates another
        Given I am logged in
        When I am on the user management page
        Then I should see the text "ada@chatfaq.test"
        When I choose to add User
        Then I should see the text "User information"
        And I should see the text "User permissions"
        When I enter "Sam" in first_name
        And I enter "Reviewer" in last_name
        And I enter "sam@chatfaq.test" in email
        And I enter "correct" in password
        And I choose to save changes
        Then I should see the text "sam@chatfaq.test"

    Scenario: Creates a group
        Given I am logged in
        When I am on the user management page
        And I open the "Group Permissions" tab
        And I choose to add Group
        And I enter "Editors" in name
        And I choose to save changes
        Then I should see the text "Editors"
