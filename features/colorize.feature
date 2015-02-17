Feature: Colorize functionality in posts
    Implement code hilighting functionality that allows for code
    to be colorized and formatted properly.

    Scenario: A visitor viewing a posts detail page with color
        Given I am at the homepage
        When I select a posts title or body
        Then I see properly formatted/colored text
