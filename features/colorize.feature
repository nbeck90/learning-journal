Feature: Colorize functionality in posts
    Implement code hilighting functionality that allows for code
    to be colorized and formatted properly.

    Scenario: A visitor viewing a posts detail page
        Given a posts detail page
        When I am viewing a post with code in it
        Then I see properly formatted/colored text
