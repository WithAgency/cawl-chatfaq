@widgetconfig
Feature: Widget configuration

    Scenario: Creates a widget and edits its name and domain
        Given I am logged in
        When I am on the widget config page
        Then I should see the text "0 Widget"
        When I choose to add Widget
        And I enter "Support" in name
        And I enter "https://support.example" in domain
        And I choose to save changes
        Then I should see the text "Support"
        When I choose to edit Support
        And I enter "Support renamed" in name
        And I enter "https://renamed.example" in domain
        And I choose to save changes
        Then I should see the text "Support renamed"
        And I should see the text "https://renamed.example"

    Scenario: Creates a theme
        Given I am logged in
        When I am on the widget config page
        And I open the "Theme" tab
        Then I should see the text "0 Theme"
        When I choose to add Theme
        And I enter "Night" in name
        And I choose to save changes
        Then I should see the text "Night"
