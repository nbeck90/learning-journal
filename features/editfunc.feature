Feature: Post Editing
    Implement an edit functionality in our website that allows
    for changing the text/itle of a post while retaining the id.

    Scenario: Edit a post
        Given a post that I have edited
        When I click the share button
        Then I move to that posts detail page
