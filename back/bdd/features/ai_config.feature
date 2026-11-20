@ai
Feature: AI configuration

    Scenario: Manages an LLM
        Given I am logged in
        When I am on the AI config page
        Then I should see the text "0 LLM"
        And I should not see the "Retriever" tab
        When I choose to add LLM
        And I enter "Draft model" in name
        And I choose to save changes
        Then I should see the text "Draft model"

    Scenario: Keeps the API key masked
        Given I am logged in
        And an LLM named "Answerer" exists
        When I am on the AI config page
        And I choose to edit Answerer
        Then the "api_key" field should be masked

    Scenario: Manages a prompt
        Given I am logged in
        When I am on the AI config page
        And I open the "Prompt" tab
        Then I should see the text "0 Prompt"
        When I choose to add Prompt
        And I enter "Short answers" in name
        And I enter "Answer briefly." in prompt
        And I choose to save changes
        Then I should see the text "Short answers"

    Scenario: Manages a generation config
        Given I am logged in
        When I am on the AI config page
        And I open the "Generation" tab
        Then I should see the text "0 Generation"
        When I choose to add Generation
        And I enter "Precise" in name
        And I choose to save changes
        Then I should see the text "Precise"

    @ray
    Scenario: Shows a retriever when Ray is available
        Given Ray is available
        And a retriever named "Finder" exists
        And I am logged in
        When I am on the AI config page
        And I open the "Retriever" tab
        Then I should see the text "Finder"
        And I should see the text "Reindex"
