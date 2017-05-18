Feature: Markdown functionality in posts
    Implement markdown functionality in my posts that properly
    displays headers/line breaks/etc.

    Scenario: A visitor viewing a posts detail page with markdown
        Given I am at the homepage
        When I select a posts title or body
        Then I see properly formatted/rendered text
