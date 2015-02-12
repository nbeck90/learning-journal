Feature: Colorize functionality in posts
    Implement markdown functionality in my posts that properly
    displays headers/line breaks/etc.

    Scenario: A visitor viewing a posts detail page
        Given a posts detail page
        When I am viewing a post with markdown written in it
        Then I see properly formatted/rendered text
