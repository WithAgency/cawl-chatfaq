@widget
Feature: Chat widget

    Scenario: Opens the shell, the menu and a user message
        Given a demo widget named "Support" exists
        When I open the widget demo
        And I choose to open widget
        Then I should see the text "Hello there"
        And I should see the text "New conversation"
        And I should see the text "Show dark mode"
        When I choose to color theme
        Then I should see the text "Show light mode"
        When I enter "Where is the handbook?" in chat prompt
        And I choose to send message
        Then I should see the text "Where is the handbook?"
